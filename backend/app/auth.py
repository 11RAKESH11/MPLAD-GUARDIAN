import os
import hmac
import hashlib
import base64
import json
import time
import re
import uuid
from typing import Optional, Tuple, List
from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from backend.app.database import query_db, execute_db

# Initialize Argon2id Password Hasher (memory-hard, salted, adaptive cost)
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=1,
    hash_len=32,
    type=Type.ID  # Argon2id
)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ["production", "prod"]

JWT_SECRET_ENV = os.getenv("JWT_SECRET")

# In production, require strong JWT secret and fail startup if missing or insecure
if IS_PRODUCTION:
    if not JWT_SECRET_ENV or JWT_SECRET_ENV in ["default-secret", "mplad-guardian-secret-key-sih2026-production", "admin", "secret"]:
        raise RuntimeError("FATAL SECURITY ERROR: JWT_SECRET environment variable must be set to a strong unique secret in production mode.")
    SECRET_KEY = JWT_SECRET_ENV.encode('utf-8')
else:
    # Development fallback with clear notice
    SECRET_KEY = (JWT_SECRET_ENV or "mplad-guardian-dev-secret-key-sih2026-local-only-do-not-use-in-prod").encode('utf-8')

security = HTTPBearer(auto_error=False)

# In-memory sliding-window rate limiter for login
LOGIN_ATTEMPTS: dict[str, list[float]] = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_RATE_WINDOW_SECONDS = 60.0

def hash_password_argon2(password: str) -> str:
    """Hashes a password using Argon2id with automatic salting."""
    return ph.hash(password)

def hash_pw(pw: str) -> str:
    """Legacy helper maintained for compatibility — produces Argon2id hashes."""
    return hash_password_argon2(pw)

def verify_and_migrate_password(plain_password: str, stored_hash: str, username: str) -> bool:
    """
    Verifies password using Argon2id. If the stored hash is a legacy SHA-256 hash,
    verifies via SHA-256 and seamlessly upgrades the database record to Argon2id.
    """
    if not stored_hash or not plain_password:
        return False
        
    # Check if stored hash is Argon2 format ($argon2id$ or $argon2i$)
    if stored_hash.startswith("$argon2"):
        try:
            ph.verify(stored_hash, plain_password)
            if ph.check_needs_rehash(stored_hash):
                new_hash = hash_password_argon2(plain_password)
                execute_db("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False
    else:
        # Check legacy SHA-256 hash (64 hex characters)
        legacy_sha = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        if hmac.compare_digest(legacy_sha, stored_hash):
            # Seamlessly upgrade legacy hash to Argon2id in database
            new_argon_hash = hash_password_argon2(plain_password)
            execute_db("UPDATE users SET password_hash = ? WHERE username = ?", (new_argon_hash, username))
            return True
        return False

def validate_password_policy(password: str) -> Tuple[bool, str]:
    """
    Enforces minimum 12 characters in production (8 in dev),
    with required character class diversity (upper, lower, digit, symbol).
    """
    min_len = 12 if IS_PRODUCTION else 8
    if len(password) < min_len:
        return False, f"Password must be at least {min_len} characters long."
        
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    char_classes = sum([has_upper, has_lower, has_digit, has_special])
    if char_classes < 3:
        return False, "Password must contain a mix of uppercase, lowercase, numbers, or special characters."
        
    common_weak = ["password123", "admin123456", "mplad123456", "123456789012"]
    if password.lower() in common_weak:
        return False, "Password is too common or easily guessable."
        
    return True, ""

def check_login_rate_limit(client_ip: str) -> bool:
    """Returns True if request is allowed, False if rate limit exceeded."""
    now = time.time()
    cutoff = now - LOGIN_RATE_WINDOW_SECONDS
    attempts = LOGIN_ATTEMPTS.get(client_ip, [])
    # Clean up expired timestamps
    valid_attempts = [t for t in attempts if t > cutoff]
    if len(valid_attempts) >= MAX_LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[client_ip] = valid_attempts
        return False
    valid_attempts.append(now)
    LOGIN_ATTEMPTS[client_ip] = valid_attempts
    return True

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)

def create_access_token(data: dict, expires_delta: int = 1800) -> str:
    """
    Creates a signed JWT with standard 30-minute (1800s) expiry and minimal payload.
    Payload contains only sub, role, iat, exp, jti, iss.
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": data.get("sub"),
        "role": data.get("role", "VIEWER"),
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        "iss": "mplad-guardian-security-engine"
    }
    
    header_b64 = b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = hmac.new(SECRET_KEY, signing_input, hashlib.sha256).digest()
    sig_b64 = b64url_encode(sig)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_token(token: str) -> dict:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid token structure")
        
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    expected_sig = hmac.new(SECRET_KEY, signing_input, hashlib.sha256).digest()
    actual_sig = b64url_decode(sig_b64)
    
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")
        
    payload = json.loads(b64url_decode(payload_b64).decode('utf-8'))
    if "exp" in payload and payload["exp"] < time.time():
        raise ValueError("Token expired")
        
    return payload

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """
    Strict user authentication for protected endpoints.
    Requires a valid JWT Bearer token; raises HTTP 401 if missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication token: missing subject claim.")
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    user = query_db("SELECT id, username, role, full_name, email, department FROM users WHERE username = ?", (username,), one=True)
    if user is None:
        raise HTTPException(status_code=401, detail="User account not found or deactivated.")
    return dict(user)

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """
    Permits public exploration by returning a synthetic VIEWER guest when unauthenticated,
    or returns the verified user dictionary if a valid Bearer token is provided.
    """
    if not credentials:
        return {"id": "viewer-guest", "username": "viewer", "role": "VIEWER", "full_name": "Public Intelligence Viewer"}
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return {"id": "viewer-guest", "username": "viewer", "role": "VIEWER", "full_name": "Public Intelligence Viewer"}

def require_role(roles: List[str]):
    """
    Server-side Role-Based Access Control (RBAC) dependency.
    ADMIN is universally authorized across all endpoints.
    Other roles must be explicitly listed in `roles`.
    Rejects unauthorized access with HTTP 403 Forbidden.
    """
    def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "VIEWER")
        if user_role == "ADMIN" or user_role in roles:
            return user
        raise HTTPException(
            status_code=403,
            detail=f"Access forbidden: Role '{user_role}' is not authorized for this operation. Required: {', '.join(roles)}"
        )
    return role_checker

def log_security_event(
    action: str,
    user_id: str,
    username: str,
    user_role: str,
    target_type: str,
    target_id: str,
    notes: str,
    request_ip: str = "internal",
    result: str = "SUCCESS"
):
    """Logs security and administrative events to the immutable audit log table."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        execute_db("""
        INSERT INTO audit_logs (user_id, username, user_role, action, target_type, target_id, previous_state, new_state, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, username, user_role, action, target_type, target_id,
            result, "", f"[{request_ip}] {notes}", now_str
        ))
    except Exception:
        pass
