# Evidence Index: Hotel Reservation DevOps & Cloud Engineering

This document indexes all verification outputs, test runs, CI logs, and operational drills executed against the repository. Every referenced evidence artifact represents raw, unedited command output generated on the system.

---

## Acceptance Test & Rubric Verification Map

| Step / Requirement | Evidence File | Command Executed | Status |
| :--- | :--- | :--- | :--- |
| **1. Baseline & Hygiene** | `evidence/01_baseline_audit.txt` | Dependency checks, layout validation, git status | Verified |
| **2. Alembic Migrations** | `evidence/02_alembic_migration.txt` | `alembic upgrade head`, `pg_constraint` inspection | Pending |
| **3. API & Concurrency** | `evidence/03_api_and_concurrency.txt` | `pytest tests/test_concurrency.py` (10 parallel requests) | Pending |
| **4. Full Test Suite** | `evidence/04_pytest_full.txt` | `pytest -v` | Pending |
| **5. Docker Build & Compose** | `evidence/05_docker_build_compose.txt` | `docker compose up -d --build`, image size inspection | Pending |
| **6. CI Pipeline Run** | `evidence/06_ci_pipeline.txt` | GitHub Actions workflow execution & run URL | Pending |
| **7. Observability & Drill** | `evidence/07_observability_failure_drill.txt` | DB outage drill, `/health` vs `/ready`, JSON logs | Pending |
| **8. Nginx HTTPS Proxy** | `evidence/08_nginx_https.txt` | `curl.exe -k https://localhost/health` & cert verification | Pending |
| **9. Backup, Restore & Rollback** | `evidence/09_backup_restore_rollback.txt` | `backup.ps1`, corruption, `restore.ps1`, v1.0.1 rollback | Pending |
| **10. Final Acceptance** | `evidence/10_acceptance_suite.txt` | All 7 handover acceptance tests | Pending |

---

## Artifact Descriptions & Verification Hashes
*(Artifacts will be populated as each step executes with real outputs.)*
