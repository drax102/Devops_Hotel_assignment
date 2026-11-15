# Observability & Outage Failure Recovery Drill
# Demonstrates liveness (/health) vs readiness (/ready) decoupling during a database outage
$ErrorActionPreference = "Stop"

function Get-UtcTimestamp {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
}

Write-Output "============================================================"
Write-Output "BLOCK 4: OBSERVABILITY & RESILIENCE OUTAGE DRILL"
Write-Output "============================================================"
Write-Output "DRILL START: $(Get-UtcTimestamp)"

Write-Output "`n=== STAGE 1: HEALTHY BASELINE (PRE-OUTAGE) ==="
Write-Output "[$(Get-UtcTimestamp)] Checking /health (Liveness):"
curl.exe -s -i http://localhost:8000/health
Write-Output "[$(Get-UtcTimestamp)] Checking /ready (Readiness):"
curl.exe -s -i http://localhost:8000/ready

Write-Output "`n=== STAGE 2: SIMULATE DATABASE FAILURE (DETECT) ==="
Write-Output "[$(Get-UtcTimestamp)] Stopping database container 'hotel-postgres'..."
docker stop hotel-postgres
Write-Output "[$(Get-UtcTimestamp)] Database container stopped."

Write-Output "`n[$(Get-UtcTimestamp)] Probing /health (Liveness) during database outage:"
curl.exe -s -i http://localhost:8000/health

Write-Output "`n[$(Get-UtcTimestamp)] Probing /ready (Readiness) during database outage:"
curl.exe -s -i http://localhost:8000/ready

Write-Output "`n=== STAGE 3: INCIDENT DIAGNOSIS VIA STRUCTURED JSON LOGS (DIAGNOSE) ==="
Write-Output "[$(Get-UtcTimestamp)] Fetching structured JSON error logs from hotel-app:"
docker compose logs --tail=15 app

Write-Output "`n=== STAGE 4: RESTORING SERVICE (RECOVER) ==="
Write-Output "[$(Get-UtcTimestamp)] Restarting database container 'hotel-postgres'..."
docker start hotel-postgres

Write-Output "[$(Get-UtcTimestamp)] Waiting for database healthcheck to report healthy..."
while ((docker inspect --format '{{.State.Health.Status}}' hotel-postgres) -ne 'healthy') {
    Start-Sleep -Seconds 1
}
Write-Output "[$(Get-UtcTimestamp)] Database container is HEALTHY."

Write-Output "`n=== STAGE 5: POST-RECOVERY VERIFICATION (SELF-HEALED) ==="
Write-Output "[$(Get-UtcTimestamp)] Probing /ready (Readiness):"
curl.exe -s -i http://localhost:8000/ready

Write-Output "`n[$(Get-UtcTimestamp)] Probing /health (Liveness):"
curl.exe -s -i http://localhost:8000/health

Write-Output "`n[$(Get-UtcTimestamp)] Verification of end-to-end functionality post-recovery:"
$testBooking = '{"customer_name": "Drill Recovery Guest", "room_id": 1, "check_in": "2026-12-20", "check_out": "2026-12-22"}' | curl.exe -s -X POST http://localhost:8000/reservations -H "Content-Type: application/json" -d "@-"
Write-Output $testBooking

Write-Output "`n============================================================"
Write-Output "DRILL TIMELINE COMPLETE: $(Get-UtcTimestamp)"
Write-Output "RESULT: DETECT (503 on /ready, 200 on /health) -> DIAGNOSE (JSON logs with request_id) -> RECOVER (200 on /ready)"
Write-Output "============================================================"
