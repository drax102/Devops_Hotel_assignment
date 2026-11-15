# Automated PostgreSQL Backup Script
# Creates a binary custom-format dump (-Fc) using pg_dump via Docker
param(
    [string]$ContainerName = "hotel-postgres",
    [string]$DbUser = "hotel_user",
    [string]$DbName = "hotel_db",
    [string]$BackupDir = "backups"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $projectRoot $BackupDir

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$fileName = "hotel_db_backup_$timestamp.dump"
$backupFilePath = Join-Path $targetDir $fileName
$containerTempPath = "/tmp/$fileName"

Write-Output "[BACKUP] Starting backup for database '$DbName' in container '$ContainerName'..."
docker exec $ContainerName pg_dump -U $DbUser -d $DbName -Fc -f $containerTempPath
docker cp "${ContainerName}:${containerTempPath}" $backupFilePath
docker exec $ContainerName rm -f $containerTempPath

if (Test-Path $backupFilePath) {
    $size = (Get-Item $backupFilePath).Length
    Write-Output "[BACKUP SUCCESS] Backup file created: $backupFilePath ($size bytes)"
} else {
    Write-Error "[BACKUP FAILED] Backup file could not be verified."
}
