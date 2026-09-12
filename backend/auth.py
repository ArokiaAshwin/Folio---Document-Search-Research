import os
import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from backend.config import settings

# Security bearer scheme
security = HTTPBearer(auto_error=False)

# File-backed user store for persistence
USERS_FILE = os.path.join(settings.BASE_DIR, "users.json")

def _load_users() -> Dict[str, dict]:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_users(users: Dict[str, dict]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, key_hex = hashed_password.split(":")
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# User models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_guest: bool = False

def register_user(req: UserRegister) -> UserResponse:
    users = _load_users()
    for u in users.values():
        if u.get("username").lower() == req.username.lower():
            raise HTTPException(status_code=400, detail="Username already exists")
        if u.get("email").lower() == req.email.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{secrets.token_hex(6)}"
    users[user_id] = {
        "id": user_id,
        "username": req.username,
        "email": req.email,
        "hashed_password": hash_password(req.password),
        "is_guest": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _save_users(users)
    return UserResponse(id=user_id, username=req.username, email=req.email, is_guest=False)

def authenticate_user(req: UserLogin) -> UserResponse:
    users = _load_users()
    for user_id, u in users.items():
        if u.get("username").lower() == req.username.lower():
            if verify_password(req.password, u.get("hashed_password", "")):
                return UserResponse(id=user_id, username=u["username"], email=u["email"], is_guest=False)
            break
    raise HTTPException(status_code=401, detail="Invalid username or password")

def create_guest_user() -> UserResponse:
    guest_id = f"guest_{secrets.token_hex(4)}"
    return UserResponse(id=guest_id, username=f"Guest_{guest_id[-4:]}", email=f"{guest_id}@demo.local", is_guest=True)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserResponse:
    if not credentials:
        # Default fallback to demo guest user if not logged in
        return create_guest_user()
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    if payload.get("is_guest", False):
        return UserResponse(id=user_id, username=payload.get("username", "Guest"), email="guest@demo.local", is_guest=True)

    users = _load_users()
    u = users.get(user_id)
    if not u:
        raise HTTPException(status_code=401, detail="User not found")
        
    return UserResponse(id=user_id, username=u["username"], email=u["email"], is_guest=False)
