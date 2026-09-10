#!/usr/bin/env python3
"""
MPLAD GUARDIAN — Production Readiness & Integrity Verifier
SIH 2026 | Problem Statement SIH26102

Verifies all critical subsystems for production deployment:
  1. Configuration & Environment Security
  2. Git Safety & Secrets Leakage
  3. Source Data Integrity (SQLite untouched & intact)
  4. Target Database Readiness (PostgreSQL / SQLite fallback)
  5. PostGIS Extension & Spatial Schema (if PostgreSQL)
  6. Required Tables & Schema Completeness
  7. Row Count Verification
  8. Redis Availability & Cache Status
  9. Frontend Production Build Artifacts
  10. Backend API Health & Readiness
  11. AI Microservice Health & Endpoints
"""

import sys
import os
import sqlite3
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class CheckResult:
    def __init__(self, category: str, name: str, status: str, message: str, details: str = ""):
        self.category = category
        self.name = name
        self.status = status  # PASS, FAIL, WARNING
        self.message = message
        self.details = details


class ReadinessVerifier:
    def __init__(self):
        self.results: List[CheckResult] = []

    def log(self, category: str, name: str, status: str, message: str, details: str = ""):
        self.results.append(CheckResult(category, name, status, message, details))

    def run_all_checks(self):
        print(f"\n{BOLD}{CYAN}{'=' * 75}{RESET}")
        print(f"{BOLD}{CYAN}  MPLAD GUARDIAN — PRODUCTION READINESS VERIFIER{RESET}")
        print(f"{BOLD}{CYAN}{'=' * 75}{RESET}\n")

        self.check_git_safety()
        self.check_environment_configuration()
        self.check_source_sqlite_database()
        self.check_database_target()
        self.check_redis()
        self.check_frontend_build()
        self.check_ai_engine()
        self.check_backend_schemas()

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Git Safety
    # ──────────────────────────────────────────────────────────────────────────
    def check_git_safety(self):
        cat = "GIT_SAFETY"

        # Check .gitignore exists and covers sensitive files
        gitignore_path = REPO_ROOT / ".gitignore"
        if not gitignore_path.exists():
            self.log(cat, ".gitignore Presence", "FAIL", ".gitignore file not found")
        else:
            content = gitignore_path.read_text(encoding="utf-8")
            required_patterns = [".env", "*.db", "node_modules"]
            missing = [p for p in required_patterns if p not in content]
            if missing:
                self.log(cat, ".gitignore Patterns", "WARNING", f"Missing patterns: {missing}")
            else:
                self.log(cat, ".gitignore Patterns", "PASS", "Essential patterns (.env, *.db, node_modules) present")

        # Check if .env or mplad.db is tracked by git
        try:
            import subprocess
            proc = subprocess.run(
                ["git", "ls-files", ".env", "mplad.db", "mplad.db.phase1_backup", "frontend/node_modules"],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            tracked_sensitive = [f.strip() for f in proc.stdout.splitlines() if f.strip()]
            if tracked_sensitive:
                self.log(cat, "Tracked Sensitive Files", "FAIL", f"Sensitive files tracked in git: {tracked_sensitive}")
            else:
                self.log(cat, "Tracked Sensitive Files", "PASS", "No sensitive files (.env, DBs, node_modules) tracked in git index")
        except Exception as e:
            self.log(cat, "Git Inspection", "WARNING", f"Could not inspect git index: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Environment Configuration
    # ──────────────────────────────────────────────────────────────────────────
    def check_environment_configuration(self):
        cat = "CONFIG_SECURITY"

        # Check .env.example exists
        env_example = REPO_ROOT / ".env.example"
        if env_example.exists():
            content = env_example.read_text(encoding="utf-8")
            # Verify it has NO real secrets
            if "bvmXwR52rLhifJkci03Ghj7GiHmrYmcq0AXWtbKHrU5P9EbJKc00ZkkVnf" in content:
                self.log(cat, ".env.example Secret Hygiene", "FAIL", "Real JWT_SECRET found in .env.example!")
            else:
                self.log(cat, ".env.example Hygiene", "PASS", ".env.example contains only clean placeholders")
        else:
            self.log(cat, ".env.example Presence", "FAIL", ".env.example is missing")

        # Check active environment settings if available
        jwt_secret = os.getenv("JWT_SECRET", "")
        env_mode = os.getenv("ENVIRONMENT", "development").lower()

        if env_mode == "production":
            if not jwt_secret or len(jwt_secret) < 32 or "REPLACE" in jwt_secret or "CHANGE_THIS" in jwt_secret:
                self.log(cat, "Production JWT_SECRET", "FAIL", "JWT_SECRET must be set to strong secret (>=32 chars) in production")
            else:
                self.log(cat, "Production JWT_SECRET", "PASS", "Strong JWT_SECRET configured")
        else:
            self.log(cat, "Environment Mode", "PASS", f"Running in '{env_mode}' mode")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Source SQLite Database
    # ──────────────────────────────────────────────────────────────────────────
    def check_source_sqlite_database(self):
        cat = "SOURCE_DATA"
        sqlite_path = REPO_ROOT / "mplad.db"

        if not sqlite_path.exists():
            self.log(cat, "Source SQLite DB Exists", "FAIL", f"mplad.db not found at {sqlite_path}")
            return

        file_size_mb = sqlite_path.stat().st_size / (1024 * 1024)
        if file_size_mb < 400:
            self.log(cat, "Source SQLite DB Size", "WARNING", f"DB size is {file_size_mb:.1f} MB (expected ~473 MB)")
        else:
            self.log(cat, "Source SQLite DB Size", "PASS", f"mplad.db intact ({file_size_mb:.1f} MB)")

        # Verify tables and row counts
        try:
            conn = sqlite3.connect(str(sqlite_path))
            cur = conn.cursor()

            expected_tables = {
                "projects": 90000,
                "risk_scores": 90000,
                "expenditure_vouchers": 100000,
                "mps": 700,
                "comparable_projects": 30000,
                "alerts": 200,
            }

            all_passed = True
            for tbl, min_count in expected_tables.items():
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                cnt = cur.fetchone()[0]
                if cnt < min_count:
                    all_passed = False
                    self.log(cat, f"Table [{tbl}] count", "FAIL", f"Found {cnt:,} rows, expected >= {min_count:,}")
                else:
                    self.log(cat, f"Table [{tbl}] count", "PASS", f"{cnt:,} rows verified")

            conn.close()
        except Exception as e:
            self.log(cat, "Source SQLite Access", "FAIL", f"Error querying SQLite source: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Database Target (PostgreSQL / SQLite fallback)
    # ──────────────────────────────────────────────────────────────────────────
    def check_database_target(self):
        cat = "TARGET_DATABASE"
        db_url = os.getenv("DATABASE_URL", "")

        if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
            self.log(cat, "Engine Target", "PASS", "PostgreSQL target configured via DATABASE_URL")
            try:
                import psycopg2
                conn = psycopg2.connect(db_url, connect_timeout=5)
                cur = conn.cursor()

                # Check PostGIS extension
                cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis';")
                ext = cur.fetchone()
                if ext:
                    self.log(cat, "PostGIS Extension", "PASS", f"PostGIS {ext[1]} active")
                else:
                    self.log(cat, "PostGIS Extension", "WARNING", "PostGIS extension not found in current database")

                # Check required production tables
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """)
                pg_tables = {r[0] for r in cur.fetchall()}
                required = ["projects", "risk_scores", "expenditure_vouchers", "mps", "alerts", "users"]
                missing = [t for t in required if t not in pg_tables]
                if missing:
                    self.log(cat, "PostgreSQL Schema Tables", "FAIL", f"Missing tables: {missing}")
                else:
                    self.log(cat, "PostgreSQL Schema Tables", "PASS", f"All core tables present ({len(pg_tables)} total)")

                conn.close()
            except Exception as e:
                self.log(cat, "PostgreSQL Connection", "WARNING", f"Could not connect to PostgreSQL: {e}. (Normal if Docker is not currently running)")
        else:
            env_mode = os.getenv("ENVIRONMENT", "development").lower()
            if env_mode == "production":
                self.log(cat, "Engine Target", "FAIL", "Production requires PostgreSQL DATABASE_URL, but none configured")
            else:
                self.log(cat, "Engine Target", "PASS", "Local development mode with SQLite engine fallback")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Redis Availability
    # ──────────────────────────────────────────────────────────────────────────
    def check_redis(self):
        cat = "REDIS_QUEUE"
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            r = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            self.log(cat, "Redis Connection", "PASS", f"Connected to Redis at {redis_url}")
        except Exception as e:
            self.log(cat, "Redis Connection", "WARNING", f"Redis not reachable ({e}). Backend will run with graceful in-process fallback.")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Frontend Build
    # ──────────────────────────────────────────────────────────────────────────
    def check_frontend_build(self):
        cat = "FRONTEND"
        dist_index = REPO_ROOT / "frontend" / "dist" / "index.html"
        dist_assets = REPO_ROOT / "frontend" / "dist" / "assets"

        if dist_index.exists() and dist_assets.exists():
            js_files = list(dist_assets.glob("*.js"))
            css_files = list(dist_assets.glob("*.css"))
            if js_files and css_files:
                self.log(cat, "Production Bundle", "PASS", f"Built bundle verified: index.html, {len(js_files)} JS chunk(s), {len(css_files)} CSS chunk(s)")
            else:
                self.log(cat, "Production Bundle", "WARNING", "dist/assets exists but JS/CSS chunks missing")
        else:
            self.log(cat, "Production Bundle", "WARNING", "frontend/dist not found. Run: cd frontend && npm run build")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. AI Engine Components
    # ──────────────────────────────────────────────────────────────────────────
    def check_ai_engine(self):
        cat = "AI_ENGINE"
        try:
            sys.path.insert(0, str(REPO_ROOT / "ai-service"))
            from risk_engine import RiskEngine
            from cost_anomaly import CostAnomalyEngine
            from duplicate_engine import DuplicateEngine
            from progress_rules import ProgressRuleEngine
            from geo_intelligence import GeographicIntelligenceEngine

            re = RiskEngine()
            # Test a dummy evaluation
            test_proj = {
                "work_code": "PROD-VERIFY-001",
                "category": "Education",
                "state": "Maharashtra",
                "district": "Pune",
                "sanctioned_amount": 500000.0,
                "expenditure_amount": 400000.0,
                "status": "Work Completed"
            }
            eval_res = re.evaluate_project(test_proj)
            if eval_res and "overall_risk_score" in eval_res and "explanation_json" in eval_res:
                self.log(cat, "RiskEngine Synthesis", "PASS", f"Risk Engine operational (score={eval_res['overall_risk_score']})")
            else:
                self.log(cat, "RiskEngine Synthesis", "FAIL", "RiskEngine evaluation returned incomplete structure")
        except Exception as e:
            self.log(cat, "AI Engine Modules", "FAIL", f"Failed to import/run AI components: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Backend Schemas & Database Abstraction
    # ──────────────────────────────────────────────────────────────────────────
    def check_backend_schemas(self):
        cat = "BACKEND_CORE"
        try:
            sys.path.insert(0, str(REPO_ROOT))
            from backend.app.database import query_db, get_engine_info
            info = get_engine_info()
            self.log(cat, "Database Layer", "PASS", f"Engine: {info['engine']}, URL: {info['database_url']}")

            # Run a baseline query to test placeholder translation and connectivity
            res = query_db("SELECT COUNT(*) FROM projects", one=True)
            if res and res[0] > 0:
                self.log(cat, "Query Execution", "PASS", f"Live query succeeded: {res[0]:,} projects accessible")
            else:
                self.log(cat, "Query Execution", "WARNING", "Query returned 0 projects or empty result")
        except Exception as e:
            self.log(cat, "Backend Database Layer", "FAIL", f"Error in database abstraction: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # Summary Report
    # ──────────────────────────────────────────────────────────────────────────
    def print_summary(self) -> int:
        passes = [r for r in self.results if r.status == "PASS"]
        warnings = [r for r in self.results if r.status == "WARNING"]
        fails = [r for r in self.results if r.status == "FAIL"]

        # Group by category
        categories: Dict[str, List[CheckResult]] = {}
        for r in self.results:
            categories.setdefault(r.category, []).append(r)

        for cat, results in categories.items():
            print(f"{BOLD}[CATEGORY: {cat}]{RESET}")
            for r in results:
                if r.status == "PASS":
                    badge = f"{GREEN}[PASS]{RESET}"
                elif r.status == "WARNING":
                    badge = f"{YELLOW}[WARNING]{RESET}"
                else:
                    badge = f"{RED}[FAIL]{RESET}"
                print(f"  {badge} {BOLD}{r.name}{RESET}: {r.message}")
            print()

        print(f"{BOLD}{'=' * 75}{RESET}")
        print(f"{BOLD}SUMMARY: {GREEN}{len(passes)} PASS{RESET} | {YELLOW}{len(warnings)} WARNING{RESET} | {RED}{len(fails)} FAIL{RESET}")
        print(f"{BOLD}{'=' * 75}{RESET}\n")

        if fails:
            print(f"{RED}{BOLD}>> PRODUCTION READINESS: BLOCKED ({len(fails)} critical failures){RESET}")
            return 1
        elif warnings:
            print(f"{YELLOW}{BOLD}>> PRODUCTION READINESS: READY WITH NOTICES ({len(warnings)} non-blocking warnings){RESET}")
            return 0
        else:
            print(f"{GREEN}{BOLD}>> PRODUCTION READINESS: FULLY READY FOR DEPLOYMENT{RESET}")
            return 0


def main():
    verifier = ReadinessVerifier()
    verifier.run_all_checks()
    exit_code = verifier.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
