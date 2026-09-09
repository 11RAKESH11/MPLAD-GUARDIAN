# 🔒 PRODUCTION SECURITY AUDIT REPORT — MPLAD GUARDIAN

**Project:** SIH 2026 | SIH26102 (MPLADS Operational Oversight Intelligence)  
**Audit Scope:** Full Application Security, Authentication, Authorization, Cryptography, API Endpoints, Database, Docker & Infrastructure  
**Auditor:** Principal Security Architect & DevSecOps Lead  
**Audit Date:** 2026-08-28  
**Audit Baseline Status:** Pre-Hardening Assessment

---

## 1. Executive Security Findings Summary

| ID | Security Area | Severity | Current Vulnerability / Risk | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | **Password Hashing** | **HIGH** | Passwords stored with unsalted SHA-256 (`hashlib.sha256(pw)`). Vulnerable to dictionary & rainbow table attacks. | Replace with **Argon2id** (memory-hard, salted, adaptive cost). |
| **SEC-02** | **Hardcoded JWT Secret Fallback** | **CRITICAL** | Default hardcoded fallback JWT secret in `backend/app/auth.py` and `docker-compose.yml`. | Enforce strict env loading; fail startup in production if `JWT_SECRET` is missing. |
| **SEC-03** | **Default Seed Credentials** | **HIGH** | Seed credentials exposed in demo endpoint and frontend default state. | Disable default credentials in production; require password initialization. |
| **SEC-04** | **Server-Side Authorization (RBAC)** | **CRITICAL** | Sensitive endpoints (e.g. `POST /api/alerts/{id}/status`, `GET /api/audit-logs`) lack strict role enforcement. | Implement strict role guards: `ADMIN`, `ANALYST`, `VIEWER` with HTTP 403 enforcement. |
| **SEC-05** | **CORS Misconfiguration** | **MEDIUM** | `allow_origins=["*"]` configured with `allow_credentials=True` in `backend/app/main.py`. | Restrict to explicit origins via `ALLOWED_ORIGINS` environment variable. |
| **SEC-06** | **HTTP Security Headers** | **MEDIUM** | Missing Content Security Policy (CSP), HSTS, X-Frame-Options, and Permissions-Policy headers. | Implement production security headers middleware in FastAPI. |
| **SEC-07** | **Rate Limiting** | **MEDIUM** | Authentication and analytical query endpoints lack rate limiting. Vulnerable to brute force. | Implement IP/token rate limiting on `/api/auth/login` (HTTP 429). |
| **SEC-08** | **Production Error Disclosure** | **LOW** | Potential stack trace / internal exception leakage in unhandled error states. | Implement centralized sanitized error handling with unique `request_id`. |
| **SEC-09** | **Docker Security & Least Privilege** | **MEDIUM** | Containers running as root user; environment files contain fallback keys. | Configure non-root `appuser`, minimal image surface, and network segregation. |
| **SEC-10** | **Audit Logging Integrity** | **LOW** | Audit log endpoint exposed publicly without ADMIN authentication check. | Restrict audit logs to ADMIN role with immutable append-only semantics. |

---

## 2. Secrets & Credential Detection Log

> [!WARNING]
> In compliance with the zero-secret-disclosure mandate, actual credential values and cryptographic hashes are redacted.

```
SECRET DETECTED
LOCATION: backend/app/auth.py (Line 11)
SEVERITY: CRITICAL
DESCRIPTION: Hardcoded default JWT secret string used as fallback when JWT_SECRET env var is unset.

SECRET DETECTED
LOCATION: docker-compose.yml (Line 12)
SEVERITY: HIGH
DESCRIPTION: Static default JWT_SECRET placeholder provided in compose definition.

SECRET DETECTED
LOCATION: backend/app/routers/auth_router.py (Lines 35-37)
SEVERITY: MEDIUM
DESCRIPTION: Demo accounts endpoint returning default developmental passwords in plain text response.

SECRET DETECTED
LOCATION: ai-service/ingest_and_analyze.py (Lines 420-422)
SEVERITY: MEDIUM
DESCRIPTION: Default demo user seeding using legacy SHA-256 password hashes.
```

---

## 3. Deep-Dive Component Audit

### 3.1 Authentication & Password Storage
- **Current State:** `hash_pw()` computes `hashlib.sha256(pw.encode('utf-8')).hexdigest()`.
- **Defect:** Fast hash function without salt or memory hardness allows rapid GPU cracking.
- **Required Fix:** Transition to `argon2.PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1, hash_len=32, type=argon2.Type.ID)`. Support automatic migration from legacy hashes upon successful authentication.

### 3.2 JWT Token Lifecycle
- **Current State:** Custom HS256 sign/verify implementation with 24-hour expiration (`86400s`).
- **Defect:** 24-hour expiration is excessively long for high-privilege oversight dashboards. Fallback secret permits forged tokens if env var is missing.
- **Required Fix:** Set access token TTL to 30 minutes (`1800s`). Require `JWT_SECRET` in production with fail-safe startup assertion (minimum 32 bytes). Maintain minimal JWT payload claims (`sub`, `role`, `iat`, `exp`, `jti`, `iss`).

### 3.3 Authorization & Role-Based Access Control (RBAC)
- **Current State:** `get_current_user` defaults to a synthetic `VIEWER` guest when no Authorization header is provided.
- **Defect:** `alerts_router.py` does not check role on status updates; `audit_router.py` allows anonymous inspection of administrative audit trails.
- **Required Fix:** Enforce server-side role dependencies:
  - `ADMIN`: User management, system config, full analytics, alert resolution, audit logs.
  - `ANALYST`: Analytics inspection, alert acknowledgment, investigation notes.
  - `VIEWER`: Read-only public dashboards; strictly denied (HTTP 403) from alert mutations and audit logs.

### 3.4 API Input Validation & SQL Injection Defense
- **Current State:** Project queries use parameterized queries (`?`), but search and sort inputs require strict whitelist validation.
- **Defect:** Unvalidated search parameters could permit denial of service via unbounded wildcards.
- **Required Fix:** Enforce Pydantic body schemas and whitelist enumeration for `status`, `severity`, `alert_type`, `sort_by`, `financial_year`, and `category`.

### 3.5 CORS & Network Security
- **Current State:** `CORSMiddleware` configured with `allow_origins=["*"]` and `allow_credentials=True`.
- **Defect:** Browsers reject wildcards with credentials, and permissive CORS creates cross-origin data exposure risks.
- **Required Fix:** Restrict `allow_origins` to explicitly configured origins from `ALLOWED_ORIGINS` environment variable (defaulting to local development origins in dev mode).

### 3.6 HTTP Security Headers
- **Current State:** Only `X-Response-Time` header is attached.
- **Required Fix:** Attach standard protective headers via middleware:
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none';`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()`

---

## 4. Remediation Checklist

- [x] Pre-Hardening Security Audit Completed
- [ ] Implement Argon2id Password Hashing & Migration Path
- [ ] Enforce Strict Password Complexity Policy (≥12 characters)
- [ ] Secure JWT Engine (Env requirement, 30m TTL, fail-safe startup)
- [ ] Implement Server-Side RBAC (`ADMIN`, `ANALYST`, `VIEWER`) across all routers
- [ ] Implement In-Memory Rate Limiting for Login & High-Cost Endpoints
- [ ] Secure CORS & Attach HTTP Security Headers
- [ ] Implement Sanitized Global Error Handling with Request IDs
- [ ] Harden Dockerfile & Docker Compose Configurations
- [ ] Build Automated Security Test Suite
- [ ] Run Full Regression Suite (Dashboard, Map, Explorer, Evidence Room)
- [ ] Generate `SECURITY.md`, `THREAT_MODEL.md`, and `PHASE3_SECURITY_REPORT.md`

---
**Audit Status:** Baseline Audit Complete — Proceeding with Phase 3 Production Hardening.
