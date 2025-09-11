import re

DOLOR = re.compile(r"(problema|error|no\s+funciona|demora|caro|mal[o|a]|necesito|ayuda|queja)", re.I)
BUSQUEDA = re.compile(r"(recomiendan|proveedor|cotización|presupuesto|alguien que|busco|donde|quien)", re.I)
OBJECION = re.compile(r"(muy caro|no responde|mala atención|no confío|no cumplen|mal servicio)", re.I)

def tag_item(text: str) -> str:
    t = text.lower()
    if BUSQUEDA.search(t): return "busqueda"
    if OBJECION.search(t): return "objecion"
    if DOLOR.search(t): return "dolor"
    return "ruido"
