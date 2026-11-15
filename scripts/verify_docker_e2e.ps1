# Verification script for Block 1 Docker Compose End-to-End
Write-Output "=== 1. DOCKER COMPOSE PROCESS STATUS ==="
docker compose ps

Write-Output "`n=== 2. IMAGE SIZE INSPECTION ==="
docker images hotel-reservation-api:local --format "Repository: {{.Repository}} | Tag: {{.Tag}} | Size: {{.Size}}"

Write-Output "`n=== 3. HEALTH CHECK ==="
curl.exe -s -i http://localhost:8000/health

Write-Output "`n=== 4. CREATE ROOM (POST /rooms) ==="
$roomRes = '{"room_number": "302", "room_type": "Executive Penthouse", "price_per_night": 350}' | curl.exe -s -X POST http://localhost:8000/rooms -H "Content-Type: application/json" -d "@-"
Write-Output $roomRes
$roomObj = $roomRes | ConvertFrom-Json
$roomId = $roomObj.id

Write-Output "`n=== 5. CREATE RESERVATION (POST /reservations) ==="
$bookingJson = "{`"customer_name`": `"Commander Riker`", `"room_id`": $roomId, `"check_in`": `"2026-12-10`", `"check_out`": `"2026-12-15`"}"
$bookingRes = $bookingJson | curl.exe -s -X POST http://localhost:8000/reservations -H "Content-Type: application/json" -d "@-"
Write-Output $bookingRes
$bookingObj = $bookingRes | ConvertFrom-Json
$bookingRef = $bookingObj.booking_reference

Write-Output "`n=== 6. RETRIEVE RESERVATION (GET /reservations/$bookingRef) ==="
curl.exe -s -i "http://localhost:8000/reservations/$bookingRef"
