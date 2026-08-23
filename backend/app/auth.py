import os
import hmac
import hashlib
import base64
import json
import time
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.database import query_db

SECRET_KEY = os.getenv("JWT_SECRET", "mplad-guardian-secret-key-sih2026-production").encode('utf-8')

security = HTTPBearer(auto_error=False)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)

def create_access_token(data: dict, expires_delta: int = 86400) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_delta
    
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

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials:
        return {"id": "viewer-guest", "username": "viewer", "role": "VIEWER", "full_name": "Public Intelligence Viewer"}
    
    token = credentials.credentials
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
        
    user = query_db("SELECT id, username, role, full_name, email, department FROM users WHERE username = ?", (username,), one=True)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)

def require_role(roles: list):
    def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles and "ADMIN" not in user.get("role"):
            raise HTTPException(status_code=403, detail="Insufficient permission for this operation")
        return user
    return role_checker
