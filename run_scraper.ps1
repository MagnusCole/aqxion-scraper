# Aqxion Scraper - Script de ejecución automática con logging
# Ejecuta el scraper y genera KPIs con logging automático

param(
    [string]$LogFile = "logs\log_$((Get-Date).ToString('yyyy-MM-dd')).txt"
)

Write-Host "[$(Get-Date)] Iniciando ejecución automática del scraper..." -ForegroundColor Green
Write-Host "" -ForegroundColor Green

try {
    # Activar entorno virtual
    Write-Host "[$(Get-Date)] Activando entorno virtual..." -ForegroundColor Yellow
    & ".venv\Scripts\activate.ps1"
    
    # Ejecutar scraper principal
    Write-Host "[$(Get-Date)] Ejecutando scraper principal..." -ForegroundColor Yellow
    & python main.py
    
    # Ejecutar análisis de KPIs
    Write-Host "[$(Get-Date)] Generando KPIs..." -ForegroundColor Yellow
    & python kpi.py
    
    # Desactivar entorno virtual
    Write-Host "[$(Get-Date)] Desactivando entorno virtual..." -ForegroundColor Yellow
    & deactivate
    
    Write-Host "[$(Get-Date)] Ejecución completada exitosamente." -ForegroundColor Green
    
} catch {
    Write-Host "[$(Get-Date)] ERROR: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host "" -ForegroundColor Green
}
