# Market Radar - Sistema Nervioso del Mercado

Un sistema inteligente que convierte datos dispersos del internet en inteligencia accionable sobre el mercado, funcionando como el "sistema nervioso" de tu negocio.

## 🚀 Características Principales

### 📡 Sensores Inteligentes
- **Google Search Sensor**: Búsqueda inteligente de competidores
- **Google Reviews Sensor**: Extracción de reseñas y opiniones *(próximamente)*
- **Forums Monitor**: Monitoreo de foros y comunidades *(próximamente)*
- **Marketplaces Tracker**: Seguimiento de precios y ofertas *(próximamente)*

### 🧠 Procesamiento Inteligente
- **Data Extractor**: Extracción automática de información relevante
- **Pattern Detector**: Detección de patrones y tendencias
- **Sentiment Analyzer**: Análisis básico de sentimiento *(próximamente)*

### 🎯 Generador de Señales
- **Business Signals**: Señales específicas de negocio accionables
- **Opportunity Detector**: Identificación automática de oportunidades
- **Threat Monitor**: Detección de amenazas del mercado
- **Trend Analyzer**: Análisis de tendencias del mercado

### 📊 Dashboard Interactivo
- **Signal Dashboard**: Visualización clara de señales críticas
- **Priority Alerts**: Alertas por nivel de importancia
- **Strategic Recommendations**: Recomendaciones basadas en datos

---

## 🛠️ Instalación y Configuración

### Requisitos
```bash
pip install -r requirements.txt
```

### Estructura del Módulo
```
market_radar/
├── sensors/          # 📡 Motores de búsqueda
├── processors/       # 🧠 Procesadores de datos
├── signals/          # 🎯 Generador de señales
├── storage/          # 💾 Almacenamiento
├── dashboard/        # 📊 Panel de control
├── cli.py           # 🖥️ Interfaz de comandos
└── config.py        # ⚙️ Configuración
```

---

## 📊 Uso Básico

### Escaneo Completo
```bash
# Escaneo completo del mercado
python -m market_radar.cli --keyword "limpieza piscina lima"

# Con límite específico de resultados
python -m market_radar.cli --keyword "servicios piscina miraflores" --limit 10
```

### Solo Sensor
```bash
# Ejecutar solo búsqueda en Google
python -m market_radar.cli --sensor google --keyword "piscina surco"
```

### Modo Verbose
```bash
# Con información detallada
python -m market_radar.cli --keyword "mantenimiento piscina" --verbose
```

---

## 📋 Tipos de Señales

### 🟢 Oportunidades (Opportunities)
- **Mercado con Baja Competencia**: Pocos competidores activos
- **Servicio Poco Ofrecido**: Nichos con baja cobertura
- **Zona Sin Cobertura**: Áreas geográficas desatendidas

### 🔴 Amenazas (Threats)
- **Alta Competencia**: Mercado saturado
- **Guerra de Precios**: Competidores bajando precios
- **Nuevo Competidor**: Entrada de nuevos actores

### 🟡 Tendencias (Trends)
- **Servicio Popular**: Servicios de alta demanda
- **Zona Activa**: Ubicaciones con alta actividad
- **Cambio de Comportamiento**: Evolución del mercado

### 🟠 Alertas (Alerts)
- **Baja Visibilidad**: Poca información de contacto
- **Baja Relevancia**: Resultados no específicos
- **Problemas Técnicos**: Errores en el procesamiento

---

## 🎯 Ejemplo de Output

```
==============================================================================
📡 MARKET RADAR - SISTEMA NERVIOSO DEL MERCADO
==============================================================================

📊 RESUMEN GENERAL
   Señales Totales: 6
   Alta Prioridad: 1
   Por Tipo:
     🟢 Opportunity: 3
     🟠 Alert: 1
     🟡 Trend: 2

🚨 SEÑALES DE ALTA PRIORIDAD (1)
   1. 🟢 🚨 Mercado con Baja Competencia
      Solo 3 competidores encontrados. Oportunidad para entrar al mercado.
      Confianza: 85.0%

💡 RECOMENDACIONES ESTRATÉGICAS
   🟢 OPORTUNIDADES: 3 señales detectadas
      → Considerar expansión en nichos identificados
      → Evaluar entrada en mercados con baja competencia
```

---

## ⚙️ Configuración Avanzada

### Variables de Configuración
```python
# market_radar/config.py
SENSOR_CONFIG = {
    "google_search": {
        "max_results": 20,
        "timeout": 30
    }
}

PROCESSING_CONFIG = {
    "min_relevance_threshold": 0.5,
    "max_concurrent_requests": 5
}

SIGNALS_CONFIG = {
    "opportunity_threshold": 0.7,
    "threat_threshold": 0.8
}
```

### Personalización Programática
```python
from market_radar.sensors.google_search import GoogleSearchSensor
from market_radar.processors.data_extractor import DataExtractor
from market_radar.signals.business_signals import BusinessSignalsGenerator

# Configurar sensor personalizado
sensor = GoogleSearchSensor()
results = await sensor.search("tu keyword", limit=15)

# Procesar datos
extractor = DataExtractor()
processed = await extractor.process({"results": results})

# Generar señales
signals_gen = BusinessSignalsGenerator()
signals = await signals_gen.generate(processed)
```

---

## 🔧 Arquitectura Técnica

### Flujo de Datos
```
Sensores → Procesadores → Generador de Señales → Dashboard
    ↓          ↓              ↓                    ↓
  Datos      Información    Señales            Visualización
 Crudos     Estructurada   Accionables         Interactiva
```

### Componentes Principales

#### 1. Sensores (Sensors)
- **Responsabilidad**: Recolectar datos del mercado
- **Entrada**: Keywords y parámetros de búsqueda
- **Salida**: Datos crudos del internet

#### 2. Procesadores (Processors)
- **Responsabilidad**: Extraer información relevante
- **Entrada**: Datos crudos de sensores
- **Salida**: Información estructurada y limpia

#### 3. Generador de Señales (Signals)
- **Responsabilidad**: Convertir datos en insights accionables
- **Entrada**: Información procesada
- **Salida**: Señales de negocio priorizadas

#### 4. Dashboard
- **Responsabilidad**: Presentar información de manera clara
- **Entrada**: Señales generadas
- **Salida**: Reportes y visualizaciones

---

## 📈 Casos de Uso

### 1. Investigación de Mercado
```bash
# Analizar competencia en zona específica
python -m market_radar.cli --keyword "limpieza piscina miraflores"
```

### 2. Monitoreo Continuo
```bash
# Monitoreo semanal automatizado
python -m market_radar.cli --keyword "servicios piscina lima"
# → Configurar como tarea programada
```

### 3. Detección de Oportunidades
```bash
# Buscar nichos desatendidos
python -m market_radar.cli --keyword "mantenimiento piscina 24h"
```

### 4. Análisis de Tendencias
```bash
# Ver evolución del mercado
python -m market_radar.cli --keyword "piscina ecologica lima"
```

---

## 🎯 Beneficios del Sistema

### Para Emprendedores
- **Toma de Decisiones**: Datos objetivos para elegir mercados
- **Identificación de Nichos**: Encontrar oportunidades desatendidas
- **Validación de Ideas**: Confirmar demanda antes de invertir

### Para Empresas
- **Monitoreo Competitivo**: Seguimiento continuo de competidores
- **Detección Temprana**: Alertas sobre cambios en el mercado
- **Optimización de Recursos**: Enfocar esfuerzos en oportunidades reales

### Para Consultores
- **Análisis Rápido**: Evaluación rápida de mercados
- **Reportes Profesionales**: Insights listos para clientes
- **Actualización Continua**: Mantener análisis al día

---

## 🚀 Roadmap

### ✅ Fase 1 (Actual)
- [x] Sensor Google Search básico
- [x] Procesador de datos inteligente
- [x] Generador de señales de negocio
- [x] Dashboard de señales
- [x] CLI funcional

### 🔄 Fase 2 (Próximamente)
- [ ] Sensor Google Reviews
- [ ] Análisis de sentimiento
- [ ] Monitoreo de foros
- [ ] Dashboard web interactivo

### 🔮 Fase 3 (Futuro)
- [ ] Integración con marketplaces
- [ ] API REST para integraciones
- [ ] Machine Learning para predicciones
- [ ] Alertas en tiempo real

---

## 📞 Soporte y Contribución

### Reportar Issues
- Usa los issues de GitHub para reportar bugs
- Incluye logs y pasos para reproducir

### Contribuir
- Fork el proyecto
- Crea una rama para tu feature
- Submit pull request con descripción clara

### Documentación
- README actualizado regularmente
- Ejemplos de uso en `examples/`
- API documentation en `docs/`

---

**Market Radar** - Tu sistema nervioso del mercado. Convirtiendo datos en decisiones. 🎯📊
