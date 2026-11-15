# Script to verify Nginx reverse proxy with TLS termination and security headers
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Output "============================================================"
Write-Output "BLOCK B / EVIDENCE 11: NGINX HTTPS REVERSE PROXY VERIFICATION"
Write-Output "============================================================"
Write-Output "Verification Date: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffZ')"
Write-Output ""

Write-Output "=== 1. DOCKER COMPOSE SERVICE STATUS ==="
docker compose ps
Write-Output ""

Write-Output "=== 2. TLS CERTIFICATE INSPECTION ==="
$crtPath = Join-Path $projectRoot "certs\selfsigned.crt"
if (Test-Path $crtPath) {
    $opensslExe = "openssl"
    if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
        if (Test-Path "C:\Program Files\Git\usr\bin\openssl.exe") {
            $opensslExe = "C:\Program Files\Git\usr\bin\openssl.exe"
        }
    }
    & $opensslExe x509 -in $crtPath -text -noout | Select-String -Pattern "Subject:", "Issuer:", "Not Before", "Not After", "DNS:", "IP Address:"
} else {
    Write-Output "Certificate file not found at $crtPath"
}
Write-Output ""

Write-Output "=== 3. HTTP (PORT 80) -> HTTPS (PORT 443) 301 REDIRECT ==="
curl.exe -s -i http://localhost/health
Write-Output ""

Write-Output "=== 4. HTTPS (PORT 443) /health LIVENESS & SECURITY HEADERS ==="
curl.exe -s -k -i https://localhost/health
Write-Output ""

Write-Output "=== 5. HTTPS (PORT 443) /ready READINESS PROBE ==="
curl.exe -s -k -i https://localhost/ready
Write-Output ""

Write-Output "=== 6. HTTPS (PORT 443) GET /rooms ==="
curl.exe -s -k -i https://localhost/rooms
Write-Output ""

Write-Output "=== 7. HTTPS (PORT 443) POST /reservations (BOOKING OVER TLS) ==="
$bookingPayload = '{"room_id":2,"customer_name":"Alice HTTPS Test","check_in":"2026-12-10","check_out":"2026-12-15"}'
$bookingPayload | curl.exe -s -k -i -X POST https://localhost/reservations -H "Content-Type: application/json" -d "@-"
Write-Output ""

Write-Output "=== 8. HTTPS (PORT 443) CONFLICT PROTECTION OVER TLS (EXPECT 409) ==="
$bookingPayload | curl.exe -s -k -i -X POST https://localhost/reservations -H "Content-Type: application/json" -d "@-"
Write-Output ""

Write-Output "=== NGINX HTTPS VERIFICATION COMPLETE ==="
