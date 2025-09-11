# Configurar Windows Task Scheduler usando schtasks
# Ejecutar como administrador

Write-Host "Configurando AQXION Scraper Scheduler..." -ForegroundColor Green

# Ruta al script batch
$scriptPath = Join-Path $PSScriptRoot "run_scraper.bat"

# Crear tarea programada cada 6 horas
schtasks /Create /TN "AQXION_Scraper_6h" /TR "\"$scriptPath\"" /SC HOURLY /MO 6 /F

Write-Host " Tarea programada configurada exitosamente!" -ForegroundColor Green
Write-Host " Se ejecutará cada 6 horas automáticamente" -ForegroundColor Yellow
Write-Host " Los logs se guardarán en: logs\kpi_YYYY-MM-DD.log" -ForegroundColor Cyan
