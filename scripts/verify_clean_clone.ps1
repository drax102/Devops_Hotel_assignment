# Script to execute clean-clone verification drill
# Tests clean clone, documented startup steps, dynamic relative-date booking, and 409 conflict
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$cloneDir = "D:\temp_clean_clone_verify"
$evidenceFile = Join-Path $projectRoot "evidence\13_clean_clone.txt"

Write-Output "============================================================"
Write-Output "ACCEPTANCE TEST 2: CLEAN-CLONE ENVIRONMENT & BOOKING DRILL"
Write-Output "============================================================"
Write-Output "Execution Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffZ')"
Write-Output ""

# 1. Stop main stack to free ports
Write-Output "=== 1. STOPPING MAIN STACK ==="
Set-Location $projectRoot
docker compose down

# 2. Prepare clean directory
Write-Output "=== 2. PREPARING ISOLATED CLONE DIRECTORY ==="
if (Test-Path $cloneDir) {
    Remove-Item -Recurse -Force $cloneDir -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $cloneDir -Force | Out-Null
Set-Location $cloneDir

# 3. Clone fresh repository
Write-Output "=== 3. GIT CLONE FROM REMOTE REPOSITORY ==="
git clone https://github.com/drax102/Devops_Hotel_assignment.git .
Write-Output ""

# 4. Follow ONLY documented README steps
Write-Output "=== 4. EXECUTING DOCUMENTED SETUP STEPS ==="
Write-Output "Step 4.1: Copy .env.example to .env"
Copy-Item .env.example .env

Write-Output "Step 4.2: Generate local TLS certificates"
powershell -ExecutionPolicy Bypass -File scripts/generate_certs.ps1

Write-Output "Step 4.3: Start service stack with Docker Compose"
docker compose up -d

Write-Output "Waiting for containers to report healthy..."
$retries = 30
$healthy = $false
while ($retries -gt 0) {
    Start-Sleep -Seconds 2
    $appStatus = docker inspect --format='{{json .State.Health.Status}}' hotel-app 2>$null
    if ($appStatus -eq '"healthy"') {
        $healthy = $true
        break
    }
    $retries--
}
Write-Output "App container health status: $appStatus"
Write-Output ""

Write-Output "=== 5. VERIFYING SERVICE STATUS ==="
docker compose ps
Write-Output ""

Write-Output "=== 6. PROBING HEALTH & READINESS ENDPOINTS OVER HTTPS ==="
Write-Output "Testing /health (Liveness):"
curl.exe -s -k -i https://localhost/health
Write-Output ""
Write-Output "Testing /ready (Readiness):"
curl.exe -s -k -i https://localhost/ready
Write-Output ""

Write-Output "=== 7. SEEDING DATABASE ==="
docker compose exec app python scripts/seed.py
Write-Output ""

Write-Output "=== 8. EXECUTING HTTPS BOOKING WITH DYNAMIC RELATIVE DATES ==="
# Using days +20 to +25 to avoid collision with seed booking BK001 (days +10 to +15)
$checkIn = (Get-Date).AddDays(20).ToString("yyyy-MM-dd")
$checkOut = (Get-Date).AddDays(25).ToString("yyyy-MM-dd")
Write-Output "Selected Dates: Check-in=$checkIn, Check-out=$checkOut"

$bookingBody = @"
{"room_id":1,"customer_name":"Clean Clone Guest","check_in":"$checkIn","check_out":"$checkOut"}
"@
Write-Output "Submitting initial reservation (Expect HTTP 201 Created):"
$bookingBody | curl.exe -s -k -i -X POST https://localhost/reservations -H "Content-Type: application/json" -d "@-"
Write-Output ""

Write-Output "=== 9. SUBMITTING CONFLICTING RESERVATION OVER HTTPS ==="
Write-Output "Submitting identical dates on Room 1 (Expect HTTP 409 Conflict):"
$bookingBody | curl.exe -s -k -i -X POST https://localhost/reservations -H "Content-Type: application/json" -d "@-"
Write-Output ""

# 10. Clean up clone directory
Write-Output "=== 10. TEARING DOWN CLEAN-CLONE STACK ==="
docker compose down -v
Set-Location $projectRoot
Remove-Item -Recurse -Force $cloneDir -ErrorAction SilentlyContinue

# 11. Restart main stack
Write-Output "=== 11. RESTARTING MAIN ASSIGNMENT STACK ==="
docker compose up -d
$retries = 30
while ($retries -gt 0) {
    Start-Sleep -Seconds 2
    $appStatus = docker inspect --format='{{json .State.Health.Status}}' hotel-app 2>$null
    if ($appStatus -eq '"healthy"') {
        break
    }
    $retries--
}
docker compose up -d nginx

Write-Output "=== CLEAN-CLONE DRILL COMPLETE ==="
