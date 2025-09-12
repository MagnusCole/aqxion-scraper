# Mejores Prácticas de Prompts para Aqxion Scraper
# Basado en análisis del repositorio system-prompts-and-models-of-ai-tools

## 1. ESTRUCTURA DE PROMPTS EFECTIVOS

### Patrón de Cursor para consultas precisas:
```
[CONTEXTO] + [TAREA ESPECÍFICA] + [FORMATO ESPERADO] + [RESTRICCIONES]
```

### Aplicación a nuestro scraper:
- **Contexto**: "Eres un experto en análisis de contenido web para marketing digital en Perú"
- **Tarea específica**: "Clasifica este contenido según categorías de intención del usuario"
- **Formato esperado**: "Responde solo con JSON válido: {tag, confidence, reasoning}"
- **Restricciones**: "No incluyas texto adicional fuera del JSON"

## 2. TÉCNICAS DE GESTIÓN DE TAREAS (Manus/Devin)

### Sistema de fases para tareas complejas:
```
FASE 1: ANÁLISIS Y PLANIFICACIÓN
- Entender el alcance de la tarea
- Identificar subtareas
- Estimar recursos necesarios

FASE 2: EJECUCIÓN
- Ejecutar subtareas en orden
- Monitorear progreso
- Manejar errores

FASE 3: VALIDACIÓN Y OPTIMIZACIÓN
- Verificar resultados
- Optimizar rendimiento
- Documentar lecciones aprendidas
```

### Aplicación a nuestro scraper:
- **Fase 1**: Análisis de keywords y configuración de scraping
- **Fase 2**: Ejecución del scraping con manejo de rate limits
- **Fase 3**: Validación de datos y optimización de consultas

## 3. MANEJO DE CONTEXTO LARGO (Devin)

### Técnicas para optimizar GPT-5 Nano:
```
- Dividir consultas largas en chunks manejables
- Usar resúmenes intermedios para mantener contexto
- Implementar sistema de "memoria" para conversaciones largas
- Priorizar información más relevante
```

### Parámetros específicos para GPT-5 Nano:
```python
{
    "model": "gpt-5-nano-2025-08-07",
    "reasoning_effort": "low",  # Para respuestas rápidas
    "max_completion_tokens": 500,  # Límite de respuesta
    # NO usar temperature - GPT-5 Nano solo acepta valor por defecto
}
```

## 4. GESTIÓN DE ERRORES Y RECUPERACIÓN (RooCode)

### Patrón de manejo de errores:
```
1. Detectar error automáticamente
2. Clasificar tipo de error (rate limit, API, parsing, etc.)
3. Intentar recuperación automática
4. Escalar a usuario solo si es necesario
5. Registrar para análisis posterior
```

### Aplicación específica:
```python
async def safe_ai_call(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await ai_service.client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": prompt}],
                reasoning_effort="low",
                max_completion_tokens=500
            )
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"AI call failed after {max_retries} attempts: {e}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## 5. SISTEMA DE PLANIFICACIÓN (Cline)

### Para tareas complejas de scraping:
```
PLAN MODE:
1. Analizar requerimientos del usuario
2. Explorar el código existente
3. Crear plan detallado con mermaid diagrams si es necesario
4. Obtener aprobación del usuario
5. Ejecutar plan paso a paso

ACT MODE:
1. Implementar cambios según el plan aprobado
2. Ejecutar pruebas después de cada cambio
3. Validar funcionalidad
4. Documentar cambios realizados
```

## 6. OPTIMIZACIONES PARA GPT-5 NANO

### Configuración óptima:
```python
# Para clasificación rápida (bajo costo)
CLASSIFICATION_CONFIG = {
    "model": "gpt-5-nano-2025-08-07",
    "reasoning_effort": "low",
    "max_completion_tokens": 300,
    "messages": [...]
}

# Para generación de keywords (más contexto)
KEYWORD_CONFIG = {
    "model": "gpt-5-nano-2025-08-07",
    "reasoning_effort": "low",
    "max_completion_tokens": 1000,
    "messages": [...]
}
```

### Estrategias de caching:
```
1. Cache por hash de contenido para evitar re-clasificación
2. Cache por combinación de parámetros
3. TTL inteligente basado en frecuencia de uso
4. Invalidación automática cuando cambian las reglas
```

## 7. MEJORES PRÁCTICAS DE COMUNICACIÓN

### Con el usuario:
- Ser específico y directo
- Usar formato Markdown consistente
- Proporcionar contexto antes de pedir decisiones
- Mantener respuestas concisas pero informativas

### Con el sistema:
- Registrar todas las acciones importantes
- Proporcionar feedback visual del progreso
- Manejar errores gracefully
- Optimizar para velocidad y costo

## 8. INTEGRACIÓN CON HERRAMIENTAS EXISTENTES

### Mejoras al sistema actual:
1. **Mejorar prompts de clasificación** usando técnicas de Cursor
2. **Implementar gestión de tareas** basada en Manus
3. **Optimizar uso de GPT-5 Nano** con parámetros correctos
4. **Agregar sistema de recuperación de errores** de RooCode
5. **Implementar planificación** para tareas complejas

### Beneficios esperados:
- ✅ Mayor precisión en clasificación de contenido
- ✅ Mejor manejo de tareas complejas
- ✅ Reducción de costos con GPT-5 Nano optimizado
- ✅ Mayor robustez del sistema
- ✅ Mejor experiencia de usuario</content>
<parameter name="filePath">d:\Projects\aqxion-scraper-mvp\ai_best_practices.md
