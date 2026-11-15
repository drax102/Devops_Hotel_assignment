# Script to inspect and verify v1.1.0 GHCR image
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$evidenceFile = Join-Path $projectRoot "evidence\13_image_digest_v1.1.0.txt"

$output = @()
$output += "============================================================"
$output += "GHCR CONTAINER IMAGE DIGEST & RUNTIME VERIFICATION (v1.1.0)"
$output += "============================================================"
$output += "Workflow Run URL: https://github.com/drax102/Devops_Hotel_assignment/actions/runs/43757515988"
$output += "Workflow Run ID: 43757515988"
$output += "Release Tag: v1.1.0 (Image Tag: 1.1.0)"
$output += "Target Repository: ghcr.io/drax102/devops_hotel_assignment"
$output += ""
$output += "=== 1. BUILDX IMAGETOOLS INSPECT (REMOTE GHCR REGISTRY) ==="
$inspect = docker buildx imagetools inspect ghcr.io/drax102/devops_hotel_assignment:1.1.0
$output += $inspect
$output += ""
$output += "=== 2. LOCAL DOCKER PULL BY TAG 1.1.0 ==="
$pull = docker pull ghcr.io/drax102/devops_hotel_assignment:1.1.0
$output += $pull
$output += ""
$output += "=== 3. RUNTIME VERIFICATION OF PULLED v1.1.0 IMAGE ==="
$cid = docker run -d --name test-v110-probe -p 8003:8000 -e POSTGRES_HOST=127.0.0.1 ghcr.io/drax102/devops_hotel_assignment:1.1.0 sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3
$probe = curl.exe -s -i http://localhost:8003/health
$output += "Launched container test-v110-probe ($cid)"
$output += "Probing http://localhost:8003/health:"
$output += $probe
docker rm -f test-v110-probe | Out-Null
$output += "Container cleaned up."
$output += ""
$output += "=== v1.1.0 VERIFICATION COMPLETE ==="

[System.IO.File]::WriteAllLines($evidenceFile, $output, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "Evidence saved to $evidenceFile"
