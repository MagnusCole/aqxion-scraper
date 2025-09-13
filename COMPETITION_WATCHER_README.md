# Competition Watcher v2.0

Un módulo independiente para analizar la competencia en el mercado de limpieza de piscinas en Lima, con separación completa entre recolección de datos y análisis.

## 🚀 Novedades v2.0

- **🗄️ Persistencia de Datos**: Base de datos SQLite para almacenar datos históricos
- **🔄 Modos Separados**: Recolección y análisis independientes
- **📊 Historial de Ejecuciones**: Seguimiento completo de todas las ejecuciones
- **⚡ Optimización**: Mejor rendimiento y manejo de errores
- **🎯 Flexibilidad**: Múltiples modos de operación según necesidad

## 🛠️ Instalación

El módulo ya está incluido en el proyecto principal. Solo necesitas:

```bash
# Asegurarse de tener las dependencias
pip install -r requirements.txt
```

## 📊 Modos de Operación

### 🎯 Modo FULL (Completo)
Ejecuta recolección + análisis en una sola operación:

```bash
python competition_watcher_run.py --mode full
```

### 📥 Modo COLLECT (Solo Recolección)
Solo recolecta y guarda datos de competidores:

```bash
# Recolectar datos básicos
python competition_watcher_run.py --mode collect

# Recolectar con límite específico
python competition_watcher_run.py --mode collect --load-limit 20
```

### 🔬 Modo ANALYZE (Solo Análisis)
Analiza datos existentes en la base de datos:

```bash
# Analizar todos los datos disponibles
python competition_watcher_run.py --mode analyze

# Analizar con límite de datos
python competition_watcher_run.py --mode analyze --load-limit 15
```

### 📚 Modo HISTORY (Historial)
Revisa el historial de ejecuciones anteriores:

```bash
# Ver últimas 10 ejecuciones
python competition_watcher_run.py --mode history

# Ver más ejecuciones
python competition_watcher_run.py --mode history --history-limit 20
```

## 📋 Parámetros Disponibles

### Parámetros Globales
- `--mode`: Modo de operación (full/collect/analyze/history) - default: full
- `--help`: Mostrar ayuda completa

### Parámetros por Modo
- `--load-limit`: Límite de competidores a procesar (para collect/analyze)
- `--history-limit`: Número de ejecuciones a mostrar (para history)

## 📈 Qué Analiza

### Información de Competidores
- **Nombre de Empresa**: Extraído de títulos, headers y meta tags
- **Servicios Ofrecidos**: Limpieza, mantenimiento, reparaciones, etc.
- **Ubicación**: Zona de cobertura en Lima
- **Información de Precios**: Rangos de precios cuando están disponibles
- **Datos de Contacto**: Teléfonos y emails
- **Descripción**: Resumen del negocio

### Análisis de Mercado
- **Categorías de Servicios**: Agrupación por tipo de servicio
- **Distribución Geográfica**: Cobertura por zonas de Lima
- **Rangos de Precios**: Análisis de precios (Soles vs Dólares)
- **Gaps de Mercado**: Áreas con poca competencia
- **Oportunidades**: Ideas para diferenciarse

## � Base de Datos

### Estructura de Tablas
- **competitors**: Datos de competidores recolectados
- **competition_analysis**: Resultados de análisis
- **competition_runs**: Historial de ejecuciones

### Persistencia Automática
- Los datos se guardan automáticamente en cada recolección
- Historial completo de todas las ejecuciones
- Posibilidad de análisis retrospectivo

## �📋 Ejemplos de Uso

### Flujo de Trabajo Típico

```bash
# 1. Recolectar datos semanalmente
python competition_watcher_run.py --mode collect --load-limit 25

# 2. Analizar datos cuando necesites insights
python competition_watcher_run.py --mode analyze

# 3. Revisar historial de cambios
python competition_watcher_run.py --mode history

# 4. Análisis completo cuando necesites todo fresco
python competition_watcher_run.py --mode full
```

### Ejemplo de Reporte

```
📊 REPORTE DE ANÁLISIS DE COMPETENCIA
Mercado: limpieza de piscina lima

Fecha de Análisis: 2025-01-15 14:30:00
Competidores Analizados: 8

🎯 Servicios más ofrecidos:
  • Limpieza/Mantenimiento: 6 competidores
  • Reparaciones: 3 competidores
  • Tratamiento Químico: 4 competidores

📍 Distribución geográfica:
  • Lima, Perú: 8 competidores

💰 Información de precios:
  • Soles: 5 competidores
  • No especificado: 3 competidores
```

## 🔧 Funcionamiento Interno

### 1. Búsqueda en Google
- Utiliza Google Custom Search Engine (GCS) si está configurado
- Filtra URLs relevantes (empresas locales, servicios)
- Evita contenido irrelevante (Wikipedia, redes sociales)

### 2. Extracción de Datos
- **Sin IA**: Usa expresiones regulares y patrones HTML
- **Patrones Inteligentes**: Busca títulos, meta descriptions, párrafos
- **Validación**: Filtra contenido irrelevante automáticamente

### 3. Análisis de Mercado
- **Categorización**: Agrupa servicios por tipo
- **Estadísticas**: Calcula frecuencias y distribuciones
- **Insights**: Identifica patrones y oportunidades

### 4. Generación de Reportes
- **Formato Markdown**: Fácil de leer y compartir
- **Estructurado**: Secciones claras y organizadas
- **Exportable**: Se puede guardar como archivo

## ⚙️ Configuración

### Variables de Entorno
```env
# Google Custom Search (opcional)
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_cse_id

# Configuración de búsqueda
MAX_CONCURRENT_REQUESTS=5
SEARCH_ENGINE=google
```

### Personalización Programática
```python
from scraping.competition_watcher import competition_watcher

# Cambiar keyword
competition_watcher.keyword = "servicios piscina surco"

# Ejecutar análisis personalizado
analysis = await competition_watcher.run_competition_analysis(max_competitors=20)

# Generar reporte
report = competition_watcher.generate_report("mi_reporte.md")
```

## 📊 Casos de Uso

### 1. Investigación de Mercado
- Entender quiénes son tus competidores
- Conocer qué servicios ofrecen
- Identificar precios del mercado

### 2. Estrategia de Posicionamiento
- Encontrar gaps de mercado
- Identificar oportunidades de diferenciación
- Definir estrategia de precios

### 3. Monitoreo Continuo
- Ejecutar periódicamente para ver cambios
- Detectar nuevos competidores
- Actualizar estrategia según evolución del mercado

### 4. Análisis Histórico
- Comparar evolución del mercado
- Ver tendencias de crecimiento
- Analizar cambios en competencia

## 🔍 Limitaciones

- **Sin IA Avanzada**: No usa GPT para análisis profundo
- **Búsqueda Limitada**: Depende de Google CSE (si no está configurado, usa búsqueda básica)
- **Extracción Simple**: Basada en patrones HTML, no en comprensión semántica
- **Cobertura Limitada**: Solo analiza las primeras URLs encontradas

## 🚀 Mejoras Futuras

- [ ] Integración con IA para análisis más profundo
- [ ] Búsqueda en múltiples motores (DuckDuckGo, Bing)
- [ ] Análisis de sentimientos en reseñas
- [ ] Dashboard web interactivo
- [ ] Alertas automáticas de nuevos competidores
- [ ] Análisis de redes sociales
- [ ] Exportación a Excel/CSV
- [ ] API REST para integración

## 📞 Soporte

Para soporte técnico o consultas:
- **Documentación**: Ver carpeta `docs/`
- **Issues**: GitHub Issues del proyecto principal
- **Logs**: El sistema genera logs detallados durante la ejecución

---

**Competition Watcher v2.0** - Tu herramienta inteligente para entender la competencia en el mercado de limpieza de piscinas. 🔍📊💾
