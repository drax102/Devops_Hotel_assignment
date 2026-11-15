# Troubleshooting Guide: Hotel Reservation Service

This guide provides practical diagnosis and remediation steps for operators diagnosing issues with the Hotel Reservation API and its supporting infrastructure.

---

## Quick Diagnostic Checklist

| Check | Command | Expected Healthy Output |
| :--- | :--- | :--- |
| **Container State** | `docker compose ps` | `hotel-nginx (Up)`, `hotel-app (healthy)`, `hotel-postgres (healthy)` |
| **Liveness Probe (HTTPS)** | `curl.exe -k -i https://localhost/health` | `HTTP/1.1 200 OK` |
| **Readiness Probe (HTTPS)** | `curl.exe -k -i https://localhost/ready` | `HTTP/1.1 200 OK` |
| **HTTP Redirect (Port 80)** | `curl.exe -i http://localhost/health` | `HTTP/1.1 301 Moved Permanently` |
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

### 2. Nginx Ingress or TLS Errors

#### Symptoms
- `curl.exe -k https://localhost/health` returns `curl: (35) schannel: ...` or connection refused.
- `docker compose ps` shows `hotel-nginx` in state `restarting` or exited.

#### Diagnosis
1. Inspect Nginx error logs:
   ```powershell
   docker compose logs nginx
   ```
2. Check if TLS certificates exist on host:
   ```powershell
   Test-Path certs\selfsigned.crt, certs\selfsigned.key
   ```
   If `$false`, the Nginx container cannot find the mounted certificates.

#### Remediation
1. Generate the certificate files:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/generate_certs.ps1
   ```
2. Restart the Nginx container:
   ```powershell
   docker compose restart nginx
   ```
3. If ports 80 or 443 are in use on host by another web server (IIS, Apache), terminate or rebind the conflicting service.

---

### 3. Application Container Unhealthy or Crash-Looping

#### Symptoms
- `docker compose ps` indicates `hotel-app` is `unhealthy` or `restarting`.
- Nginx returns `502 Bad Gateway`.

#### Diagnosis
1. Inspect the container startup log:
   ```powershell
   docker compose logs app
   ```
2. Common causes:
   - **Database not yet ready**: Ensure `depends_on: condition: service_healthy` is present in `docker-compose.yml`.
   - **Alembic migration failed**: An unhandled schema discrepancy or syntax error in a migration file prevented startup.

#### Remediation
- If migrations failed, inspect Alembic state:
  ```powershell
  docker compose run --rm app alembic current
  ```
- Re-run migrations manually if necessary:
  ```powershell
  docker compose exec app alembic upgrade head
  ```

---

### 4. Concurrency Conflict (HTTP 409 Conflict)

#### Symptoms
- An API consumer receives `HTTP/1.1 409 Conflict` when submitting a reservation:
  ```json
  {"detail": "Room is already booked for the requested dates"}
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
docker compose logs app | Select-String "<REQUEST_ID>"
```

The log entry will contain the full JSON event context, duration in milliseconds, and exception stack trace.
