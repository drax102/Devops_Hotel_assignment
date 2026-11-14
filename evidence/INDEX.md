# Evidence Index: Hotel Reservation DevOps & Cloud Engineering

This document indexes all verification outputs, test runs, CI logs, and operational drills executed against the repository. Every referenced evidence artifact represents raw, unedited command output generated on the system.

---

## Acceptance Test & Rubric Verification Map

| Step / Requirement | Evidence File | Command Executed | Status |
| :--- | :--- | :--- | :--- |
| **1. Baseline & Hygiene** | `evidence/01_baseline_audit.txt` | Dependency checks, layout validation, git status | **VERIFIED** |
| **2. Alembic Migrations** | `evidence/02_alembic_migration.txt` | `alembic upgrade head`, `pg_constraint` inspection | **VERIFIED** |
| **3. Idempotent Seed** | `evidence/03_seed_verification.txt` | `python scripts/seed.py` (run twice, no duplicates) | **VERIFIED** |
| **4. Full Test Suite & Concurrency** | `evidence/04_pytest_full.txt` | `pytest -v -s` (11 tests pass, 1x 201 + 9x 409) | **VERIFIED** |
| **5. Docker Build & Compose** | `evidence/05_docker_build_compose.txt` | `docker compose up -d --build`, image size inspection | Pending |
| **6. CI Pipeline Run** | `evidence/06_ci_pipeline.txt` | GitHub Actions workflow execution & run URL | Pending |
| **7. Observability & Drill** | `evidence/07_observability_failure_drill.txt` | DB outage drill, `/health` vs `/ready`, JSON logs | Pending |
| **8. Nginx HTTPS Proxy** | `evidence/08_nginx_https.txt` | `curl.exe -k https://localhost/health` & cert verification | Pending |
| **9. Backup, Restore & Rollback** | `evidence/09_backup_restore_rollback.txt` | `backup.ps1`, corruption, `restore.ps1`, v1.0.1 rollback | Pending |
| **10. Final Acceptance** | `evidence/10_acceptance_suite.txt` | All 7 handover acceptance tests | Pending |

---

## Artifact Summaries

### `evidence/01_baseline_audit.txt`
- Baseline system and runtime environment audit (Python 3.13.5, Windows 11, pinned packages).

### `evidence/02_alembic_migration.txt`
- Output of `alembic upgrade head` applying revision `6944177ec459`.
- Direct query from `pg_constraint` confirming `prevent_overlapping_reservations` constraint type `x` (exclusion) using `btree_gist` and `daterange(check_in, check_out, '[)') WITH && WHERE (status = 'confirmed')`.

### `evidence/03_seed_verification.txt`
- Output of running `python scripts/seed.py` consecutively twice.
- First run creates rooms 101, 102, 201, 202 and booking BK001.
- Second run detects existing records, skips them, and completes with zero duplicate key errors.

### `evidence/04_pytest_full.txt`
- Full test run against isolated `hotel_test_db`.
- 11 passed tests including health, rooms, reservations, availability, boundary edge cases, and 10 concurrent requests resulting in exactly one HTTP 201 Created and nine HTTP 409 Conflict responses.
