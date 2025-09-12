import aiohttp
import asyncio
from urllib.parse import urlparse, parse_qs, unquote
from selectolax.parser import HTMLParser
from config_v2 import get_settings

# Obtener configuración
settings = get_settings()

import aiohttp
import asyncio
from urllib.parse import urlparse, parse_qs, unquote
from selectolax.parser import HTMLParser
from config_v2 import get_settings
import json

# Obtener configuración
settings = get_settings()

async def search_urls_for(keyword: str, max_results: int = 10) -> list[str]:
    """
    Buscar URLs relevantes para una keyword usando el motor de búsqueda configurado
    """
    search_engine = settings.scraping.search_engine

    if search_engine == "google":
        return await search_google(keyword, max_results)
    elif search_engine == "duckduckgo":
        return await search_duckduckgo(keyword, max_results)
    else:
        # Fallback a mock URLs
        return get_mock_urls(keyword, max_results)

async def search_google(keyword: str, max_results: int = 10) -> list[str]:
    """
    Buscar usando Google Custom Search Engine
    """
    api_key = settings.scraping.google_api_key
    cse_id = settings.scraping.google_cse_id

    if not api_key or not cse_id:
        print("⚠️ Google API key or CSE ID not configured, using mock URLs")
        return get_mock_urls(keyword, max_results)

    try:
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': keyword,
            'num': min(max_results, 10),  # Google limita a 10 resultados por request
            'start': 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    urls = []

                    for item in data.get('items', []):
                        url = item.get('link', '')
                        if url and is_valid_result_url(url):
                            urls.append(url)

                    print(f"🔍 Google search for '{keyword}': found {len(urls)} URLs")
                    return urls[:max_results]
                else:
                    error_text = await response.text()
                    print(f"❌ Google search error: {response.status} - {error_text}")
                    return get_mock_urls(keyword, max_results)

    except Exception as e:
        print(f"❌ Error searching Google: {e}")
        return get_mock_urls(keyword, max_results)

async def search_duckduckgo(keyword: str, max_results: int = 10) -> list[str]:
    """
    Buscar usando DuckDuckGo con Scrapling para mejor parsing
    """
    try:
        from scrapling_simple import enhanced_scrape_url

        # URL de búsqueda de DuckDuckGo
        search_url = f"https://duckduckgo.com/html/?q={keyword}"

        # Usar Scrapling para obtener el HTML
        result = await asyncio.get_event_loop().run_in_executor(
            None, enhanced_scrape_url, search_url
        )

        if result['status'] != 'success':
            print(f"❌ DuckDuckGo search failed: {result.get('error', 'Unknown error')}")
            return get_mock_urls(keyword, max_results)

        html_content = result.get('full_html', '')
        if not html_content:
            # Intentar fallback con requests directo
            return await search_duckduckgo_fallback(keyword, max_results)

        urls = []

        # Parsear resultados usando selectolax
        parser = HTMLParser(html_content)

        # DuckDuckGo usa diferentes clases para resultados
        result_selectors = [
            '.result__url',
            '.result__title',
            'a.result__url',
            'a.result__title',
            '.links_main a'
        ]

        for selector in result_selectors:
            links = parser.css(selector)
            for link in links[:max_results]:
                href = link.attributes.get('href', '')

                if href and href.startswith('/l/?uddg='):
                    # Es un enlace de redirección de DuckDuckGo
                    try:
                        from urllib.parse import parse_qs, unquote
                        parsed = urlparse(href)
                        query_params = parse_qs(parsed.query)
                        real_url = query_params.get('uddg', [''])[0]

                        if real_url:
                            real_url = unquote(real_url)
                            if is_valid_result_url(real_url):
                                urls.append(real_url)
                    except Exception as e:
                        print(f"Error procesando URL: {href} - {e}")
                        continue
                elif href and href.startswith('http'):
                    # URL directa
                    if is_valid_result_url(href):
                        urls.append(href)

        # Remover duplicados
        urls = list(dict.fromkeys(urls))

        print(f"🔍 DuckDuckGo search with Scrapling for '{keyword}': found {len(urls)} URLs")
        return urls[:max_results] if urls else get_mock_urls(keyword, max_results)

    except Exception as e:
        print(f"❌ Error searching DuckDuckGo with Scrapling: {e}")
        return await search_duckduckgo_fallback(keyword, max_results)

async def search_duckduckgo_fallback(keyword: str, max_results: int = 10) -> list[str]:
    """
    Fallback usando requests directo para DuckDuckGo
    """
    try:
        # Usar la API de DuckDuckGo instant answers
        url = f"https://api.duckduckgo.com/"
        params = {
            'q': keyword,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    urls = []

                    # Extraer URLs de resultados
                    if 'Results' in data:
                        for result in data['Results'][:max_results]:
                            result_url = result.get('FirstURL', '')
                            if result_url and is_valid_result_url(result_url):
                                urls.append(result_url)

                    print(f"🔍 DuckDuckGo fallback search for '{keyword}': found {len(urls)} URLs")
                    return urls if urls else get_mock_urls(keyword, max_results)
                else:
                    print(f"❌ DuckDuckGo fallback search error: {response.status}")
                    return get_mock_urls(keyword, max_results)

    except Exception as e:
        print(f"❌ Error in DuckDuckGo fallback: {e}")
        return get_mock_urls(keyword, max_results)

def get_mock_urls(keyword: str, max_results: int = 10) -> list[str]:
    """
    URLs de ejemplo para testing - sitios con contenido conversacional
    """
    mock_urls = [
        "https://www.reddit.com/r/marketing/",
        "https://www.quora.com/topic/Digital-Marketing",
        "https://forum.wordreference.com/threads/marketing.123456/",
        "https://www.blackhatworld.com/forums/digital-marketing.63/",
        "https://www.warriorforum.com/marketing/",
        "https://www.digitalmarketingforums.com/",
        "https://www.marketingprofs.com/answer-exchange/",
        "https://community.hubspot.com/",
        "https://www.growthhackers.com/",
        "https://www.marketingexperiments.com/"
    ]

    # Filtrar por keyword básica
    if any(term in keyword.lower() for term in ["marketing", "digital", "agencia", "empresa", "servicios"]):
        return mock_urls[:max_results]

    return mock_urls[:max_results]

def extract_real_urls_from_duckduckgo(html_content: str, max_results: int = 10) -> list[str]:
    """
    Extrae las URLs reales de los resultados HTML de DuckDuckGo
    """
    try:
        parser = HTMLParser(html_content)
        urls = []

        # DuckDuckGo usa enlaces con class "result__url" o similares
        result_links = parser.css("a.result__url, a.result__title")

        for link in result_links[:max_results]:
            href = link.attributes.get("href", "")

            if href and href.startswith("/l/?uddg="):
                # Es un enlace de redirección de DuckDuckGo
                # Extraer la URL real del parámetro uddg
                try:
                    parsed = urlparse(href)
                    query_params = parse_qs(parsed.query)
                    real_url = query_params.get("uddg", [""])[0]

                    if real_url:
                        real_url = unquote(real_url)  # Decodificar URL
                        # Filtrar URLs válidas (no anuncios, etc.)
                        if is_valid_result_url(real_url):
                            urls.append(real_url)
                except Exception as e:
                    print(f"Error procesando URL: {href} - {e}")
                    continue
            elif href and href.startswith("http"):
                # URL directa
                if is_valid_result_url(href):
                    urls.append(href)

        return urls[:max_results]

    except Exception as e:
        print(f"Error parseando HTML de DuckDuckGo: {e}")
        return []

def is_valid_result_url(url: str) -> bool:
    """
    Filtra URLs válidas para scraping (excluye anuncios, etc.)
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Excluir dominios no deseados
        excluded_domains = [
            'duckduckgo.com',
            'google.com',
            'bing.com',
            'yahoo.com',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'youtube.com',
            'amazon.com',
            'wikipedia.org'
        ]

        if any(excluded in domain for excluded in excluded_domains):
            return False

        # Solo URLs HTTP/HTTPS válidas
        return parsed.scheme in ['http', 'https'] and len(parsed.netloc) > 0

    except:
        return False

# Mantener compatibilidad con código síncrono existente
def search_urls_for_sync(keyword: str) -> list[str]:
    """
    Versión síncrona para compatibilidad
    """
    try:
        # Ejecutar la versión async en un loop de eventos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(search_urls_for(keyword))
        loop.close()
        return result
    except Exception as e:
        print(f"Error en búsqueda síncrona: {e}")
        return []
