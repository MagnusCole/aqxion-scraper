# Aqxion Scraper MVP - Inicio Rápido

## 🚀 Cómo Usar

### 1. Ejecutar Scraper
```bash
python main.py
```

### 2. Ver KPIs
```bash
python kpi.py
```

### 3. Dashboard Web
```bash
streamlit run dashboard_web.py
```

### 4. Scheduler Automático (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
```

## 📊 KPIs Generados

- **Dolores únicos**: Problemas del mercado (necesidades, dolores)
- **Búsquedas proveedor**: Intención de compra activa
- **Objeciones**: Barreras y preocupaciones
- **Ruido**: Contenido no relevante

### Ejemplo de Output:
```
=== KPI DEL DÍA ===
Dolores únicos: 3
Objeciones: 1
Búsquedas proveedor: 5
Ruido: 45
Total únicos: 54
```

## 🔄 Flujo de Datos

```
🔍 DuckDuckGo Search → 📄 Extracción de URLs → 🏷️ Tagging de Intención → 💾 SQLite DB → 📊 KPIs → 🖥️ Dashboard
```

1. **Búsqueda**: Keywords configurados en `.env`
2. **Extracción**: URLs y contenido usando Scrapling
3. **Análisis**: Regex patterns identifican intención
4. **Almacenamiento**: Posts con tags en SQLite
5. **Visualización**: Dashboard web con métricas

## ⚠️ Alertas Automáticas

El scraper muestra alertas en consola para posts relevantes:
```
⚠️ NUEVO DOLOR: Necesito solución para limpieza de piscina...
⚠️ NUEVO BUSQUEDA: Busco proveedor de mantenimiento...
```

## 📁 Estructura del Proyecto

```
aqxion-scraper-mvp/
├── main.py              # 🚀 Scraper principal
├── dashboard_web.py     # 🖥️ Dashboard Streamlit
├── kpi.py              # 📊 KPIs de negocio
├── db.py               # 💾 Base de datos
├── config.py           # ⚙️ Configuración
├── rules.py            # 🎯 Sistema de tagging
├── run_scraper.ps1     # 🔄 Script de ejecución
├── setup_scheduler.ps1 # ⏰ Configuración automática
├── logs/               # 📝 Logs diarios
└── .env               # 🔐 Variables de entorno
```

## 🎯 Características Clave

- ✅ **Scheduler automático** cada 6 horas
- ✅ **Dashboard web** con métricas en tiempo real
- ✅ **Alertas manuales** para oportunidades de venta
- ✅ **Tagging inteligente** de intención comercial
- ✅ **Extracción de cuerpo** y fechas de publicación
- ✅ **Deduplicación** inteligente
- ✅ **Logging estructurado** con archivos diarios

## 🔧 Configuración (.env)

```env
KEYWORDS=limpieza de piscina lima|agencia marketing lima|dashboard pymes peru
MAX_PER_KW=30
LOG_LEVEL=INFO
```

## 📞 Próximos Pasos

1. **Ejecutar scraper**: `python main.py`
2. **Configurar scheduler**: `powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1`
3. **Ver dashboard**: `streamlit run dashboard_web.py`
4. **Monitorear logs**: `logs\log_YYYY-MM-DD.txt`

¡Listo para identificar oportunidades de negocio en Perú! 🎯</content>
<parameter name="filePath">d:\Projects\aqxion-scraper-mvp\README_RAPIDO.md
