import re

# Expresiones regulares mejoradas con variantes coloquiales peruanas
DOLOR = re.compile(r"""
    # Problemas y errores
    (problema|error|no\s+funciona|demora|caro|mal[o|a]|queja|
     # Variantes coloquiales
     chamba|urgente|al\s+toque|necesito\s+urgente|no\s+anda|
     mantenimiento\s+inmediato|limpieza\s+inmediata|reparacion\s+urgente|
     falla|defecto|rota|estropeado|dañado|no\s+sirve|
     # Expresiones de frustración
     estoy\s+harto|ya\s+no\s+aguanto|terrible|horrible|desastre|
     # Términos técnicos comunes
     no\s+carga|se\s+congela|se\s+traba|lento|crash|cuelga)
""", re.I | re.VERBOSE)

BUSQUEDA = re.compile(r"""
    # Búsquedas de proveedores
    (recomiendan|proveedor|cotización|presupuesto|alguien\s+que|
     # Variantes coloquiales
     coticen|proforma|donde\s+encuentro|quien\s+tiene|busco\s+a\s+alguien|
     necesito\s+proveedor|proveedor\s+de\s+confianza|empresa\s+seria|
     # Términos de búsqueda
     donde\s+comprar|donde\s+adquirir|me\s+pueden\s+cotizar|
     presupuesto\s+para|precio\s+de|cuanto\s+cuesta|
     # Expresiones de búsqueda
     alguien\s+sabe|conocen\s+alguien|hay\s+alguien\s+que)
""", re.I | re.VERBOSE)

OBJECION = re.compile(r"""
    # Objeciones y quejas
    (muy\s+caro|no\s+responde|mala\s+atención|no\s+confío|no\s+cumplen|
     # Variantes coloquiales
     carísimo|precio\s+exagerado|atención\s+pésima|servicio\s+malo|
     no\s+son\s+de\s+confianza|malo\s+servicio|atención\s+deficiente|
     # Quejas específicas
     cobran\s+mucho|precios\s+altos|caro\s+el\s+servicio|
     no\s+contestan|no\s+llaman\s+de\s+vuelta|ignoran|
     # Expresiones de desconfianza
     no\s+me\s+inspiran\s+confianza|tengo\s+dudas|no\s+estoy\s+seguro|
     me\s+parece\s+sospechoso|no\s+me\s+convence)
""", re.I | re.VERBOSE)

def tag_item(text: str) -> str:
    t = text.lower()
    if BUSQUEDA.search(t): return "busqueda"
    if OBJECION.search(t): return "objecion"
    if DOLOR.search(t): return "dolor"
    return "ruido"
