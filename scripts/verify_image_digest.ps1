# Verification Script for GHCR Pushed Image by Digest
Write-Output "============================================================"
Write-Output "GHCR CONTAINER IMAGE DIGEST & RUNTIME VERIFICATION"
Write-Output "============================================================"
Write-Output "Workflow Run URL: https://github.com/drax102/Devops_Hotel_assignment/actions/runs/43717288264"
Write-Output "Image Repository: ghcr.io/drax102/devops_hotel_assignment"
Write-Output "Image Tag: 1.0.0 (also tagged: 1.0, 1, latest, sha-012b738)"
Write-Output "Image Index Digest: sha256:9fc1f38d9fdd9beaf19a310253f2d9ff50c2277369791fe4acff293f6fe38f14"
Write-Output "Linux/AMD64 Manifest Digest: sha256:0040a3901bc53a6194d1561134bd5f4cd881efed3b9dacb8fd7a9fd70c28603c"

Write-Output "`n=== 1. BUILDX IMAGETOOLS INSPECT (REMOTE GHCR REGISTRY) ==="
docker buildx imagetools inspect ghcr.io/drax102/devops_hotel_assignment:1.0.0

Write-Output "`n=== 2. LOCAL DOCKER PULL BY DIGEST ==="
docker pull ghcr.io/drax102/devops_hotel_assignment@sha256:9fc1f38d9fdd9beaf19a310253f2d9ff50c2277369791fe4acff293f6fe38f14

Write-Output "`n=== 3. RUN LOCAL CONTAINER FROM PULLED DIGEST ==="
docker rm -f test-ghcr-digest 2>$null
docker run -d --name test-ghcr-digest --network assignment_hotel_hotel_internal -e POSTGRES_HOST=db -e POSTGRES_USER=hotel_user -e POSTGRES_PASSWORD=local_dev_password_123 -e POSTGRES_DB=hotel_db -p 8001:8000 ghcr.io/drax102/devops_hotel_assignment@sha256:9fc1f38d9fdd9beaf19a310253f2d9ff50c2277369791fe4acff293f6fe38f14

Start-Sleep -Seconds 5

Write-Output "`n=== 4. CONTAINER PROCESS & LOGS ==="
docker ps --filter "name=test-ghcr-digest"
docker logs --tail 15 test-ghcr-digest

Write-Output "`n=== 5. HEALTH CHECK AGAINST PULLED CONTAINER (PORT 8001) ==="
curl.exe -s -i http://localhost:8001/health

Write-Output "`n=== 6. CLEANUP TEST CONTAINER ==="
docker rm -f test-ghcr-digest
