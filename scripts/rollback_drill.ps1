# Automated Release and Rollback Drill Script
# Demonstrates versioned image deployment, regression detection, and fast rollback
$ErrorActionPreference = "Stop"

function Get-UtcTimestamp {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
}

function Wait-For-HttpResponse {
    param([string]$Url, [int]$TimeoutSeconds = 15)
    $startTime = [System.Diagnostics.Stopwatch]::StartNew()
    while ($startTime.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $output = curl.exe -s -k -i $Url
        if ($output -and ($output | Select-String -Pattern "HTTP/1\.[01]")) {
            return ($output -join "`n")
        }
        Start-Sleep -Milliseconds 500
    }
    return (curl.exe -s -k -i $Url -join "`n")
}

Write-Output "============================================================"
Write-Output "BLOCK 5: VERSIONED RELEASE & FAST ROLLBACK DRILL"
Write-Output "============================================================"

# Stage 1: Build & Deploy Stable Baseline v1.0.0
Write-Output "`n=== STAGE 1: ESTABLISH STABLE v1.0.0 RELEASE ==="
Write-Output "[$(Get-UtcTimestamp)] Tagging current image as hotel-reservation-api:v1.0.0..."
docker tag hotel-reservation-api:local hotel-reservation-api:v1.0.0

$env:APP_VERSION = "v1.0.0"
Write-Output "[$(Get-UtcTimestamp)] Deploying stable v1.0.0 via Compose (APP_VERSION=v1.0.0)..."
docker compose up -d app | Out-Null

$v100Res = Wait-For-HttpResponse "https://localhost/health"
Write-Output "[$(Get-UtcTimestamp)] Probing stable v1.0.0 /health:"
Write-Output $v100Res

# Stage 2: Introduce Deliberate Bug & Build v1.0.1
Write-Output "`n=== STAGE 2: BUILD BUGGY RELEASE v1.0.1 ==="
$mainPyPath = "app/main.py"
$originalContent = [System.IO.File]::ReadAllText((Resolve-Path $mainPyPath).Path)

$healthyTarget = 'return {"status": "healthy", "service": "hotel-reservation-api"}'
$buggyCode = 'raise HTTPException(status_code=500, detail="CRITICAL REGRESSION: deliberate bug in v1.0.1")'

if (-not $originalContent.Contains($healthyTarget)) {
    Write-Error "Could not find target string in app/main.py to inject bug"
}

$buggyContent = $originalContent.Replace($healthyTarget, $buggyCode)
[System.IO.File]::WriteAllText((Resolve-Path $mainPyPath).Path, $buggyContent)
Write-Output "[$(Get-UtcTimestamp)] Deliberate HTTP 500 regression injected into app/main.py."

Write-Output "[$(Get-UtcTimestamp)] Building buggy image hotel-reservation-api:v1.0.1..."
docker build -t hotel-reservation-api:v1.0.1 . | Out-Null
Write-Output "[$(Get-UtcTimestamp)] Image hotel-reservation-api:v1.0.1 built successfully."

# Stage 3: Deploy v1.0.1 & Detect Regression
Write-Output "`n=== STAGE 3: DEPLOY v1.0.1 & DETECT REGRESSION ==="
$env:APP_VERSION = "v1.0.1"
Write-Output "[$(Get-UtcTimestamp)] Deploying buggy v1.0.1 via Compose (APP_VERSION=v1.0.1)..."
docker compose up -d app | Out-Null

$buggyRes = Wait-For-HttpResponse "https://localhost/health"
Write-Output "[$(Get-UtcTimestamp)] Probing v1.0.1 /health (DETECTING CRITICAL OUTAGE):"
Write-Output $buggyRes

# Stage 4: Execute Fast Rollback to v1.0.0
Write-Output "`n=== STAGE 4: EXECUTE FAST ROLLBACK TO v1.0.0 ==="
Write-Output "[$(Get-UtcTimestamp)] Rolling back Compose to stable image tag (APP_VERSION=v1.0.0)..."
$env:APP_VERSION = "v1.0.0"
docker compose up -d app | Out-Null

$rollbackRes = Wait-For-HttpResponse "https://localhost/health"
Write-Output "[$(Get-UtcTimestamp)] Probing /health post-rollback (VERIFYING RECOVERY):"
Write-Output $rollbackRes

# Stage 5: Clean Up Source Code (Never leave deliberate bug in repo)
Write-Output "`n=== STAGE 5: SOURCE CODE HYGIENE (REVERTING DELIBERATE BUG) ==="
[System.IO.File]::WriteAllText((Resolve-Path $mainPyPath).Path, $originalContent)
git checkout -- app/main.py
$env:APP_VERSION = "local"
docker compose up -d app | Out-Null

Write-Output "[$(Get-UtcTimestamp)] Git status on app/main.py:"
git status --short app/main.py

Write-Output "`n============================================================"
Write-Output "ROLLBACK DRILL COMPLETED SUCCESSFULLY"
Write-Output "RELEASE & ROLLBACK COMMANDS DOCUMENTED:"
Write-Output "  Deploy new release: `$env:APP_VERSION='vX.Y.Z'; docker compose up -d app"
Write-Output "  Fast rollback     : `$env:APP_VERSION='vPREV' ; docker compose up -d app"
Write-Output "============================================================"
