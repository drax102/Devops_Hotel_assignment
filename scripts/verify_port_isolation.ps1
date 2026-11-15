# Script to verify port isolation (only ports 80 and 443 published to host)
$ErrorActionPreference = "Continue"

Write-Output "============================================================"
Write-Output "EVIDENCE 12: PORT ISOLATION VERIFICATION"
Write-Output "============================================================"
Write-Output "Verification Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffZ')"
Write-Output ""

Write-Output "=== 1. DOCKER COMPOSE CONFIG PUBLISHED PORTS ==="
docker compose config | Select-String "published"
Write-Output ""

Write-Output "=== 2. PROBING HTTPS PORT 443 (EXPECT 200 OK) ==="
curl.exe -s -k -i https://localhost/health
Write-Output ""

Write-Output "=== 3. PROBING DIRECT APP PORT 8000 (EXPECT CONNECTION REFUSED / FAIL) ==="
$out8000 = curl.exe -s -i --max-time 3 http://localhost:8000/health 2>&1
$exitCode = $LASTEXITCODE
if ($out8000) {
    Write-Output "Output: $out8000"
}
Write-Output "Exit Code: $exitCode (non-zero indicates connection failure as expected)"
Write-Output ""

Write-Output "=== 4. PROBING DIRECT POSTGRES PORT 5432 (EXPECT CONNECTION REFUSED / CLOSED) ==="
$pgPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue
Write-Output "Port 5432 TcpTestSucceeded: $($pgPortCheck.TcpTestSucceeded) (False = properly isolated)"
Write-Output ""

Write-Output "=== PORT ISOLATION VERIFICATION COMPLETE ==="
