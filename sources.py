from config import KEYWORDS

# Para MVP: usaremos búsquedas web públicas simples (ejemplo con duckduckgo html)
# En producción: usa APIs oficiales cuando existan.
def search_urls_for(keyword: str):
    q = keyword.replace(" ", "+")
    # páginas públicas de resultados simples (sólo demo)
    return [f"https://html.duckduckgo.com/html/?q={q}"]
