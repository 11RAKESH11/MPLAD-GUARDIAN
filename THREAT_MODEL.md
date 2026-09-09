# 🛡️ SECURITY THREAT MODEL & RISK ASSESSMENT — MPLAD GUARDIAN

**System:** MPLAD GUARDIAN — Parliamentary Oversight & Governance Decision Intelligence  
**Framework:** STRIDE + OWASP Top 10 + NIST Cybersecurity Framework  
**Scope:** Frontend, FastAPI Backend, SQLite / PostgreSQL Storage, AI Anomaly Engine, and Container Runtime  
**Status:** Post-Hardening Threat Model (Phase 3 Complete)

---

## Threat Analysis Matrix (T1 – T12)

| Threat ID | Threat Category | Attack Surface | Existing / Pre-Hardening State | Production Hardened Defense | Residual Risk | Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **T1** | **Credential Theft** | User login, database storage, transmission | Unsalted SHA-256 password storage. Vulnerable to offline dictionary/rainbow table recovery if database is breached. | Upgraded to memory-hard **Argon2id** ($m=64\text{MB}, t=2, p=1$) with per-user unique salts. Strict TLS/HTTPS transport encryption. | Negligible; computational cost of offline brute forcing is infeasible. | **LOW** |
| **T2** | **Brute-Force & Credential Stuffing** | `POST /api/auth/login` | Unrestricted login endpoint allowed rapid automated authentication attempts. | **Sliding-window IP/user rate limiter** (max 5 requests/min $\rightarrow$ HTTP 429). Generic error message (`"Invalid credentials."`) prevents username enumeration. | Attacker distributing across vast botnet; mitigated by edge WAF/reverse proxy. | **LOW** |
| **T3** | **Privilege Escalation** | JWT token tampering, role header manipulation | Client role claims could theoretically be forged if JWT secret was default/weak. | **Server-side cryptographic JWT verification** using HMAC-SHA256 with strong environment secret. Role claim verified against database record on each privileged action. | Zero without compromising server `JWT_SECRET`. | **LOW** |
| **T4** | **Unauthorized API Access (BOLA / IDOR)** | Alert status updates, audit log viewing, admin actions | Default guest viewer permitted access without explicit role validation on select POST endpoints. | **Server-side RBAC dependencies (`require_role`)**: `ADMIN` (full control), `ANALYST` (triage/notes), `VIEWER` (strictly read-only public endpoints, HTTP 403 on mutation). | Minimal; verified by automated RBAC test matrix. | **LOW** |
| **T5** | **SQL Injection (SQLi)** | Project search queries, filters, sorting parameters | Dynamic `WHERE` clauses and string concatenation could allow data exfiltration. | **100% Parameterized queries (`?` placeholders)** across all database queries. Whitelist dictionaries for sort columns and order directions. | Zero; raw user strings never reach the SQL execution engine unparameterized. | **LOW** |
| **T6** | **Cross-Site Scripting (XSS)** | Project descriptions, MP names, alert notes in React UI | Unescaped HTML rendering or unsanitized dynamic sinks. | **React JSX auto-escaping** on all DOM nodes. Zero usage of `dangerouslySetInnerHTML`, `eval()`, or `innerHTML`. Strict CSP with `frame-ancestors 'none'`. | Negligible; zero dynamic script sinks in frontend. | **LOW** |
| **T7** | **Cross-Site Request Forgery (CSRF)** | Authenticated API mutation endpoints | Bearer tokens stored in client application. | Stateless JWT Bearer authorization in `Authorization` header rather than ambient cookies; CORS restricted via `ALLOWED_ORIGINS`. | Zero for Authorization-header-based REST APIs. | **LOW** |
| **T8** | **Secret & Credential Leakage** | Repository commits, API responses, Docker images | Hardcoded default secrets in code and compose files. | Enforced environment variable loading; fail-safe startup in production; zero secrets returned in API responses; `.gitignore` covers `.env` and database files. | Low; protected by Git pre-commit audits and CI scanning. | **LOW** |
| **T9** | **Malicious File Upload & Path Traversal** | Dataset ingestion and CSV processing | Ingestion scripts reading from relative directory paths. | Server reads only from verified static `DATA/` directory; zero public file upload endpoints exposed to unauthenticated users; path sanitization enforced. | Zero; no public upload vectors. | **LOW** |
| **T10** | **AI Engine Abuse & Denial of Service** | On-the-fly statistical analysis & similarity calculations | Unbounded TF-IDF or pairwise calculations on extremely large payload requests. | Input payload validation via Pydantic; pre-computed risk indexes; strict request timeouts; internal network segregation. | Low; heavy computations cached with TTL. | **LOW** |
| **T11** | **Data Tampering & Audit Log Deletion** | Project records, audit trails, risk scores | Potential manipulation of past audit trails or decision records. | **Append-only audit log semantics**; no `DELETE` or `UPDATE` endpoints exposed on `audit_logs`; database WAL mode with transaction integrity. | Low; requires direct operating system root database file access. | **LOW** |
| **T12** | **Information & Stack Trace Disclosure** | API error responses, debug endpoints | Development stack traces or SQL operational errors returned to client. | **Centralized FastAPI exception handlers** that sanitize 500 errors in production, generating a unique `request_id` and logging full traces strictly server-side. | Zero; clean JSON error contracts returned to client. | **LOW** |

---

## Threat Mitigation Verification Summary

- **Total Assessed Threats:** 12
- **Mitigated / Hardened:** 12 (100%)
- **Critical / High Residual Risks:** 0
- **Overall Security Posture:** **PRODUCTION-READY & HARDENED**
