# Aqxion Scraper MVP

Un scraper web inteligente para extraer y analizar contenido relacionado con negocios en Perú, enfocado en identificar oportunidades de venta y marketing.

## 🚀 Características

### Extracción de Datos
- **Scraping stealth**: Usa Scrapling para evitar detección
- **Múltiples keywords**: Configurable vía variables de entorno
- **Extracción de cuerpo**: Obtiene contenido detallado de las páginas
- **Deduplicación inteligente**: Evita contenido duplicado usando slugs

### Análisis de Intención
- **Clasificación automática**: Identifica dolores, búsquedas y objeciones
- **Patrones regex**: Sistema configurable de reglas de negocio
- **Etiquetas semánticas**: Categoriza el contenido por intención comercial

### Infraestructura
- **Base de datos SQLite**: Almacenamiento eficiente con WAL mode
- **Logging estructurado**: Seguimiento completo de operaciones
- **Configuración externa**: Variables de entorno para fácil deployment
- **Métricas de negocio**: KPIs enfocados en oportunidades de venta

## 📊 KPIs de Negocio

- **Dolores únicos**: Problemas identificados en el mercado
- **Búsquedas proveedor**: Intención de compra activa
- **Objeciones**: Barreras y preocupaciones del mercado
- **Ruido**: Contenido no relevante (filtrado automáticamente)

## 🛠️ Instalación

### Prerrequisitos
- Python 3.11+
- Virtual environment

### Setup
```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install scrapling selectolax python-dotenv slugify

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus keywords y configuración
```

### Configuración (.env)
```env
# Keywords a buscar (separados por pipeline)
KEYWORDS=limpieza de piscina lima|agencia marketing lima|dashboard pymes peru

# Máximo de resultados por keyword
MAX_PER_KW=30

# Nivel de logging
LOG_LEVEL=INFO

# API Key para OpenAI (opcional, para futuras mejoras)
OPENAI_API_KEY=your_key_here
```

## 📁 Estructura del Proyecto

```
aqxion-scraper-mvp/
├── main.py              # Script principal de scraping
├── db.py                # Operaciones de base de datos
├── config.py            # Configuración y variables de entorno
├── rules.py             # Reglas de clasificación por intención
├── sources.py           # Generación de URLs de búsqueda
├── kpi.py              # Análisis de métricas de negocio
├── viewer.py           # Dashboard de visualización
├── .env                # Variables de entorno
└── scraping.db         # Base de datos SQLite
```

## 🚀 Uso

### Ejecutar Scraping
```bash
python main.py
```

### Ver Dashboard
```bash
python viewer.py
```

### Ver KPIs
```bash
python kpi.py
```

## 🎯 Reglas de Clasificación

### Dolores (Problemas)
- "necesito", "tengo problema", "no puedo", "difícil"
- "busco solución", "ayuda con", "cómo resolver"

### Búsquedas (Intención de Compra)
- "busco", "buscando", "quiero contratar"
- "presupuesto", "cotización", "precio"

### Objeciones (Barreras)
- "caro", "muy caro", "demasiado", "cuesta mucho"
- "no tengo tiempo", "complicado", "difícil de usar"

## 📈 Resultados de Ejemplo

```
=== KPI DEL DÍA ===
Dolores únicos: 1
Objeciones: 0
Búsquedas proveedor: 1
Ruido: 70
Total únicos: 102

=== TOP KEYWORDS POR INTENCIÓN ===
dashboard pymes peru (dolor): 1
limpieza de piscina lima (busqueda): 1
```

## 🔧 Personalización

### Agregar Nuevos Patrones
Edita `rules.py` para agregar nuevos patrones de regex:

```python
patterns = {
    'dolor': [
        re.compile(r'nuevo_patron|otro_patron', re.IGNORECASE),
    ],
    'busqueda': [
        re.compile(r'patron_de_busqueda', re.IGNORECASE),
    ]
}
```

### Modificar Keywords
Actualiza la variable `KEYWORDS` en `.env`:
```env
KEYWORDS=tu keyword|otro keyword|tercer keyword
```

## 📊 Base de Datos

### Esquema
```sql
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    body TEXT,
    tag TEXT,
    published_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_tag ON posts(tag);
CREATE INDEX idx_posts_keyword ON posts(keyword);
```

## 🔄 Mejoras Futuras

- [ ] Integración con LLM para clasificación más precisa
- [ ] Dashboard web interactivo
- [ ] Scheduler automático
- [ ] Alertas en tiempo real
- [ ] Análisis de sentimientos
- [ ] Integración con CRM

## 📝 Notas Técnicas

- **Scrapling**: Librería de scraping que simula navegación real
- **Selectolax**: Parser HTML rápido para extracción de contenido
- **Slugify**: Normalización de texto para deduplicación
- **SQLite WAL**: Modo Write-Ahead Logging para mejor performance

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o consultas sobre el proyecto, por favor contacta al equipo de desarrollo.</content>
<filePath">d:\Projects\aqxion-scraper-mvp\README.md</filePath>
<parameter name="content"># Aqxion Scraper MVP

Un scraper web inteligente para extraer y analizar contenido relacionado con negocios en Perú, enfocado en identificar oportunidades de venta y marketing.

## 🚀 Características

### Extracción de Datos
- **Scraping stealth**: Usa Scrapling para evitar detección
- **Múltiples keywords**: Configurable vía variables de entorno
- **Extracción de cuerpo**: Obtiene contenido detallado de las páginas
- **Deduplicación inteligente**: Evita contenido duplicado usando slugs

### Análisis de Intención
- **Clasificación automática**: Identifica dolores, búsquedas y objeciones
- **Patrones regex**: Sistema configurable de reglas de negocio
- **Etiquetas semánticas**: Categoriza el contenido por intención comercial

### Infraestructura
- **Base de datos SQLite**: Almacenamiento eficiente con WAL mode
- **Logging estructurado**: Seguimiento completo de operaciones
- **Configuración externa**: Variables de entorno para fácil deployment
- **Métricas de negocio**: KPIs enfocados en oportunidades de venta

## 📊 KPIs de Negocio

- **Dolores únicos**: Problemas identificados en el mercado
- **Búsquedas proveedor**: Intención de compra activa
- **Objeciones**: Barreras y preocupaciones del mercado
- **Ruido**: Contenido no relevante (filtrado automáticamente)

## 🛠️ Instalación

### Prerrequisitos
- Python 3.11+
- Virtual environment

### Setup
```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install scrapling selectolax python-dotenv slugify

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus keywords y configuración
```

### Configuración (.env)
```env
# Keywords a buscar (separados por pipeline)
KEYWORDS=limpieza de piscina lima|agencia marketing lima|dashboard pymes peru

# Máximo de resultados por keyword
MAX_PER_KW=30

# Nivel de logging
LOG_LEVEL=INFO

# API Key para OpenAI (opcional, para futuras mejoras)
OPENAI_API_KEY=your_key_here
```

## 📁 Estructura del Proyecto

```
aqxion-scraper-mvp/
├── main.py              # Script principal de scraping
├── db.py                # Operaciones de base de datos
├── config.py            # Configuración y variables de entorno
├── rules.py             # Reglas de clasificación por intención
├── sources.py           # Generación de URLs de búsqueda
├── kpi.py              # Análisis de métricas de negocio
├── viewer.py           # Dashboard de visualización
├── .env                # Variables de entorno
└── scraping.db         # Base de datos SQLite
```

## 🚀 Uso

### Ejecutar Scraping
```bash
python main.py
```

### Ver Dashboard
```bash
python viewer.py
```

### Ver KPIs
```bash
python kpi.py
```

## 🎯 Reglas de Clasificación

### Dolores (Problemas)
- "necesito", "tengo problema", "no puedo", "difícil"
- "busco solución", "ayuda con", "cómo resolver"

### Búsquedas (Intención de Compra)
- "busco", "buscando", "quiero contratar"
- "presupuesto", "cotización", "precio"

### Objeciones (Barreras)
- "caro", "muy caro", "demasiado", "cuesta mucho"
- "no tengo tiempo", "complicado", "difícil de usar"

## 📈 Resultados de Ejemplo

```
=== KPI DEL DÍA ===
Dolores únicos: 1
Objeciones: 0
Búsquedas proveedor: 1
Ruido: 70
Total únicos: 102

=== TOP KEYWORDS POR INTENCIÓN ===
dashboard pymes peru (dolor): 1
limpieza de piscina lima (busqueda): 1
```

## 🔧 Personalización

### Agregar Nuevos Patrones
Edita `rules.py` para agregar nuevos patrones de regex:

```python
patterns = {
    'dolor': [
        re.compile(r'nuevo_patron|otro_patron', re.IGNORECASE),
    ],
    'busqueda': [
        re.compile(r'patron_de_busqueda', re.IGNORECASE),
    ]
}
```

### Modificar Keywords
Actualiza la variable `KEYWORDS` en `.env`:
```env
KEYWORDS=tu keyword|otro keyword|tercer keyword
```

## 📊 Base de Datos

### Esquema
```sql
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    body TEXT,
    tag TEXT,
    published_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_tag ON posts(tag);
CREATE INDEX idx_posts_keyword ON posts(keyword);
```

## 🔄 Mejoras Futuras

- [ ] Integración con LLM para clasificación más precisa
- [ ] Dashboard web interactivo
- [ ] Scheduler automático
- [ ] Alertas en tiempo real
- [ ] Análisis de sentimientos
- [ ] Integración con CRM

## 📝 Notas Técnicas

- **Scrapling**: Librería de scraping que simula navegación real
- **Selectolax**: Parser HTML rápido para extracción de contenido
- **Slugify**: Normalización de texto para deduplicación
- **SQLite WAL**: Modo Write-Ahead Logging para mejor performance

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o consultas sobre el proyecto, por favor contacta al equipo de desarrollo.</content>
</xai:function_call">README.md
