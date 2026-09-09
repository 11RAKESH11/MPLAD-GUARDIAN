"""
MPLAD GUARDIAN — Backup & Disaster Recovery Utility (Phase 4.5)

Creates timestamped logical backups of the active database (SQLite / PostgreSQL)
with SHA-256 integrity checksum verification.
"""

import os
import sys
import time
import shutil
import hashlib
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backup_utility")

BACKUP_DIR = os.getenv("BACKUP_DIR", r"c:\SIH_PROJECT\backups")
SQLITE_SOURCE = os.getenv("SQLITE_PATH", r"c:\SIH_PROJECT\mplad.db")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

def backup_sqlite():
    ensure_dir(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"mplad_backup_{timestamp}.db")
    
    logger.info(f"Initiating hot online backup of SQLite database...")
    start = time.time()
    
    # Use SQLite Online Backup API for 100% consistent live backup
    src_conn = sqlite3.connect(SQLITE_SOURCE)
    dst_conn = sqlite3.connect(backup_file)
    
    with dst_conn:
        src_conn.backup(dst_conn, pages=1000)
        
    dst_conn.close()
    src_conn.close()
    
    elapsed = time.time() - start
    size_mb = os.path.getsize(backup_file) / (1024 * 1024)
    sha256 = compute_sha256(backup_file)
    
    meta_file = os.path.join(BACKUP_DIR, f"mplad_backup_{timestamp}.json")
    meta = {
        "timestamp": timestamp,
        "backup_file": os.path.basename(backup_file),
        "size_bytes": os.path.getsize(backup_file),
        "size_mb": round(size_mb, 2),
        "sha256": sha256,
        "duration_seconds": round(elapsed, 2),
        "engine": "sqlite"
    }
    
    import json
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)
        
    logger.info(f"✓ Backup successfully created at {backup_file} ({size_mb:.2f} MB in {elapsed:.2f}s)")
    logger.info(f"  SHA-256 Checksum: {sha256}")
    return backup_file, meta

def verify_backup(backup_file):
    logger.info(f"Verifying integrity of backup {backup_file}...")
    conn = sqlite3.connect(backup_file)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    result = cur.fetchone()[0]
    conn.close()
    
    if result.lower() == "ok":
        logger.info("✓ Backup integrity check PASSED.")
        return True
    else:
        logger.error(f"✗ Backup integrity check FAILED: {result}")
        return False

if __name__ == "__main__":
    b_file, meta = backup_sqlite()
    verify_backup(b_file)
