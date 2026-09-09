# 🛡️ SECURITY ARCHITECTURE & GOVERNANCE GUIDE — MPLAD GUARDIAN

**System:** MPLAD GUARDIAN — Parliamentary Development & Expenditure Intelligence Platform  
**Hackathon Target:** Smart India Hackathon (SIH 2026) | Problem Statement SIH26102  
**Security Profile:** Production-Hardened Application & Infrastructure Architecture  
**Document Classification:** Official Security Architecture Guide

---

## 1. Authentication & Password Security

### 1.1 Password Storage (Argon2id)
All user authentication credentials are encrypted using **Argon2id** (`argon2-cffi`), the winner of the Password Hashing Competition (PHC) and recommended standard by OWASP and NIST.

- **Algorithm:** Argon2id (v=19)
- **Time Cost ($t$):** 2 iterations
- **Memory Cost ($m$):** 65,536 KiB (64 MB per hash)
- **Parallelism ($p$):** 1 lane
- **Hash Length:** 32 bytes
- **Salting:** Cryptographically secure 16-byte random salt generated automatically per password.
- **Legacy Migration:** Ingestion and verification engines support automated migration: if a legacy SHA-256 hash is verified on login, the database record is seamlessly upgraded in-place to Argon2id without disrupting the user session.

### 1.2 Password Policy
- **Minimum Length:** 12 characters in production environments (8 characters in development mode).
- **Complexity Requirements:** Must incorporate at least 3 distinct character classes:
  - Uppercase letters (`A-Z`)
  - Lowercase letters (`a-z`)
  - Numerical digits (`0-9`)
  - Special punctuation symbols (`!@#$%^&*()_+-=[]{}|;:,.<>?`)
- **Blocklist:** Common dictionary words and sequential sequences (e.g. `password123`, `admin123456`) are rejected at the API boundary.

---

## 2. JSON Web Token (JWT) Lifecycle & RBAC

### 2.1 Token Specification
- **Signing Algorithm:** HMAC-SHA256 (HS256)
- **Access Token Lifetime:** 30 minutes (`1800s`).
- **Cryptographic Secret:** Loaded exclusively from the `JWT_SECRET` environment variable.
- **Fail-Safe Startup:** If `ENVIRONMENT=production` and `JWT_SECRET` is unset, weak, or matches default placeholders, the backend immediately halts execution with a fatal error.
- **Payload Minimization:**
  ```json
  {
    "sub": "admin",
    "role": "ADMIN",
    "iat": 1756400000,
    "exp": 1756401800,
    "jti": "d4e8a1c9-72f3-4a1b-9e2c-3b1a8d4f6e5c",
    "iss": "mplad-guardian-security-engine"
  }
  ```
  *Note:* No sensitive personally identifiable information (PII), database credentials, or financial records are embedded in the JWT payload.

### 2.2 Role-Based Access Control (RBAC) Matrix

| Capability / Resource | ADMIN | ANALYST | VIEWER | Unauthenticated |
| :--- | :---: | :---: | :---: | :---: |
| **Public Dashboard & Map** | ✅ | ✅ | ✅ | ✅ (Read-Only) |
| **Project Explorer & Detail** | ✅ | ✅ | ✅ | ✅ (Read-Only) |
| **MP Portfolios & State Views** | ✅ | ✅ | ✅ | ✅ (Read-Only) |
| **Priority Review Alerts List** | ✅ | ✅ | ✅ | ✅ (Read-Only) |
| **Flagship Evidence Room** | ✅ | ✅ | ✅ | ✅ (Read-Only) |
| **Update Alert Status & Notes** | ✅ | ✅ | ❌ (HTTP 403) | ❌ (HTTP 401) |
| **View System Audit Logs** | ✅ | ❌ (HTTP 403) | ❌ (HTTP 403) | ❌ (HTTP 401) |
| **Trigger Data Ingestion Pipeline** | ✅ | ❌ (HTTP 403) | ❌ (HTTP 403) | ❌ (HTTP 401) |
| **User & Account Management** | ✅ | ❌ (HTTP 403) | ❌ (HTTP 403) | ❌ (HTTP 401) |

---

## 3. Network & Transport Layer Hardening

### 3.1 Cross-Origin Resource Sharing (CORS)
- **Configuration:** Managed via `ALLOWED_ORIGINS` environment variable.
- **Production Setting:** Explicit domain whitelist (e.g. `https://mpladguardian.gov.in,https://app.mpladguardian.gov.in`).
- **Policy:** Wildcard origins (`*`) combined with credential sharing (`allow_credentials=True`) are strictly forbidden in production.

### 3.2 HTTP Security Headers
Every HTTP response from the FastAPI engine attaches defense-in-depth protective headers:
- `Content-Security-Policy`: Restricts scripts and framing to trusted self-origins; denies clickjacking via `frame-ancestors 'none'`.
- `X-Content-Type-Options`: Set to `nosniff` to prevent MIME-confusion attacks.
- `X-Frame-Options`: Set to `DENY` to eliminate frame embedding.
- `Referrer-Policy`: `strict-origin-when-cross-origin`.
- `Permissions-Policy`: `geolocation=(), camera=(), microphone=(), payment=()`.
- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains` (enforced when served over HTTPS).

---

## 4. Rate Limiting & Anti-Abuse Defenses

### 4.1 In-Memory Sliding-Window Limiter
- **Endpoint:** `POST /api/auth/login`
- **Threshold:** Maximum 5 attempts per 60-second window per client IP address.
- **Penalty:** HTTP 429 Too Many Requests with retry-after header and detailed security audit logging.
- **Generic Responses:** Failed authentications always return generic `"Invalid credentials."` to prevent user enumeration.

---

## 5. SQL Injection & Cross-Site Scripting (XSS) Defenses

### 5.1 Parameterized SQL Queries
- All SQL queries across routers utilize parameterized binding (`?` placeholders) in SQLite/PostgreSQL.
- Dynamic sorting (`sort_by`, `order`) uses strict server-side dictionary whitelists; raw string interpolation of query parameters into SQL statements is strictly prohibited.

### 5.2 Zero-Trust Frontend Rendering
- The React application utilizes JSX auto-escaping for all dynamic data rendering (project descriptions, MP names, alert evidence, and audit logs).
- Dangerous execution sinks (`dangerouslySetInnerHTML`, `eval()`, `exec()`) are completely absent from the frontend codebase.

---

## 6. Container & Infrastructure Security

### 6.1 Docker Hardening
- **Non-Root Execution:** Backend Docker container executes as unprivileged user `appuser` (UID 10001) in `appgroup` (GID 10001).
- **Filesystem & Privilege:** Containers specify `no-new-privileges:true`.
- **Health Checks:** Automated container health checks verify availability via `curl -f http://localhost:8000/api/health`.
- **Network Isolation:** Internal Docker bridge network separates backend processing from external public networks.

---

## 7. Audit Logging & Request Traceability

### 7.1 Distributed Request Tracing
- All HTTP requests receive an RFC 4122 UUID4 `X-Request-ID` attached via middleware.
- Request IDs correlate error occurrences across server logs, client diagnostics, and the audit log table.

### 7.2 Immutable Audit Trail
- Security-sensitive actions (login success, login failure, rate-limiting triggers, alert status updates, password changes) are recorded to the `audit_logs` table.
- Audit records capture: `user_id`, `username`, `user_role`, `action`, `target_type`, `target_id`, `previous_state`, `new_state`, `notes`, `created_at`.
- Endpoints allow **append-only** access; audit records cannot be modified or deleted via user APIs.

---

## 8. Production Deployment Checklist

- [x] Ensure `ENVIRONMENT=production` and `DEBUG=false` in deployment `.env`.
- [x] Configure a cryptographically strong `JWT_SECRET` (≥32 bytes random).
- [x] Set explicit production domains in `ALLOWED_ORIGINS`.
- [x] Disable public demo accounts endpoint (`ENABLE_DOCS=false`).
- [x] Verify database file permissions (read/write restricted to application user).
- [x] Run SSL/TLS termination with valid certificates (HTTPS / HSTS).
- [x] Execute automated security regression test suite (`pytest tests/`).
