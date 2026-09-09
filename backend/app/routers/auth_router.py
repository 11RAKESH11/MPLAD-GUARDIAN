from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.database import query_db, execute_db
from backend.app.auth import (
    create_access_token,
    get_current_user,
    verify_and_migrate_password,
    validate_password_policy,
    hash_password_argon2,
    check_login_rate_limit,
    log_security_event,
    IS_PRODUCTION
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Access Control"])

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="User account identifier")
    password: str = Field(..., min_length=1, max_length=128, description="User password")

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

@router.post("/login")
def login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Rate limit check (max 5 requests per 60s per IP)
    if not check_login_rate_limit(client_ip):
        log_security_event(
            action="LOGIN_RATE_LIMITED",
            user_id="anonymous",
            username=req.username,
            user_role="UNKNOWN",
            target_type="AUTH",
            target_id=req.username,
            notes="Login rate limit exceeded for client IP.",
            request_ip=client_ip,
            result="BLOCKED"
        )
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts. Please wait 60 seconds before trying again."
        )
        
    user = query_db(
        "SELECT id, username, password_hash, full_name, email, role, department FROM users WHERE username = ?",
        (req.username.strip(),),
        one=True
    )
    
    if not user:
        log_security_event(
            action="LOGIN_FAILED",
            user_id="unknown",
            username=req.username,
            user_role="UNKNOWN",
            target_type="AUTH",
            target_id=req.username,
            notes="Authentication attempt failed: user not found.",
            request_ip=client_ip,
            result="FAILURE"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials.")
        
    user_dict = dict(user)
    stored_hash = user_dict.get("password_hash")
    
    if not verify_and_migrate_password(req.password, stored_hash, user_dict["username"]):
        log_security_event(
            action="LOGIN_FAILED",
            user_id=user_dict["id"],
            username=user_dict["username"],
            user_role=user_dict["role"],
            target_type="AUTH",
            target_id=user_dict["id"],
            notes="Authentication attempt failed: invalid password.",
            request_ip=client_ip,
            result="FAILURE"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials.")
        
    token = create_access_token({"sub": user_dict["username"], "role": user_dict["role"]})
    
    # Log successful authentication
    log_security_event(
        action="LOGIN_SUCCESS",
        user_id=user_dict["id"],
        username=user_dict["username"],
        user_role=user_dict["role"],
        target_type="AUTH",
        target_id=user_dict["id"],
        notes=f"User successfully authenticated with role '{user_dict['role']}'.",
        request_ip=client_ip,
        result="SUCCESS"
    )
    
    # Return user object without sensitive fields
    safe_user = {
        "id": user_dict["id"],
        "username": user_dict["username"],
        "full_name": user_dict["full_name"],
        "email": user_dict["email"],
        "role": user_dict["role"],
        "department": user_dict["department"]
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": safe_user
    }

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, request: Request, current_user: dict = Depends(get_current_user)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    username = current_user["username"]
    
    user = query_db("SELECT password_hash FROM users WHERE username = ?", (username,), one=True)
    if not user or not verify_and_migrate_password(req.current_password, user["password_hash"], username):
        raise HTTPException(status_code=400, detail="Current password verification failed.")
        
    is_valid, msg = validate_password_policy(req.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)
        
    new_hash = hash_password_argon2(req.new_password)
    execute_db("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
    
    log_security_event(
        action="PASSWORD_CHANGE",
        user_id=current_user["id"],
        username=username,
        user_role=current_user["role"],
        target_type="USER",
        target_id=current_user["id"],
        notes="User successfully changed password.",
        request_ip=client_ip,
        result="SUCCESS"
    )
    
    return {"success": True, "detail": "Password successfully updated."}

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "department": current_user["department"]
    }

@router.get("/demo-accounts")
def demo_accounts():
    """
    Returns governance role descriptors. In production mode, credentials are fully redacted.
    In development mode, role descriptors and usernames are provided without plain text default passwords.
    """
    if IS_PRODUCTION:
        return {
            "mode": "PRODUCTION",
            "accounts": [],
            "notice": "Demo account enumeration is strictly disabled in production mode."
        }
        
    return {
        "mode": "DEVELOPMENT",
        "accounts": [
            {"username": "admin", "role": "ADMIN", "description": "Full administrative oversight, alert resolution & system config"},
            {"username": "analyst", "role": "ANALYST", "description": "Analytical deep-dive, risk triage & alert acknowledgment"},
            {"username": "viewer", "role": "VIEWER", "description": "Read-only access to public intelligence & dashboards"}
        ],
        "notice": "Development mode active. Passwords are securely hashed with Argon2id."
    }
