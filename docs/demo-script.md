# Video Walkthrough Script: Cloud Deployment & CI/CD Platform

**Target Duration**: 3 – 5 minutes  
**Target Audience**: Algions AI Labs Senior Evaluation Panel  
**Environment**: Windows 11 / PowerShell / Docker Desktop (WSL2)

---

## Pre-Recording Checklist
- [ ] Terminal font size enlarged to 18pt or 20pt for high legibility.
- [ ] Docker Desktop is running in background.
- [ ] Terminal is positioned at `D:\PROJECTS\assignment_hotel`.
- [ ] Browser window open with tabs:
  1. GitHub Repository: `https://github.com/drax102/Devops_Hotel_assignment`
  2. GitHub Actions Green Runs: `https://github.com/drax102/Devops_Hotel_assignment/actions`
  3. GHCR Container Package: `https://github.com/drax102/Devops_Hotel_assignment/pkgs/container/devops_hotel_assignment`

---

## Scene 1: Introduction & Clean Environment Startup (0:00 – 0:45)
**Satisfies Acceptance Test 2 (Clean build and start) & Acceptance Test 5 (Health checks)**

### Voiceover
> *"Hello! This is the demonstration of the Hotel Availability and Reservation Service for the Algions AI Labs Cloud Engineering assessment. We will walk through all seven mandatory acceptance tests. Starting with a clean clone, we generate our local TLS certificates and launch our multi-container architecture using Docker Compose."*

### Actions & Commands
```powershell
# 1. Generate local TLS certificates
powershell -ExecutionPolicy Bypass -File scripts/generate_certs.ps1

# 2. Start the service stack
docker compose up -d

# 3. Verify container topology and health
docker compose ps
```

### Visual Cue
Point to the three running services:
- `hotel-postgres`: PostgreSQL 17 on private bridge `hotel_internal` with named volume `postgres_data`.
- `hotel-app`: FastAPI application running strictly as non-privileged `appuser:10001`.
- `hotel-nginx`: Nginx reverse proxy terminating TLS and redirecting port 80 to 443.

### Probing Endpoints
```powershell
# Demonstrate HTTP port 80 redirect to HTTPS 443
curl.exe -i http://localhost/health

# Demonstrate HTTPS liveness probe (200 OK)
curl.exe -k -i https://localhost/health

# Demonstrate HTTPS readiness probe (DB connectivity check)
curl.exe -k -i https://localhost/ready
```

---

## Scene 2: Concurrency & Double-Booking Protection (0:45 – 1:30)
**Satisfies Acceptance Test 1 (Two concurrent conflicting reservations cannot both be confirmed)**

### Voiceover
> *"Acceptance Test 1 requires that two concurrent conflicting reservations cannot both be confirmed. We enforce this at the database engine layer using a PostgreSQL GiST exclusion constraint on room ID and date range. Let's run our automated concurrency test where ten simultaneous threads attempt to book the exact same room for overlapping dates."*

### Actions & Commands
```powershell
.venv\Scripts\pytest.exe tests/test_concurrency.py -v -s
```

### Visual Cue
Highlight the test output:
```
CONCURRENCY TEST COMPLETED:
Total Requests Sent:   10
Status 201 Created:    1
Status 409 Conflict:   9
```
> *"Exactly one booking is confirmed with HTTP 201 Created, while the other nine concurrent attempts are immediately rejected with HTTP 409 Conflict. Zero race conditions, zero data corruption."*

---

## Scene 3: CI/CD Pipeline & Versioned GHCR Container (1:30 – 2:15)
**Satisfies Acceptance Test 3 (CI runs checks, tests, build) & Acceptance Test 4 (Versioned image produced)**

### Voiceover
> *"Next, we demonstrate our automated CI/CD pipeline and container registry integration. Every pull request and push to main runs our GitHub Actions pipeline on Ubuntu 24.04 with Ruff, Black, PostgreSQL 17 migrations, and our full test suite. When a release tag is pushed, a multi-platform image is versioned and published to GitHub Container Registry."*

### Actions & Commands
Switch to browser or display in terminal:
```powershell
# Query live GitHub Actions status
powershell -Command @"
`$runs = curl.exe -s https://api.github.com/repos/drax102/Devops_Hotel_assignment/actions/runs | ConvertFrom-Json
`$runs.workflow_runs | Select-Object -First 2 id, head_branch, event, status, conclusion, html_url
"@
```

### Visual Cue
Point to workflow run `43717288264` and display remote GHCR image inspection:
```powershell
docker buildx imagetools inspect ghcr.io/drax102/devops_hotel_assignment:1.0.0
```
> *"Notice the verified immutable image index digest `sha256:9fc1f38d...` published directly to GHCR under tag `1.0.0`."*

---

## Scene 4: Observability & Outage Recovery Drill (2:15 – 3:00)
**Satisfies Acceptance Test 5 (Structured logs) & Acceptance Test 6 (Service failure detected and recovered)**

### Voiceover
> *"Acceptance Test 6 requires simulating a service failure, detecting it through observability, and demonstrating recovery. Our API emits structured JSON logs with correlation IDs, and decouples process liveness from database readiness. Let's run our automated failure drill."*

### Actions & Commands
```powershell
powershell -ExecutionPolicy Bypass -File scripts/failure_drill.ps1
```

### Visual Cue
Walk through the 3 phases printed by the script:
1. **Pre-outage**: Both `/health` and `/ready` return `200 OK`.
2. **Outage Injected** (`docker stop hotel-postgres`):
   - `/health` continues returning `200 OK` (web process alive).
   - `/ready` immediately returns `503 Service Unavailable`.
   - Structured JSON logs display `"level": "ERROR"`, `"request_id": "..."`, and database timeout details.
3. **Recovery** (`docker start hotel-postgres`):
   - Database reconnects.
   - `/ready` returns `200 OK`.
   - Successful reservation created immediately following recovery.

---

## Scene 5: Backup, Restore & Rollback Drills (3:00 – 3:45)
**Satisfies Acceptance Test 7 (DB backup restored, rollback demonstrated with evidence)**

### Voiceover
> *"Acceptance Test 7 requires demonstrating both a database backup and restore, and a fast rollback with a brief interruption. We provide automated scripts for both."*

### Actions & Commands
#### 1. Database Backup & Restore Drill
```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_backup_restore.ps1
```
Highlight output:
- Pre-backup: 5 rooms, 2 reservations.
- Atomic `pg_dump` binary dump created in `backups/`.
- Destruction simulated: `TRUNCATE TABLE reservations, rooms CASCADE` (0 rooms, 0 reservations).
- Restoration executed via `scripts/restore.ps1`.
- Post-restore: all 5 rooms, 2 reservations, and the GiST exclusion constraint restored intact!
- Volume persistence drill: PostgreSQL container deleted and recreated, proving persistent volume retention.

#### 2. Release Rollback Drill
```powershell
powershell -ExecutionPolicy Bypass -File scripts/rollback_drill.ps1
```
Highlight output:
- Stable release `v1.0.0` running healthy.
- Buggy release `v1.0.1` deployed; health check fails with `HTTP 500`.
- Automated rollback executed via `$env:APP_VERSION="v1.0.0"; docker compose up -d app`.
- Stack immediately recovers to `HTTP 200 OK` with zero configuration file modification.

---

## Scene 6: Conclusion (3:45 – 4:00)

### Voiceover
> *"All seven mandatory acceptance tests have been executed live, verified, and backed by raw evidence in the `evidence/` directory. Thank you for your time and evaluation!"*

---

## Summary of Acceptance Test Commands for Screencast

| Test # | Acceptance Requirement | Screencast Command |
| :---: | :--- | :--- |
| **1** | Concurrency Conflict Protection | `.venv\Scripts\pytest.exe tests/test_concurrency.py -v -s` |
| **2** | Clean Start from Documented Steps | `scripts/generate_certs.ps1; docker compose up -d` |
| **3** | CI Pipeline Execution | View GitHub Actions URL / `evidence/06_ci_pipeline.txt` |
| **4** | Versioned Image Produced | `docker buildx imagetools inspect ghcr.io/drax102/devops_hotel_assignment:1.0.0` |
| **5** | Health Checks & JSON Logs | `curl.exe -k https://localhost/health; docker compose logs --tail=20 app` |
| **6** | Failure Detected & Recovered | `powershell -ExecutionPolicy Bypass -File scripts/failure_drill.ps1` |
| **7** | DB Backup Restored & Rollback | `scripts/demo_backup_restore.ps1; scripts/rollback_drill.ps1` |
