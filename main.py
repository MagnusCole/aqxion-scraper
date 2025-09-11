import hashlib, datetime as dt, re, logging, os
from urllib.parse import urljoin
from scrapling.fetchers import Fetcher
from selectolax.parser import HTMLParser
from slugify import slugify

from db import init_db, upsert_post
from sources import search_urls_for
from rules import tag_item
from config import KEYWORDS, MAX_PER_KW, LOG_LEVEL

# Logging setup
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("aqxion")

def make_id(url: str, title: str, body: str) -> str:
    base = f"{url}|{slugify(title or '')}|{(body or '')[:120]}".encode()
    return hashlib.sha256(base).hexdigest()[:16]

def scrape_url(url: str, keyword: str):
    now = dt.datetime.utcnow().isoformat()
    try:
        page = Fetcher.get(url)
        html = HTMLParser(page.html_content)
        count = 0
        for a in html.css("a"):
            if count >= MAX_PER_KW:
                break
            href = a.attributes.get("href", "")
            title = (a.text() or "").strip()
            if (not href or
                href.startswith("#") or
                any(x in href.lower() for x in ["javascript:", "mailto:", "tel:"]) or
                len(title) < 25):
                continue

            full_url = page.urljoin(href)
            if not full_url.startswith("http"):
                continue

            # Extraer body y fecha siguiendo el link
            body = None
            published_at = None
            try:
                detail_page = Fetcher.get(full_url)
                detail_html = HTMLParser(detail_page.html_content)
                # Heurísticas para snippet
                body = " ".join(t.strip() for t in detail_html.text().split())[:600]
                # Fecha si existe
                time_elem = detail_html.css_first("time")
                if time_elem:
                    published_at = time_elem.attributes.get("datetime")

                # Heurística adicional: meta[property="article:published_time"]
                if not published_at:
                    meta_time = detail_html.css_first('meta[property="article:published_time"]')
                    if meta_time:
                        published_at = meta_time.attributes.get("content")
            except Exception as e:
                log.warning(f"Error extrayendo detalle de {full_url}: {e}")

            # Etiquetado de intención
            text_for_tag = f"{title} {body or ''}"
            tag = tag_item(text_for_tag)

            # Normalizar y guardar
            post = {
                "id": make_id(full_url, title, body),
                "source": "MVP",
                "url": full_url,
                "title": title[:300],
                "body": body,
                "lang": "es",
                "created_at": now,
                "keyword": keyword,
                "tag": tag,
                "published_at": published_at,
            }
            upsert_post(post)

            # ⚠️ ALERTA MANUAL: Mostrar posts relevantes en consola
            if tag in ["dolor", "busqueda"]:
                log.warning(f"⚠️ NUEVO {tag.upper()} | {keyword}: {title[:120]} — {full_url}")
                if body:
                    log.warning(f"   Snippet: {body[:100]}{'...' if len(body) > 100 else ''}")
                log.warning("-" * 80)

            count += 1

        log.info(f"Procesados {count} items de {url}")
    except Exception as e:
        log.error(f"Error scraping {url}: {e}")

def run_once():
    init_db()
    keywords_to_use = KEYWORDS
    log.info(f"Iniciando scrape con {len(keywords_to_use)} keywords")
    total_processed = 0

    for kw in keywords_to_use:
        for url in search_urls_for(kw):
            scrape_url(url, kw)
            total_processed += 1

    log.info(f"Scrape completado. Procesadas {len(keywords_to_use)} keywords")

if __name__ == "__main__":
    run_once()
