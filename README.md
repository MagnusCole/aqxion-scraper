# Aqxion Scraper MVP

Un sistema completo de scraping web inteligente para análisis de mercado y oportunidades de negocio en Perú, implementando la metodología Eugene Schwartz para identificar dolores, búsquedas y objeciones del mercado.

## 🚀 Características Principales

### 🎯 Análisis de Mercado Eugene Schwartz
- **Implementación completa** de la metodología Eugene Schwartz
- **Identificación de dolores** del mercado objetivo
- **Detección de búsquedas activas** de proveedores/servicios
- **Análisis de objeciones** y barreras del mercado
- **Clasificación automática** de intención comercial
- **Análisis de madurez del mercado** y oportunidades

### 🕷️ Sistema de Scraping Inteligente
- **Scraping stealth** con Scrapling para evitar detección
- **Múltiples motores de scraping**:
  - EfficientScraper: Alto rendimiento con concurrencia
  - MarketingPainPointsScraper: Enfocado en puntos de dolor
  - SimpleScraplingScraper: Scraping básico con aiohttp
- **Gestión inteligente de rate limiting** por dominio
- **Deduplicación avanzada** usando hashes de contenido
- **Validación de calidad** de contenido extraído
- **Extracción de metadatos** completos (títulos, cuerpos, URLs)

### 🤖 Inteligencia Artificial Integrada
- **AIService** con OpenAI GPT para análisis de contenido
- **Generación automática de keywords** relevantes
- **Clasificación semántica** de intenciones comerciales
- **Análisis de sentimiento** y relevancia
- **Sistema de circuit breaker** para manejo de errores de API
- **Cache inteligente** de análisis previos

### 💾 Infraestructura Robusta
- **Base de datos SQLite** optimizada con WAL mode
- **Sistema de caché dual**:
  - Redis distribuido (con fallback local)
  - SmartCacheManager para optimización de memoria
- **Logging estructurado** con múltiples niveles
- **Configuración centralizada** vía variables de entorno
- **Métricas y monitoreo** en tiempo real

### 📊 Dashboard Web Interactivo
- **Dashboard completo** con Streamlit
- **Visualización de KPIs** en tiempo real
- **Análisis de radar de mercado** con métricas avanzadas
- **Gráficos interactivos** de tendencias
- **Filtros por fecha y keyword**
- **Exportación de datos** a CSV/Excel

### 🛠️ Utilidades y Herramientas
- **TaskManager**: Sistema de gestión de tareas asíncronas
- **CircuitBreaker**: Protección contra fallos en cascada
- **KPI Calculator**: Cálculos automáticos de métricas de negocio
- **PlanningSystem**: Planificación estratégica de scraping
- **ContextOptimizer**: Optimización de contexto para IA
- **AlertSystem**: Notificaciones automáticas de leads

### 🔧 Arquitectura Modular
```
aqxion-scraper-mvp/
├── core/           # Sistema Eugene Schwartz y lógica principal
├── scraping/       # Motores de scraping especializados
├── ai/            # Servicios de IA y análisis
├── cache/         # Sistemas de caché (Redis + local)
├── config/        # Configuración centralizada
├── database/      # Operaciones de base de datos
├── utils/         # Utilidades y herramientas
├── cleaners/      # Scripts de limpieza de código
├── demos/         # Ejemplos y demostraciones
├── docs/          # Documentación completa
├── tests/         # Suite de pruebas
├── web/           # Dashboard interactivo
└── instructions/  # Guías de desarrollo
```

## 📈 KPIs y Métricas de Negocio

### Métricas Principales
- **Dolores únicos**: Problemas identificados en el mercado
- **Búsquedas proveedor**: Intención de compra activa
- **Objeciones**: Barreras y preocupaciones del mercado
- **Score de relevancia**: Puntuación de calidad del contenido
- **Tasa de conversión**: Leads generados vs. contenido analizado

### Métricas Técnicas
- **Tasa de éxito de scraping**: URLs procesadas exitosamente
- **Velocidad de procesamiento**: Páginas/minuto
- **Eficiencia de caché**: Hit rate de caché
- **Uptime del sistema**: Disponibilidad del servicio
- **Cobertura de keywords**: Porcentaje de keywords procesados

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Python 3.11+
- Redis (opcional, incluye versión portable)
- Git

### Setup Rápido
```bash
# Clonar repositorio
git clone <repository-url>
cd aqxion-scraper-mvp

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones
```

### Configuración Avanzada
```bash
# Instalar Redis portable (incluido)
# El sistema funciona con o sin Redis

# Configurar base de datos
python -c "from database.db import init_db; init_db()"

# Ejecutar pruebas
python -m pytest tests/
```

## 🚀 Uso del Sistema

### Ejecución Básica
```bash
# Ejecutar scraping completo
python core/main_async.py

# Ejecutar con configuración específica
python core/main_async.py --keyword "limpieza de piscina en lima"

# Ejecutar dashboard web
streamlit run web/dashboard_web.py
```

### Uso Programático
```python
from core.eugene_schwartz_system import EugeneSchwartzSystem
from scraping.efficient_scraper import EfficientScraper
from ai.ai_service import AIService

# Inicializar sistema
system = EugeneSchwartzSystem()
scraper = EfficientScraper()
ai_service = AIService()

# Ejecutar análisis completo
async def analyze_market():
    results = await system.analyze_market_opportunity("tu keyword")
    return results
```

### API del Dashboard
- **URL**: `http://localhost:8501`
- **Métricas en tiempo real**
- **Filtros interactivos**
- **Exportación de datos**
- **Visualizaciones avanzadas**

## 🔧 Configuración Detallada

### Variables de Entorno
```env
# Base de datos
DB_PATH=scraping.db

# Scraping
MAX_CONCURRENT_REQUESTS=10
MIN_TITLE_LENGTH=10
MIN_BODY_LENGTH=50

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4

# Redis (opcional)
REDIS_URL=redis://localhost:6380

# Logging
LOG_LEVEL=INFO
```

### Configuración de Keywords
```python
# En config/sources.py
KEYWORDS = [
    "limpieza de piscina en lima",
    "mantenimiento piscinas",
    "servicios piscina lima"
]
```

## 📊 Funcionalidades Avanzadas

### Sistema de Caché Inteligente
- **Redis distribuido** con puerto configurable (6380)
- **Fallback automático** a caché local
- **Compresión de datos** para optimización
- **TTL configurable** por tipo de contenido
- **Métricas de rendimiento** en tiempo real

### Gestión de Tareas Asíncronas
- **TaskManager** para operaciones complejas
- **Ejecución paralela** con control de concurrencia
- **Reintentos automáticos** con backoff exponencial
- **Monitoreo de progreso** en tiempo real
- **Cancelación graceful** de tareas

### Sistema de Alertas
- **Alertas automáticas** de leads calificados
- **Notificaciones por email/SMS** (configurable)
- **Umbrales personalizables** de activación
- **Historial completo** de alertas
- **Integración con sistemas externos**

### Optimización de Rendimiento
- **Pool de conexiones** HTTP optimizado
- **Compresión automática** de respuestas
- **Rate limiting inteligente** por dominio
- **Gestión de memoria** eficiente
- **Procesamiento asíncrono** completo

## 🧪 Testing y Calidad

### Suite de Pruebas
```bash
# Ejecutar todas las pruebas
python -m pytest tests/ -v

# Pruebas específicas
python -m pytest tests/test_scraping.py
python -m pytest tests/test_ai_service.py

# Cobertura de código
python -m pytest --cov=src --cov-report=html
```

### Pruebas de Integración
- **IntegrationTester** para validación end-to-end
- **Pruebas de carga** con múltiples keywords
- **Validación de datos** en base de datos
- **Verificación de APIs** externas

## 📚 Documentación Adicional

### Guías Disponibles
- `docs/AI_GUIDE.md` - Guía completa de IA
- `docs/EFFICIENT_SCRAPING_README.md` - Optimización de scraping
- `instructions/python.instructions.md` - Guía de desarrollo
- `docs/ai_best_practices.md` - Mejores prácticas de IA

### Scripts de Utilidad
- `cleaners/` - Scripts de limpieza de código
- `demos/` - Ejemplos de uso
- `utils/` - Herramientas adicionales

## 🔒 Seguridad y Mejores Prácticas

### Medidas de Seguridad
- **Rate limiting** para evitar bloqueos
- **Headers realistas** en requests HTTP
- **Gestión segura** de API keys
- **Validación de entrada** en todas las funciones
- **Logging seguro** sin exposición de datos sensibles

### Mejores Prácticas
- **Entorno virtual** obligatorio
- **Variables de entorno** para configuración
- **Control de versiones** con Git
- **Documentación** actualizada
- **Pruebas automatizadas** antes de deploy

## 🚀 Deployment y Escalabilidad

### Docker
```bash
# Construir imagen
docker build -t aqxion-scraper .

# Ejecutar contenedor
docker run -p 8501:8501 aqxion-scraper
```

### Docker Compose
```bash
# Ejecutar stack completo
docker-compose up -d

# Servicios incluidos:
# - Aplicación principal
# - Redis
# - Base de datos
# - Dashboard web
```

### Escalabilidad
- **Arquitectura modular** para fácil escalado
- **Soporte para múltiples instancias**
- **Balanceo de carga** integrado
- **Monitoreo distribuido**
- **Backup automático** de datos

## 🤝 Contribución

### Guías para Contribuidores
1. **Fork** el repositorio
2. **Crear branch** para nueva funcionalidad
3. **Seguir estándares** de código
4. **Agregar tests** para nuevas funciones
5. **Actualizar documentación**
6. **Crear Pull Request**

### Estándares de Código
- **PEP 8** para Python
- **Type hints** obligatorios
- **Docstrings** completos
- **Logging estructurado**
- **Manejo de errores** robusto

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- **Issues**: GitHub Issues
- **Documentación**: Ver carpeta `docs/`
- **Ejemplos**: Ver carpeta `demos/`

---

**Aqxion Scraper MVP** - Tu herramienta definitiva para análisis de mercado inteligente y generación de oportunidades de negocio. 🚀✨
