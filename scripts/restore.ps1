# Automated PostgreSQL Restore Script
# Restores a custom-format dump using pg_restore via Docker
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BackupFile,
    [string]$ContainerName = "hotel-postgres",
    [string]$DbUser = "hotel_user",
    [string]$DbName = "hotel_db"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Error "[RESTORE ERROR] Specified backup file does not exist: $BackupFile"
    exit 1
}

$resolvedFile = (Resolve-Path $BackupFile).Path
$containerTempPath = "/tmp/restore_target.dump"

Write-Output "[RESTORE] Transferring backup to '$ContainerName'..."
docker cp $resolvedFile "${ContainerName}:${containerTempPath}"

Write-Output "[RESTORE] Executing pg_restore with --clean --if-exists..."
# Note: pg_restore exits with code 0 or 1 on minor clean warnings (e.g. object not found to drop)
docker exec $ContainerName pg_restore -U $DbUser -d $DbName --clean --if-exists $containerTempPath
docker exec $ContainerName rm -f $containerTempPath

Write-Output "[RESTORE SUCCESS] Database '$DbName' successfully restored from '$BackupFile'."
