# Operational Runbook: Hotel Reservation Service

This runbook provides step-by-step procedures for operators managing the Hotel Availability & Reservation platform.

---

## 1. Architecture & Component Topology

```
                       [ Host / Client / Browser ]
                                    │
               ┌────────────────────┴────────────────────┐
               │                                         │
       Port 80 (HTTP)                            Port 443 (HTTPS)
               │                                         │
               └────────────────────┬────────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │     hotel-nginx     │
                         │   (Nginx Alpine)    │
                         │ (TLS / Sec Headers) │
                         └──────────┬──────────┘
                                    │
                      Docker Bridge: hotel_internal
                      (DNS: app, Port: 8000)
                                    │
                         ┌──────────▼──────────┐
                         │      hotel-app      │
                         │  FastAPI (Uvicorn)  │
                         │  (appuser:10001)    │
                         └──────────┬──────────┘
                                    │
                      Docker Bridge: hotel_internal
                      (DNS: db, Port: 5432)
                                    │
                         ┌──────────▼──────────┐
                         │   hotel-postgres    │
                         │   PostgreSQL 17     │
                         │  (postgres_data)    │
                         └─────────────────────┘
```

- **Ingress Gateway**: `hotel-nginx` terminates TLS on port 443, issues 301 redirects for unencrypted port 80 HTTP requests, and sets defensive security headers.
- **Runtime User**: `hotel-app` runs strictly as non-root user `appuser:10001`.
- **Database Engine**: PostgreSQL 17 on Alpine Linux.
- **Data Persistence**: Named Docker volume `postgres_data`.
- **Internal Network**: Isolated bridge `hotel_internal`. Neither the database nor the application ports are exposed directly in production; ingress flows exclusively through Nginx.

---

## 2. Prerequisites

- **Docker Desktop** (WSL2 engine on Windows, or Docker Engine on Linux/macOS)
- **PowerShell 5.1+** (on Windows) or standard Bash shell
- **OpenSSL** (Git for Windows OpenSSL or containerized fallback)
- **curl.exe** or `curl` for HTTP/HTTPS probing

---

## 3. Starting the Service Stack

### Clean Startup
```powershell
# 1. Create environment configuration if not already present
Copy-Item .env.example .env

# 2. Generate local TLS certificate
powershell -ExecutionPolicy Bypass -File scripts/generate_certs.ps1

# 3. Start services in detached mode
docker compose up -d

# 4. Check container health status
docker compose ps
```

The database container automatically initializes. The FastAPI container awaits database readiness (`depends_on: condition: service_healthy`) and executes `alembic upgrade head` before starting the Uvicorn ASGI server. Nginx starts once FastAPI reports healthy.

---

## 4. Health & Readiness Verification

The service decouples process liveness from database readiness:

### Liveness Probe (`/health`)
Probes whether the application process and ASGI event loop are responsive.
```powershell
# Via Nginx HTTPS (default stack)
curl.exe -k -i https://localhost/health

# Direct to container (when started with docker-compose.dev.yml)
curl.exe -i http://localhost:8000/health
```
- **Expected Status**: `HTTP/1.1 200 OK`
- **Response**: `{"status":"healthy","service":"hotel-reservation-api"}`

### Readiness Probe (`/ready`)
Probes whether the application can successfully query the PostgreSQL database (`SELECT 1`). Configured with a 3-second fail-fast timeout.
```powershell
# Via Nginx HTTPS
curl.exe -k -i https://localhost/ready
```
- **Expected Status**: `HTTP/1.1 200 OK` (when DB is up) or `HTTP/1.1 503 Service Unavailable` (when DB is unreachable).
- **Response (Up)**: `{"status":"ready","database":"connected"}`

---

## 5. Structured Logging & Observability

All application logs are formatted as JSON lines conforming to ISO8601 UTC timestamps with embedded correlation IDs:

```json
{"timestamp": "2026-11-15T19:53:23.440Z", "level": "INFO", "logger": "hotel_api", "message": "GET /health completed in 1.25ms with status 200", "request_id": "24571a32-7207-4969-afe1-8ab2a2fccca5"}
```

### Viewing Logs
```powershell
# Stream live logs from application container
docker compose logs -f app

# Search logs for a specific Request ID
docker compose logs app | Select-String "24571a32-7207-4969-afe1-8ab2a2fccca5"
```

---

## 6. Database Seeding

The database seeder is idempotent. It ensures initial room inventory exists and safely skips records if already populated.

```powershell
# Execute seed inside the running application container
docker compose exec app python scripts/seed.py

# Alternatively, execute from host virtual environment (if port 5432 published)
.venv\Scripts\python.exe scripts/seed.py
```

---

## 7. TLS Certificate Management

### Generating or Rotating Certificates
```powershell
powershell -ExecutionPolicy Bypass -File scripts/generate_certs.ps1
docker compose restart nginx
```

### Verifying TLS & Nginx Ingress
An automated verification script tests port 80 redirect, TLS cipher negotiation, security headers, and HTTPS booking:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_nginx_https.ps1
```

---

## 8. Backup & Recovery Operations

### Taking a Database Backup
Backups are performed online using `pg_dump` with custom compressed archive format (`-Fc`), which preserves table constraints, triggers, and indices (including the GiST exclusion constraint).

```powershell
powershell -ExecutionPolicy Bypass -File scripts/backup.ps1
```
- Backups are stored in `backups/hotel_db_YYYYMMDD_HHMMSS.dump`.
- Returns exit code 0 on success.

### Restoring from Backup
Restores the database state using `pg_restore --clean --if-exists`.

```powershell
# Restore specific dump file
powershell -ExecutionPolicy Bypass -File scripts/restore.ps1 -DumpFile backups/hotel_db_20261115_195512.dump

# If -DumpFile is omitted, scripts/restore.ps1 automatically selects the latest dump
powershell -ExecutionPolicy Bypass -File scripts/restore.ps1
```

### End-to-End Backup & Recovery Drill
An automated drill script verifies backup integrity, table corruption recovery, and volume persistence:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_backup_restore.ps1
```

---

## 9. Release Deployment & Fast Rollback

Releases are containerized and version-tagged. Deployment and rollback do not require modifying code or configuration files.

### Deploying a New Release
```powershell
# Specify version and recreate application container
$env:APP_VERSION = "v1.0.0"
docker compose up -d app

# Verify container is running new image and healthy
docker compose ps app
curl.exe -k -i https://localhost/health
```

### Rollback Procedure
If a regression or fault is detected in a new release:
```powershell
# Revert APP_VERSION to the previous known good tag
$env:APP_VERSION = "v1.0.0"
docker compose up -d app

# Verify immediate recovery
curl.exe -k -i https://localhost/health
```
Rollback executes as a fast rollback with a brief interruption (container recreation takes ~2-3 seconds).

### Automated Rollback Drill
Run the verified rollback drill to validate fast rollback with a brief interruption:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/rollback_drill.ps1
```

---

## 10. Stopping and Teardown

```powershell
# Graceful stop (keeps containers and network intact)
docker compose stop

# Teardown containers and network (preserves database data volume)
docker compose down

# Complete wipe (DESTRUCTIVE: deletes database volume)
docker compose down -v
```
