# Evidence Index: Hotel Reservation DevOps & Cloud Engineering

This document indexes all verification outputs, test runs, CI logs, and operational drills executed against the repository. Every referenced evidence artifact represents raw, unedited command output generated on the system.

---

## Acceptance Test Verification Map

| Step / Requirement | Evidence File | Command Executed | Status |
| :--- | :--- | :--- | :--- |
| **1. Baseline & Concurrency Protection** | [`evidence/04_pytest_full.txt`](file:///evidence/04_pytest_full.txt) | `pytest -v -s` (10 concurrent requests: 1x 201 Created, 9x 409 Conflict) | **VERIFIED** |
| **2. Clean-Clone Environment & Start** | [`evidence/13_clean_clone.txt`](file:///evidence/13_clean_clone.txt) | Clean clone into new folder, README steps, dynamic booking (201) & duplicate (409) | **VERIFIED** |
| **3. CI Pipeline Run** | [`evidence/06_ci_pipeline.txt`](file:///evidence/06_ci_pipeline.txt) | GitHub API extraction of runs `43716465249` (PR) & `43716727141` (main) | **VERIFIED** |
| **4. Versioned Image Produced** | [`evidence/07_image_digest.txt`](file:///evidence/07_image_digest.txt)<br>[`evidence/14_image_digest_v1.1.0.txt`](file:///evidence/14_image_digest_v1.1.0.txt) | Release tag `v1.0.0` (run `43717288264`) & `v1.1.0` (run `43757515988`), `imagetools inspect`, digest pull | **VERIFIED** |
| **5. Health Checks & JSON Logs** | [`evidence/08_observability_failure_drill.txt`](file:///evidence/08_observability_failure_drill.txt) | Decoupled `/health` & `/ready`, structured JSON logs with `x-request-id` | **VERIFIED** |
| **6. Failure Detection & Recovery** | [`evidence/08_observability_failure_drill.txt`](file:///evidence/08_observability_failure_drill.txt) | DB stopped: `/ready` returns 503, error logged. DB started: self-heals to 200 | **VERIFIED** |
| **7. Backup, Restore & Rollback** | [`evidence/09_backup_restore.txt`](file:///evidence/09_backup_restore.txt)<br>[`evidence/10_rollback_drill.txt`](file:///evidence/10_rollback_drill.txt) | `backup.ps1` (-Fc), table truncate, `restore.ps1`, volume persistence.<br>Fast rollback with a brief interruption from buggy v1.0.1 to v1.0.0 | **VERIFIED** |
| **Ingress & TLS Verification** | [`evidence/11_nginx_https.txt`](file:///evidence/11_nginx_https.txt) | Port 80->443 redirect, TLS termination, security headers, HTTPS booking & 409 | **VERIFIED** |
| **Port Isolation Verification** | [`evidence/12_port_isolation.txt`](file:///evidence/12_port_isolation.txt) | Default stack publishes only 80 and 443; ports 8000 and 5432 closed to host | **VERIFIED** |
| **Public Ingress / Demo** | [`evidence/15_public_tunnel.txt`](file:///evidence/15_public_tunnel.txt) | Temporary public demo URL served through Cloudflare quick tunnel (`/health` & `/ready` 200 OK) | **VERIFIED** |

---

## Important Scope Note on Releases & Rollback
GHCR image `v1.0.0` was built from commit `012b738` (before `/ready`, JSON logging, and Nginx were introduced); the rollback drill used locally built tags (`hotel-reservation-api:v1.0.0` and `v1.0.1`). Release `v1.1.0` (commit `ffc4ffd7d5b6222a0d0b6bfd80dc1561f4546f5a`) contains the application updates (`/ready` and JSON logging). Nginx is not part of the application image; it runs as a separate service container using stock `nginx:alpine` with a mounted configuration.
A TEMPORARY public demo URL was served through a Cloudflare quick tunnel from my laptop (see evidence/15). Public URL is temporary and has no authentication; no permanent hosting.

---

## Detailed Evidence Summaries

### 1. `evidence/01_baseline_audit.txt`
- Baseline system and runtime environment audit (Python 3.13.5, Windows 11, pinned packages).
- Verifies `.env` is absent from git tracking and clean git working tree.

### 2. `evidence/02_alembic_migration.txt`
- Output of `alembic upgrade head` applying revision `6944177ec459`.
- Direct query from PostgreSQL `pg_constraint` confirming `prevent_overlapping_reservations` constraint type `x` (exclusion) using `btree_gist` and `daterange(check_in, check_out, '[)') WITH && WHERE (status = 'confirmed')`.

### 3. `evidence/03_seed_verification.txt`
- Output of running `python scripts/seed.py` consecutively twice.
- First run creates rooms 101, 102, 201, 202 and booking BK001.
- Second run detects existing records, skips them gracefully, and completes with zero duplicate key errors.

### 4. `evidence/04_pytest_full.txt`
- Full test run against isolated `hotel_test_db`.
- Verified health, rooms, reservations, availability, boundary edge cases, and 10 concurrent requests resulting in exactly one HTTP 201 Created and nine HTTP 409 Conflict responses.

### 5. `evidence/05_docker_build_compose.txt`
- Docker build producing a lean 322MB image running as non-root `appuser:10001`.
- Clean Compose startup on bridge network `hotel_internal`.
- Live container health check verification (`/health` returning 200 OK).

### 6. `evidence/06_ci_pipeline.txt`
- Live GitHub Actions API logs extracted via `scripts/save_ci_evidence.py`.
- Run `43716465249` (PR `feat/ci-pipeline`) and Run `43716727141` (`main`) executing `ruff`, `black --check`, PostgreSQL 17 service container migrations, `pytest`, and container build.

### 7. `evidence/07_image_digest.txt`
- Release tag `v1.0.0` triggering GitHub Actions workflow run `43717288264`.
- Remote GHCR registry inspection via `docker buildx imagetools inspect ghcr.io/drax102/devops_hotel_assignment:1.0.0`.
- Verified OCI Image Index Digest: `sha256:9fc1f38d9fdd9beaf19a310253f2d9ff50c2277369791fe4acff293f6fe38f14`.
- Verified Linux AMD64 Manifest Digest: `sha256:0040a3901bc53a6194d1561134bd5f4cd881efed3b9dacb8fd7a9fd70c28603c`.
- Pull by digest locally and execution test verifying 200 OK response on port 8001.

### 8. `evidence/08_observability_failure_drill.txt`
- Outage simulation executed by `scripts/failure_drill.ps1`.
- Baseline healthy state: `/health` (liveness) 200 OK, `/ready` (readiness) 200 OK.
- Database stopped: `/health` continues returning 200 OK (web process alive), `/ready` fails fast within 3s returning 503 Service Unavailable.
- JSON-formatted structured error logs captured showing ISO8601 timestamps and correlated `x-request-id`.
- Database restarted: `/ready` automatically recovers to 200 OK; subsequent reservation creation succeeds.

### 9. `evidence/09_backup_restore.txt`
- Database backup and recovery verification executed by `scripts/demo_backup_restore.ps1`.
- Pre-backup state: 5 rooms, 2 reservations.
- `scripts/backup.ps1` generates timestamped custom PostgreSQL binary dump (`backups/hotel_db_YYYYMMDD_HHMMSS.dump`).
- Corruption simulation: `TRUNCATE TABLE reservations, rooms RESTART IDENTITY CASCADE` leaves 0 rooms, 0 reservations.
- `scripts/restore.ps1` executes `pg_restore --clean --if-exists`, restoring all 5 rooms, 2 reservations, and the GiST exclusion constraint.
- Volume persistence drill: `docker rm -f hotel-postgres` and container recreation confirms named volume `postgres_data` persists data across container lifecycles.

### 10. `evidence/10_rollback_drill.txt`
- Release deployment and rollback verification executed by `scripts/rollback_drill.ps1`.
- Stable `hotel-reservation-api:v1.0.0` deployed via `APP_VERSION=v1.0.0` returning 200 OK.
- Buggy `hotel-reservation-api:v1.0.1` with simulated HTTP 500 regression deployed; health check fails with HTTP 500.
- Fast rollback with a brief interruption executed via `APP_VERSION=v1.0.0 docker compose up -d app`.
- Verified immediate recovery to HTTP 200 OK; source code clean and untouched.

### 11. `evidence/11_nginx_https.txt`
- Nginx TLS termination and reverse proxy verification executed by `scripts/verify_nginx_https.ps1`.
- Verifies `hotel-nginx`, `hotel-app`, and `hotel-postgres` container states.
- Inspects x509 certificate for CN=localhost with SANs `DNS:localhost, IP:127.0.0.1`.
- Verifies HTTP port 80 returns `301 Moved Permanently` redirecting to `https://localhost/health`.
- Verifies HTTPS port 443 returns `200 OK` on `/health` and `/ready` with security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Referrer-Policy`).
- Verifies successful room booking over HTTPS (`201 Created`) and subsequent double-booking rejection (`409 Conflict`).

### 12. `evidence/12_port_isolation.txt`
- Verification of port isolation executed by `scripts/verify_port_isolation.ps1`.
- Confirms `docker compose config | Select-String "published"` yields only port 80 and port 443.
- Confirms `curl.exe -k https://localhost/health` succeeds with `200 OK`.
- Confirms direct access to container port `http://localhost:8000/health` fails with connection refused (Exit Code 7).
- Confirms direct access to PostgreSQL port `127.0.0.1:5432` fails with connection closed (`TcpTestSucceeded: False`).

### 13. `evidence/13_clean_clone.txt`
- Clean-clone environment and startup verification executed by `scripts/verify_clean_clone.ps1`.
- Cloned repository into fresh isolated directory (`D:\temp_clean_clone_verify`).
- Followed ONLY the documented README commands: `.env.example` -> `.env`, `generate_certs.ps1`, `docker compose up -d`.
- Verified `/health` and `/ready` return 200 OK over HTTPS.
- Executed `scripts/seed.py` successfully.
- Submitted HTTPS reservation using dynamic dates relative to today (`Check-in: today+20 days, Check-out: today+25 days`), returning `201 Created` with booking reference `BK-91C086B5`.
- Submitted conflicting reservation for identical room and dates, returning `409 Conflict` (`Room is already booked for the requested dates`).
- Verified complete teardown and clean restart of the primary stack.

### 14. `evidence/14_image_digest_v1.1.0.txt`
- Release tag `v1.1.0` triggering GitHub Actions workflow run `43757515988`.
- Remote GHCR registry inspection via `docker buildx imagetools inspect ghcr.io/drax102/devops_hotel_assignment:1.1.0`.
- Verified OCI Image Index Digest: `sha256:c04f01272af8741827b6e4d13109ac9dc0f52db2e5d86d6807f072ac5354bac8`.
- Verified Linux AMD64 Manifest Digest: `sha256:da8cdab147170c264d06a41e1cd5cb0119af66c5b400207a3965c0f25193ddfc`.
- Pull by tag `1.1.0` locally and runtime execution test verifying 200 OK response on port 8003.

### 15. `evidence/15_public_tunnel.txt`
- A TEMPORARY public demo URL was served through a Cloudflare quick tunnel from my laptop (see evidence/15).
- Verifies public HTTP/1.1 200 OK responses for both `/health` and `/ready` with Cloudflare headers and edge security headers (`x-content-type-options`, `x-frame-options`, `x-request-id`, `x-xss-protection`).
- Tunnel hostname replaced with `<tunnel-url>` because the tunnel URL is temporary and dies when stopped.
