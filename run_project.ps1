param(
    [switch]$Setup,
    [switch]$SkipMec,
    [switch]$WithMl
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $Root ".runtime"
$LogDir = Join-Path $RuntimeDir "logs"
New-Item -ItemType Directory -Force -Path $RuntimeDir, $LogDir | Out-Null

function Require-Command {
    param([string]$Name, [string]$InstallHint)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing command '$Name'. $InstallHint"
    }
}

function Start-LoggedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    [pscustomobject]@{
        name = $Name
        pid = $process.Id
        stdout = $stdout
        stderr = $stderr
    }
}

Require-Command "bun" "Install Bun from https://bun.sh or adjust backend/package.json scripts."
Require-Command "python" "Install Python 3.12+ and make sure it is on PATH."

if ($Setup) {
    Push-Location (Join-Path $Root "backend")
    try {
        if (Get-Command pnpm -ErrorAction SilentlyContinue) {
            pnpm install
        }
        bunx prisma generate
        bunx prisma db push
    }
    finally {
        Pop-Location
    }

    $UiVenvPython = Join-Path $Root "ui\.venv\Scripts\python.exe"
    if (-not (Test-Path $UiVenvPython)) {
        python -m venv (Join-Path $Root "ui\.venv")
    }
    & $UiVenvPython -m pip install -r (Join-Path $Root "ui\requirements.txt")
}

$processes = @()

$processes += Start-LoggedProcess `
    -Name "backend" `
    -FilePath "bun" `
    -ArgumentList @("src/index.ts") `
    -WorkingDirectory (Join-Path $Root "backend")

$UiPython = Join-Path $Root "ui\.venv\Scripts\python.exe"
if (-not (Test-Path $UiPython)) {
    $UiPython = "python"
}

$uiCommand = @"
`$env:API_BASE_URL='http://localhost:4000/api'
`$env:MEC_API_URL='http://localhost:8000'
`$env:MEC_REGION='local-demo'
`$env:MEC_NODE_NAME='MEC Local Docker'
`$env:MQTT_BROKER_HOST='localhost'
`$env:MQTT_BROKER_PORT='1883'
`$env:USE_MOCK_API='false'
`$env:USE_MOCK_ADMIN_ANALYTICS='false'
& '$UiPython' -m app.main
"@

$processes += Start-LoggedProcess `
    -Name "ui" `
    -FilePath "powershell" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $uiCommand) `
    -WorkingDirectory (Join-Path $Root "ui")

if (-not $SkipMec) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Push-Location (Join-Path $Root "mec")
        try {
            docker compose up --build -d
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Warning "Docker is not available; MEC containers were not started. Re-run with Docker installed or use -SkipMec."
    }
}

if ($WithMl) {
    if (Get-Command poetry -ErrorAction SilentlyContinue) {
        $processes += Start-LoggedProcess `
            -Name "ml-flower" `
            -FilePath "poetry" `
            -ArgumentList @("run", "flwr", "run", ".", "--stream") `
            -WorkingDirectory (Join-Path $Root "ml")
    }
    else {
        Write-Warning "Poetry is not available; ML Flower simulation was not started."
    }
}

$processes | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $RuntimeDir "pids.json")

Write-Host ""
Write-Host "PrivacyStressApp started."
Write-Host "Backend: http://localhost:4000/api/health"
Write-Host "UI:      http://localhost:8080"
if (-not $SkipMec) {
    Write-Host "MEC API: http://localhost:8000/status"
}
Write-Host "Logs:    $LogDir"
Write-Host "PIDs:    $(Join-Path $RuntimeDir 'pids.json')"
