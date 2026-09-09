import pytest
import time
import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth import (
    hash_password_argon2,
    verify_and_migrate_password,
    validate_password_policy,
    create_access_token,
    verify_token,
    ph,
    LOGIN_ATTEMPTS
)
from backend.app.database import query_db, execute_db

client = TestClient(app)

# ----------------------------------------------------------------------
# 1. PASSWORD SECURITY & ARGON2ID TESTS
# ----------------------------------------------------------------------

def test_argon2id_password_hashing():
    """Verify that password hashing uses genuine Argon2id format with salting."""
    pw = "StrongP@ssw0rd2026!"
    h1 = hash_password_argon2(pw)
    h2 = hash_password_argon2(pw)
    
    assert h1.startswith("$argon2id$"), "Hash must begin with $argon2id$"
    assert h1 != h2, "Different salts must produce distinct hash outputs for same password"
    assert verify_and_migrate_password(pw, h1, "testuser") is True
    assert verify_and_migrate_password("WrongPassword123!", h1, "testuser") is False

def test_legacy_sha256_automatic_migration():
    """Verify that legacy SHA-256 hashes are verified and seamlessly upgraded to Argon2id."""
    import hashlib
    test_user = "migrating_user"
    plain_pw = "MigrationP@ss123"
    legacy_sha = hashlib.sha256(plain_pw.encode('utf-8')).hexdigest()
    
    # Insert temporary user with legacy SHA256
    execute_db(
        "INSERT OR REPLACE INTO users (id, username, password_hash, role, full_name, email, department, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("usr-migrate-test", test_user, legacy_sha, "VIEWER", "Migrating User", "mig@test.gov", "Test", "2026-08-28")
    )
    
    # Verification should succeed and upgrade hash in database
    assert verify_and_migrate_password(plain_pw, legacy_sha, test_user) is True
    
    # Query database to confirm upgraded hash
    row = query_db("SELECT password_hash FROM users WHERE username = ?", (test_user,), one=True)
    assert row["password_hash"].startswith("$argon2id$"), "Stored hash must now be upgraded to Argon2id"
    
    # Clean up test user
    execute_db("DELETE FROM users WHERE username = ?", (test_user,))

def test_password_policy_enforcement():
    """Verify that weak or short passwords are rejected by the password policy validator."""
    # Too short (< 8 chars in dev)
    valid, msg = validate_password_policy("short")
    assert not valid
    assert "at least" in msg
    
    # Lack of character classes
    valid, msg = validate_password_policy("alllowercaseletters")
    assert not valid
    assert "mix" in msg
    
    # Known weak password
    valid, msg = validate_password_policy("password123")
    assert not valid
    
    # Strong compliant password
    valid, msg = validate_password_policy("Gov#Oversight$2026")
    assert valid
    assert msg == ""

# ----------------------------------------------------------------------
# 2. JWT LIFECYCLE & TAMPERING DEFENSE
# ----------------------------------------------------------------------

def test_jwt_valid_generation_and_verification():
    """Verify that valid JWTs contain minimal claims and verify successfully."""
    payload_data = {"sub": "admin", "role": "ADMIN"}
    token = create_access_token(payload_data, expires_delta=1800)
    
    decoded = verify_token(token)
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "ADMIN"
    assert decoded["iss"] == "mplad-guardian-security-engine"
    assert "exp" in decoded
    assert decoded["exp"] > time.time()

def test_jwt_expired_token_rejection():
    """Verify that expired JWTs are strictly rejected."""
    payload_data = {"sub": "admin", "role": "ADMIN"}
    expired_token = create_access_token(payload_data, expires_delta=-10)
    
    with pytest.raises(ValueError, match="Token expired"):
        verify_token(expired_token)
        
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401

def test_jwt_tampered_signature_rejection():
    """Verify that tampered tokens fail signature verification."""
    token = create_access_token({"sub": "viewer", "role": "VIEWER"})
    parts = token.split('.')
    
    # Tamper payload part to claim ADMIN role
    tampered_payload = json.dumps({"sub": "viewer", "role": "ADMIN", "exp": int(time.time()) + 1800})
    import base64
    tampered_b64 = base64.urlsafe_b64encode(tampered_payload.encode()).decode().rstrip('=')
    tampered_token = f"{parts[0]}.{tampered_b64}.{parts[2]}"
    
    resp = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp.status_code == 401

# ----------------------------------------------------------------------
# 3. AUTHENTICATION & LOGIN FLOW
# ----------------------------------------------------------------------

def test_login_success_and_generic_error():
    """Verify valid login produces token and invalid credentials yield generic 401."""
    # Valid login
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    assert "password_hash" not in data["user"], "Password hash must never be returned in API"
    
    # Invalid password -> generic error
    resp_bad = client.post("/api/v1/auth/login", json={"username": "admin", "password": "IncorrectPassword!"})
    assert resp_bad.status_code == 401
    assert resp_bad.json()["error"]["message"] == "Invalid credentials."
    
    # Nonexistent user -> generic error (no username enumeration)
    resp_no_user = client.post("/api/v1/auth/login", json={"username": "nonexistent_official", "password": "AnyPassword123!"})
    assert resp_no_user.status_code == 401
    assert resp_no_user.json()["error"]["message"] == "Invalid credentials."

def test_login_rate_limiting():
    """Verify that excessive failed login attempts trigger HTTP 429 Too Many Requests."""
    LOGIN_ATTEMPTS.clear()
    
    # Attempt 5 logins
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong_password"})
        
    # 6th attempt should be blocked with 429
    blocked_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong_password"})
    assert blocked_resp.status_code == 429
    assert "Too many authentication attempts" in blocked_resp.json()["error"]["message"]
    
    # Clean up rate limit state for other tests
    LOGIN_ATTEMPTS.clear()

# ----------------------------------------------------------------------
# 4. ROLE-BASED ACCESS CONTROL (RBAC) & AUTHORIZATION
# ----------------------------------------------------------------------

def test_rbac_matrix_on_protected_endpoints():
    """
    Rigorously verify access permissions across all three roles:
    - ADMIN: full access to audit logs and alert status updates
    - ANALYST: allowed alert status update, DENIED (403) audit logs
    - VIEWER: DENIED (403) alert status updates, DENIED (403) audit logs
    - UNATHENTICATED: DENIED (401) on protected endpoints
    """
    from backend.app.auth import LOGIN_ATTEMPTS
    LOGIN_ATTEMPTS.clear()
    token_admin = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    token_analyst = client.post("/api/v1/auth/login", json={"username": "analyst", "password": "analyst123"}).json()["access_token"]
    token_viewer = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "viewer123"}).json()["access_token"]
    
    # 1. Audit Logs (ADMIN only)
    resp_admin_audit = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp_admin_audit.status_code == 200, "ADMIN must be able to view audit logs"
    
    resp_analyst_audit = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token_analyst}"})
    assert resp_analyst_audit.status_code == 403, "ANALYST must be denied from audit logs"
    
    resp_viewer_audit = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token_viewer}"})
    assert resp_viewer_audit.status_code == 403, "VIEWER must be denied from audit logs"
    
    resp_anon_audit = client.get("/api/v1/audit-logs")
    assert resp_anon_audit.status_code == 401, "Unauthenticated user must be rejected with 401"
    
    # 2. Alert Status Mutation (ADMIN & ANALYST allowed, VIEWER denied)
    sample_alert = query_db("SELECT id FROM alerts LIMIT 1", one=True)[0]
    
    # VIEWER attempting mutation -> 403
    resp_viewer_alert = client.post(
        f"/api/v1/alerts/{sample_alert}/status",
        headers={"Authorization": f"Bearer {token_viewer}"},
        json={"status": "UNDER_REVIEW", "resolution_notes": "Unauthorized attempt"}
    )
    assert resp_viewer_alert.status_code == 403, "VIEWER must be rejected from modifying alert status"
    
    # ANALYST attempting mutation -> 200
    resp_analyst_alert = client.post(
        f"/api/v1/alerts/{sample_alert}/status",
        headers={"Authorization": f"Bearer {token_analyst}"},
        json={"status": "UNDER_REVIEW", "resolution_notes": "Oversight Analyst reviewed evidence"}
    )
    assert resp_analyst_alert.status_code == 200, "ANALYST must be authorized to update alert status"
    
    # ADMIN attempting mutation -> 200
    resp_admin_alert = client.post(
        f"/api/v1/alerts/{sample_alert}/status",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"status": "OPEN", "resolution_notes": "Reset by Administrator"}
    )
    assert resp_admin_alert.status_code == 200, "ADMIN must be authorized to update alert status"

# ----------------------------------------------------------------------
# 5. HTTP SECURITY HEADERS & DEFENSE-IN-DEPTH
# ----------------------------------------------------------------------

def test_http_security_headers_present():
    """Verify that all required security headers and X-Request-ID are attached to API responses."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    
    headers = resp.headers
    assert "X-Request-ID" in headers, "X-Request-ID must be present"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in headers
    assert "Content-Security-Policy" in headers
    assert "frame-ancestors 'none'" in headers.get("Content-Security-Policy")

# ----------------------------------------------------------------------
# 6. SQL INJECTION DEFENSE & INPUT VALIDATION
# ----------------------------------------------------------------------

def test_sql_injection_defense():
    """Verify that SQL injection payloads in search queries and parameters are safely handled."""
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT null, username, password_hash FROM users --",
        "admin'--",
        "<script>alert(1)</script>"
    ]
    
    for payload in sqli_payloads:
        # Search query
        resp = client.get("/api/v1/projects", params={"q": payload, "limit": 5})
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        
        # State query
        resp_st = client.get("/api/v1/states", params={"state": payload})
        assert resp_st.status_code == 200
        
        # Alert filter
        resp_al = client.get("/api/v1/alerts", params={"status": payload})
        assert resp_al.status_code == 200
        
    # Verify users table was NOT dropped
    user_count = query_db("SELECT COUNT(*) FROM users", one=True)[0]
    assert user_count >= 3, "Database integrity intact after SQL injection attempts"

# ----------------------------------------------------------------------
# 7. ERROR SANITIZATION
# ----------------------------------------------------------------------

def test_sanitized_validation_errors():
    """Verify that malformed requests return structured error with request_id."""
    resp = client.post("/api/v1/auth/login", json={"invalid_field": 123})
    assert resp.status_code == 422
    data = resp.json()
    assert "request_id" in data or "X-Request-ID" in resp.headers
    assert "error" in data or "detail" in data
