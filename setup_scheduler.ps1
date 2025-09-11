# Configurar Windows Task Scheduler para Aqxion Scraper
# Ejecutar cada 6 horas

$TaskName = "Aqxion Scraper"
$ScriptPath = "$PSScriptRoot\run_scraper.ps1"
$LogPath = "$PSScriptRoot\logs\log_%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%.txt"

# Verificar si la tarea ya existe y eliminarla
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tarea existente eliminada." -ForegroundColor Yellow
}

# Crear nueva tarea
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File \"$ScriptPath\""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Ejecuta Aqxion Scraper cada 6 horas"

Write-Host "Tarea programada configurada exitosamente." -ForegroundColor Green
Write-Host "La tarea se ejecutará cada 6 horas." -ForegroundColor Green
