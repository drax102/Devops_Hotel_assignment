# Evidence Index: Hotel Reservation DevOps & Cloud Engineering

This document indexes all verification outputs, test runs, CI logs, and operational drills executed against the repository. Every referenced evidence artifact represents raw, unedited command output generated on the system.

---

## Acceptance Test & Rubric Verification Map

| Step / Requirement | Evidence File | Command Executed | Status |
| :--- | :--- | :--- | :--- |
| **1. Baseline & Hygiene** | [`evidence/01_baseline_audit.txt`](file:///evidence/01_baseline_audit.txt) | Environment audit, Python 3.13.5, Windows 11, dependency checks | **VERIFIED** |
| **2. Alembic Migrations** | [`evidence/02_alembic_migration.txt`](file:///evidence/02_alembic_migration.txt) | `alembic upgrade head`, `pg_constraint` GiST exclusion query | **VERIFIED** |
| **3. Idempotent Seed** | [`evidence/03_seed_verification.txt`](file:///evidence/03_seed_verification.txt) | `python scripts/seed.py` (run twice consecutively, zero duplicates) | **VERIFIED** |
| **4. Test Suite & Concurrency** | [`evidence/04_pytest_full.txt`](file:///evidence/04_pytest_full.txt) | `pytest -v -s` (10 concurrent requests: 1x 201 Created, 9x 409 Conflict) | **VERIFIED** |
| **5. Docker Build & Compose** | [`evidence/05_docker_build_compose.txt`](file:///evidence/05_docker_build_compose.txt) | Multi-stage build (322MB, non-root `appuser:10001`), Compose up, `/health` 200 | **VERIFIED** |
| **6. CI Pipeline Verification** | [`evidence/06_ci_pipeline.txt`](file:///evidence/06_ci_pipeline.txt) | GitHub API extraction of runs `43716465249` (PR) & `43716727141` (main) | **VERIFIED** |
| **7. Versioned GHCR Digest** | [`evidence/07_image_digest.txt`](file:///evidence/07_image_digest.txt) | `v1.0.0` release workflow `43717288264`, `imagetools inspect`, digest pull | **VERIFIED** |
| **8. Observability & Outage Drill** | [`evidence/08_observability_failure_drill.txt`](file:///evidence/08_observability_failure_drill.txt) | DB stopped: `/health` 200, `/ready` 503, JSON logs + `x-request-id`, self-healing | **VERIFIED** |
| **9. Backup, Restore & Persistence** | [`evidence/09_backup_restore.txt`](file:///evidence/09_backup_restore.txt) | `backup.ps1` (-Fc dump), table wipe, `restore.ps1`, volume persistence drill | **VERIFIED** |
| **10. Versioned Rollback Drill** | [`evidence/10_rollback_drill.txt`](file:///evidence/10_rollback_drill.txt) | v1.0.0 deployed -> v1.0.1 HTTP 500 regression -> rolled back to v1.0.0 | **VERIFIED** |

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
- Multi-stage Docker build producing a lean 322MB image running as non-root `appuser:10001`.
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
- Immediate zero-downtime rollback executed via `APP_VERSION=v1.0.0 docker compose up -d app`.
- Verified immediate recovery to HTTP 200 OK; source code clean and untouched.
