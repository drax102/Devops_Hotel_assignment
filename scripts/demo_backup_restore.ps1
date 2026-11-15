# Comprehensive Demonstration Script for Block 3: Backup & Restore + Volume Persistence
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Output "============================================================"
Write-Output "BLOCK 3: DATABASE BACKUP, RESTORE & PERSISTENCE VERIFICATION"
Write-Output "============================================================"

# Ensure stack is running
docker compose up -d db app
Start-Sleep -Seconds 3

# Seed baseline data
Write-Output "`n=== 1. ENSURE BASELINE DATA (SEED SCRIPT) ==="
.venv\Scripts\python.exe scripts/seed.py

# Query pre-backup counts and constraint
Write-Output "`n=== 2. PRE-BACKUP DATABASE AUDIT ==="
Write-Output "Rooms count:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM rooms;"
Write-Output "Reservations count:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM reservations;"
Write-Output "Exclusion constraint check:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -c "SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'prevent_overlapping_reservations';"

# Run backup script
Write-Output "`n=== 3. RUNNING BACKUP SCRIPT (scripts/backup.ps1) ==="
powershell -ExecutionPolicy Bypass -File scripts/backup.ps1

$backupFile = (Get-ChildItem -Path (Join-Path $projectRoot "backups") -Filter "*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
Write-Output "Selected backup file for restoration: $backupFile"

# Simulate data loss / corruption
Write-Output "`n=== 4. SIMULATING CATASTROPHIC DATA LOSS (TRUNCATE TABLES) ==="
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -c "TRUNCATE TABLE reservations, rooms RESTART IDENTITY CASCADE;"

Write-Output "`n=== 5. POST-DELETION AUDIT (PROVING DATA IS GONE) ==="
Write-Output "Rooms count (should be 0):"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM rooms;"
Write-Output "Reservations count (should be 0):"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM reservations;"

# Run restore script
Write-Output "`n=== 6. RUNNING RESTORE SCRIPT (scripts/restore.ps1) ==="
powershell -ExecutionPolicy Bypass -File scripts/restore.ps1 -BackupFile $backupFile

# Post-restore verification
Write-Output "`n=== 7. POST-RESTORE VERIFICATION (DATA & CONSTRAINT INTEGRITY) ==="
Write-Output "Rooms count (restored):"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM rooms;"
Write-Output "Reservations count (restored):"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM reservations;"
Write-Output "Exclusion constraint verification:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -c "SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'prevent_overlapping_reservations';"

# Demonstrate volume persistence
Write-Output "`n=== 8. VOLUME PERSISTENCE DEMONSTRATION ==="
Write-Output "Removing hotel-postgres container without deleting volume..."
docker rm -f hotel-postgres
Write-Output "Recreating database container using existing volume..."
docker compose up -d db

Write-Output "Waiting for database healthcheck..."
while ((docker inspect --format '{{.State.Health.Status}}' hotel-postgres) -ne 'healthy') {
    Start-Sleep -Seconds 1
}

Write-Output "Querying data from newly recreated database container:"
Write-Output "Rooms count from new container:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM rooms;"
Write-Output "Reservations count from new container:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -t -c "SELECT count(*) FROM reservations;"
Write-Output "Exclusion constraint on new container:"
docker exec -i hotel-postgres psql -U hotel_user -d hotel_db -c "SELECT conname, contype FROM pg_constraint WHERE conname = 'prevent_overlapping_reservations';"

Write-Output "`n============================================================"
Write-Output "BACKUP, RESTORE & PERSISTENCE VERIFICATION COMPLETED"
Write-Output "============================================================"
