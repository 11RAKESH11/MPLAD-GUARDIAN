from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.app.database import query_db
from backend.app.auth import hash_pw, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginRequest):
    p_hash = hash_pw(req.password)
    user = query_db("SELECT id, username, full_name, email, role, department FROM users WHERE username = ? AND password_hash = ?", (req.username, p_hash), one=True)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_dict = dict(user)
    token = create_access_token({"sub": user_dict["username"], "role": user_dict["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_dict
    }

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/demo-accounts")
def demo_accounts():
    return {
        "accounts": [
            {"username": "admin", "role": "ADMIN", "description": "Full administrative oversight, alert resolution & system config", "default_password": "admin123"},
            {"username": "analyst", "role": "ANALYST", "description": "Analytical deep-dive, risk triage & alert acknowledgment", "default_password": "analyst123"},
            {"username": "viewer", "role": "VIEWER", "description": "Read-only access to public intelligence & dashboards", "default_password": "viewer123"}
        ]
    }
