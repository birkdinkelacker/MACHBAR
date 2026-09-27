$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$serverUrl = 'http://127.0.0.1:8000'

try {
    $health = Invoke-RestMethod "$serverUrl/api/health" -TimeoutSec 2
    if ($health.ok) {
        Write-Host "MACHBAR läuft bereits: $serverUrl/#/admin"
        exit 0
    }
} catch {
    # Start the local server when it is not reachable.
}

if (-not (Test-Path -LiteralPath (Join-Path $projectDirectory 'dist/index.html'))) {
    throw 'Das Frontend fehlt. Bitte zuerst npm install und npm run build ausführen.'
}

$pythonPath = (Get-Command python -ErrorAction Stop).Source
$serverPath = Join-Path $projectDirectory 'backend/server.py'
$logDirectory = Join-Path $projectDirectory '.local'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$env:MACHBAR_HOST = '127.0.0.1'
$env:MACHBAR_PORT = '8000'
$env:MACHBAR_DB = Join-Path $projectDirectory 'backend/machbar.db'
$process = Start-Process -FilePath $pythonPath -ArgumentList @('-u', ('"' + $serverPath + '"')) -WorkingDirectory $projectDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'server.log') -RedirectStandardError (Join-Path $logDirectory 'server-error.log')

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 300
    $process.Refresh()
    if ($process.HasExited) {
        throw "Der Server konnte nicht starten. Details: $logDirectory\server-error.log"
    }
    try {
        $health = Invoke-RestMethod "$serverUrl/api/health" -TimeoutSec 1
        if ($health.ok) {
            Write-Host "MACHBAR läuft im Hintergrund: $serverUrl/#/admin"
            Write-Host "Server-Prozess: $($process.Id)"
            exit 0
        }
    } catch {
        # Give Python a short moment to finish startup.
    }
}
throw "Der Server antwortet noch nicht. Details: $logDirectory\server-error.log"
