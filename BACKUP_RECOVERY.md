# BACKUP, DISASTER RECOVERY & ROLLBACK RUNBOOK

**System:** MPLAD GUARDIAN Production Platform  
**Specification:** Phase 4.5 Production Operations Standard  

---

## 1. Overview & RPO / RTO Targets

| Objective | Target | Implementation Mechanism |
| :--- | :--- | :--- |
| **Recovery Point Objective (RPO)** | < 1 Hour | Hourly automated snapshots + WAL archiving |
| **Recovery Time Objective (RTO)** | < 5 Minutes | Fast container restart & instant SQLite rollback toggle |
| **Integrity Verification** | 100% Deterministic | SHA-256 checksums + `PRAGMA integrity_check` / `pg_checksums` |

---

## 2. Backup Procedures

### 2.1 Hot Online SQLite Backup (Current & Fallback)
```bash
python scripts/backup_database.py
```
- Uses SQLite Online Backup API (`sqlite3.backup`) to capture a hot snapshot without locking concurrent readers.
- Automatically writes timestamped backup to `backups/mplad_backup_YYYYMMDD_HHMMSS.db`.
- Computes SHA-256 cryptographic checksum and executes `PRAGMA integrity_check`.

### 2.2 PostgreSQL Production Logical Backup (`pg_dump`)
```bash
# Export full compressed custom-format dump
docker compose exec postgres pg_dump -U app_user -d mplad_db -Fc -f /var/lib/postgresql/data/mplad_backup.dump

# Copy to host backup repository
docker cp mplad-postgres:/var/lib/postgresql/data/mplad_backup.dump ./backups/
```

### 2.3 PostGIS Spatial Boundary Backup
```bash
docker compose exec postgres pg_dump -U app_user -d mplad_db -t spatial_boundaries -Fc -f /var/lib/postgresql/data/spatial_boundaries.dump
```

---

## 3. Restore & Disaster Recovery Procedures

### 3.1 Restoring PostgreSQL from Logical Dump
```bash
# 1. Terminate active application connections
docker compose stop backend worker

# 2. Re-create database schema and restore
docker compose exec postgres dropdb -U app_user --if-exists mplad_db
docker compose exec postgres createdb -U app_user mplad_db
docker compose exec postgres pg_restore -U app_user -d mplad_db /var/lib/postgresql/data/mplad_backup.dump

# 3. Restart application containers
docker compose start backend worker
```

### 3.2 Instant Rollback to Authoritative SQLite Engine
If PostgreSQL cluster suffers critical hardware failure, data corruption, or network segmentation:

1. **Step 1:** Modify environment variable:
   ```env
   DATABASE_URL=
   DATABASE_PATH=/app/mplad.db
   ```
2. **Step 2:** Restart the backend container:
   ```bash
   docker compose restart backend
   ```
3. **Step 3:** Verify readiness:
   ```bash
   curl http://localhost:8000/api/v1/ready
   # Expected: {"status": "ready"}
   ```

*Zero downtime fallback: SQLite database `mplad.db` remains mounted read-only and always available.*
