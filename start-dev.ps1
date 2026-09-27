$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$logDirectory = Join-Path $projectDirectory '.local'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

function Test-LocalUrl($url) {
    try { return (Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { return $false }
}

if (-not (Test-LocalUrl 'http://127.0.0.1:8000/api/health')) {
    $env:MACHBAR_HOST = '127.0.0.1'
    $env:MACHBAR_PORT = '8000'
    $env:MACHBAR_DB = Join-Path $projectDirectory 'backend/machbar.db'
    $serverPath = Join-Path $projectDirectory 'backend/server.py'
    $backendProcess = Start-Process -FilePath (Get-Command python -ErrorAction Stop).Source -ArgumentList @('-u', ('"' + $serverPath + '"')) -WorkingDirectory $projectDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'server.log') -RedirectStandardError (Join-Path $logDirectory 'server-error.log')
    Write-Host "Backend gestartet (PID $($backendProcess.Id))."
}
if (-not (Test-LocalUrl 'http://127.0.0.1:5173/')) {
    $vitePath = Join-Path $projectDirectory 'node_modules/vite/bin/vite.js'
    if (-not (Test-Path -LiteralPath $vitePath)) { throw 'Bitte zuerst npm install ausfuehren.' }
    $frontendProcess = Start-Process -FilePath (Get-Command node -ErrorAction Stop).Source -ArgumentList @(('"' + $vitePath + '"')) -WorkingDirectory $projectDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'vite.log') -RedirectStandardError (Join-Path $logDirectory 'vite-error.log')
    Write-Host "Frontend gestartet (PID $($frontendProcess.Id))."
}
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if ((Test-LocalUrl 'http://127.0.0.1:5173/') -and (Test-LocalUrl 'http://127.0.0.1:5173/api/health')) {
        Write-Host 'MACHBAR lokal: http://127.0.0.1:5173/'
        Write-Host 'Adminportal: http://127.0.0.1:5173/#/admin'
        exit 0
    }
    Start-Sleep -Milliseconds 500
}
throw "Server nicht erreichbar. Bitte Protokolle in $logDirectory pruefen."
