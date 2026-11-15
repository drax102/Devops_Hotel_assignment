# Troubleshooting Guide: Hotel Reservation Service

This guide provides practical diagnosis and remediation steps for operators diagnosing issues with the Hotel Reservation API and its supporting infrastructure.

---

## Quick Diagnostic Checklist

| Check | Command | Expected Healthy Output |
| :--- | :--- | :--- |
| **Container State** | `docker compose ps` | `hotel-app (healthy)`, `hotel-postgres (healthy)` |
| **Liveness Probe** | `curl.exe -i http://localhost:8000/health` | `HTTP/1.1 200 OK` |
| **Readiness Probe** | `curl.exe -i http://localhost:8000/ready` | `HTTP/1.1 200 OK` |
| **Structured Logs** | `docker compose logs --tail=50 app` | JSON lines with `"level": "INFO"` |
| **PostgreSQL Socket** | `docker compose exec db pg_isready -U hotel_user -d hotel_db` | `accepting connections` |

---

## Incident Diagnosis & Remediation

### 1. Database Outage / `/ready` Returns HTTP 503

#### Symptoms
- `/health` responds with `HTTP 200 OK` (web process is running).
- `/ready` responds with `HTTP 503 Service Unavailable` with payload `{"detail":"Database unreachable: ..."}`.
- Reservation and room endpoints return 500 or timeout.

#### Root Cause
The FastAPI application cannot communicate with the PostgreSQL instance via the internal network bridge `hotel_internal`.

#### Diagnosis
1. Inspect PostgreSQL container status:
   ```powershell
   docker compose ps db
   ```
2. Inspect recent database error logs:
   ```powershell
   docker compose logs --tail=100 db
   ```
3. Inspect JSON error logs from the API container:
   ```powershell
   docker compose logs --tail=50 app | Select-String "Database readiness check failed"
   ```
   Note the `request_id` and error message.

#### Remediation
- If the DB container is stopped or exited, start it:
  ```powershell
  docker compose start db
  ```
- Wait for the DB healthcheck to turn healthy (`docker compose ps db`).
- The application will automatically self-heal and reconnect on the next request.

---

### 2. Application Container Unhealthy or Crash-Looping

#### Symptoms
- `docker compose ps` indicates `hotel-app` is `unhealthy` or `restarting`.
- `curl http://localhost:8000/health` returns connection refused.

#### Diagnosis
1. Inspect the container startup log:
   ```powershell
   docker compose logs app
   ```
2. Common causes:
   - **Database not yet ready**: Ensure `depends_on: condition: service_healthy` is present in `docker-compose.yml`.
   - **Alembic migration failed**: An unhandled schema discrepancy or syntax error in a migration file prevented startup.
   - **Port conflict**: Another process is occupying the mapped port.

#### Remediation
- If migrations failed, inspect Alembic state:
  ```powershell
  docker compose run --rm app alembic current
  ```
- If port 8000 is occupied on the host, identify and resolve the conflicting process (see Section 3).

---

### 3. Port Conflicts on Host (8000 or 5432)

#### Symptoms
- `docker compose up` outputs:
  `Error response from daemon: driver failed programming external connectivity on endpoint ... bind: address already in use`

#### Diagnosis
Find the process occupying the port on Windows:
```powershell
# For application port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# For database port 5432
Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue | Select-Object OwningProcess
```

#### Remediation
1. Identify the process name using its PID:
   ```powershell
   Get-Process -Id <PID>
   ```
2. Terminate the rogue host process:
   ```powershell
   Stop-Process -Id <PID> -Force
   ```
3. Alternatively, adjust `APP_PORT` in `.env` to an open port (e.g., `8080`).

---

### 4. Concurrency Conflict (HTTP 409 Conflict)

#### Symptoms
- An API consumer receives `HTTP/1.1 409 Conflict` when submitting a reservation:
  ```json
  {"detail": "Room 101 is not available for the selected dates"}
  ```

#### Explanation
**This is NOT a bug.** This is expected behavior enforcing business logic. The PostgreSQL exclusion constraint `prevent_overlapping_reservations` enforces that no two confirmed reservations can overlap on the same room ID.

#### Verification
Verify the constraint is active in PostgreSQL:
```powershell
docker compose exec db psql -U hotel_user -d hotel_db -c "SELECT conname, contype FROM pg_constraint WHERE conname = 'prevent_overlapping_reservations';"
```
Expected output:
```
             conname             | contype 
---------------------------------+---------
 prevent_overlapping_reservations | x
(1 row)
```
Constraint type `x` denotes an exclusion constraint.

---

### 5. Database Backup or Restore Issues

#### Symptoms
- `scripts/restore.ps1` fails with errors about active connections or constraint violations.

#### Diagnosis
PostgreSQL prevents dropping or cleaning tables if active transactions hold exclusive locks.

#### Remediation
1. Terminate any orphaned connections before restoring:
   ```powershell
   docker compose exec db psql -U hotel_user -d hotel_db -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'hotel_db' AND pid <> pg_backend_pid();"
   ```
2. Re-run restore script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/restore.ps1
   ```

---

### 6. Tracing Requests with Correlation IDs

Every incoming HTTP request is assigned a unique UUID4 `X-Request-ID`. If an error occurs, search for the returned header in the application logs:

```powershell
# In PowerShell:
docker compose logs app | Select-String "<REQUEST_ID>"
```

The log entry will contain the full JSON event context, duration in milliseconds, and exception stack trace.
