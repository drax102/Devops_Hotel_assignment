# Script to generate a self-signed TLS certificate and private key for local HTTPS
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$certsDir = Join-Path $projectRoot "certs"

if (-not (Test-Path $certsDir)) {
    New-Item -ItemType Directory -Path $certsDir -Force | Out-Null
}

$crtPath = Join-Path $certsDir "selfsigned.crt"
$keyPath = Join-Path $certsDir "selfsigned.key"

# Locate OpenSSL executable
$opensslCmd = Get-Command openssl -ErrorAction SilentlyContinue
if ($opensslCmd) {
    $opensslExe = $opensslCmd.Source
} elseif (Test-Path "C:\Program Files\Git\usr\bin\openssl.exe") {
    $opensslExe = "C:\Program Files\Git\usr\bin\openssl.exe"
} else {
    Write-Output "[CERT] Host openssl not found, falling back to containerized openssl..."
    docker run --rm -v "${certsDir}:/certs" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/selfsigned.key -out /certs/selfsigned.crt -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
    Write-Output "[CERT SUCCESS] Certificate generated via container at $certsDir"
    exit 0
}

Write-Output "[CERT] Generating self-signed TLS certificate using $opensslExe..."
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $opensslExe req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $keyPath -out $crtPath -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>$null
$ErrorActionPreference = $prevEAP

if ((Test-Path $crtPath) -and (Test-Path $keyPath)) {
    Write-Output "[CERT SUCCESS] Self-signed certificate created:"
    Write-Output "  Certificate: $crtPath"
    Write-Output "  Private Key: $keyPath"
} else {
    Write-Error "[CERT ERROR] Failed to create certificate files."
}
