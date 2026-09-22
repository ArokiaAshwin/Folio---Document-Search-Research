import os
import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from flask import request
from jose import JWTError, jwt
from pydantic import BaseModel
from backend.config import settings

# File-backed user store for persistence
USERS_FILE = os.path.join(settings.BASE_DIR, "users.json")

class AuthError(Exception):
    """Custom exception for authentication and authorization errors."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

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

import urllib.request
import urllib.parse

# User models
class UserRegister(BaseModel):
    email: str
    password: str
    username: Optional[str] = None

class UserLogin(BaseModel):
    password: str
    email: Optional[str] = None
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    picture: Optional[str] = None
    is_guest: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "picture": self.picture,
            "is_guest": self.is_guest
        }

def register_user(req: UserRegister) -> UserResponse:
    email = req.email.strip().lower()
    if "@" not in email or "." not in email:
        raise AuthError(status_code=400, detail="Please enter a valid email address.")
    
    if len(req.password) < 6:
        raise AuthError(status_code=400, detail="Password must be at least 6 characters long.")

    username = (req.username or "").strip()
    if not username:
        # Auto-derive friendly username from email prefix
        username = email.split("@")[0]

    users = _load_users()
    for u in users.values():
        if u.get("email", "").lower() == email:
            raise AuthError(status_code=400, detail="An account with this email already exists.")
    
    # Check if username is taken; if auto-generated and taken, append digits
    existing_usernames = {u.get("username", "").lower() for u in users.values()}
    final_username = username
    if final_username.lower() in existing_usernames:
        final_username = f"{username}_{secrets.token_hex(2)}"

    user_id = f"user_{secrets.token_hex(6)}"
    users[user_id] = {
        "id": user_id,
        "username": final_username,
        "email": email,
        "hashed_password": hash_password(req.password),
        "is_guest": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _save_users(users)
    return UserResponse(id=user_id, username=final_username, email=email, is_guest=False)

def authenticate_user(req: UserLogin) -> UserResponse:
    identifier = (req.email or req.username or "").strip().lower()
    if not identifier:
        raise AuthError(status_code=400, detail="Please enter your email or username.")

    users = _load_users()
    for user_id, u in users.items():
        user_email = u.get("email", "").lower()
        user_name = u.get("username", "").lower()
        if user_email == identifier or user_name == identifier:
            if verify_password(req.password, u.get("hashed_password", "")):
                return UserResponse(
                    id=user_id, 
                    username=u.get("username", ""), 
                    email=u.get("email", ""), 
                    picture=u.get("picture"),
                    is_guest=False
                )
            raise AuthError(status_code=401, detail="Incorrect password. Please try again.")

    raise AuthError(status_code=401, detail="No account found with that email or username.")

def google_authenticate(credential: str) -> UserResponse:
    """
    Validates Google ID token using Google's tokeninfo API or demo credentials.
    Finds or registers the user, and returns UserResponse.
    """
    token = credential.strip()
    if not token:
        raise AuthError(status_code=400, detail="Google credential token is missing.")

    email = ""
    name = ""
    picture = ""
    google_id = ""

    # Check for demo/sandbox Google token (used when testing without GCP credentials)
    if token.startswith("demo_google:"):
        parts = token.split(":", 2)
        email = parts[1] if len(parts) > 1 else "demo_google_user@gmail.com"
        name = parts[2] if len(parts) > 2 else "Google Demo User"
        google_id = f"demo_gid_{hashlib.sha256(email.encode()).hexdigest()[:12]}"
        picture = "https://lh3.googleusercontent.com/a/default-user=s96-c"
    else:
        # Verify with Google's official public tokeninfo endpoint
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(token)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Folio-QA-Chatbot"})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise AuthError(status_code=401, detail="Google authentication failed.")
                data = json.loads(response.read().decode("utf-8"))
                
                if "error" in data or "error_description" in data:
                    raise AuthError(status_code=401, detail=data.get("error_description", "Invalid Google token."))
                
                email = data.get("email", "").strip().lower()
                name = data.get("name", "") or data.get("given_name", "") or email.split("@")[0]
                picture = data.get("picture", "")
                google_id = data.get("sub", "")
                
                if not email:
                    raise AuthError(status_code=400, detail="Email not provided by Google account.")
        except urllib.error.HTTPError as e:
            raise AuthError(status_code=401, detail="Google token verification failed or expired.")
        except Exception as e:
            if isinstance(e, AuthError):
                raise
            raise AuthError(status_code=500, detail=f"Failed to verify Google token: {str(e)}")

    users = _load_users()
    existing_user_id = None
    
    # 1. Match by google_id or email
    for uid, u in users.items():
        if u.get("google_id") == google_id or u.get("email", "").lower() == email:
            existing_user_id = uid
            break

    if existing_user_id:
        # Update user metadata with latest Google info
        u = users[existing_user_id]
        u["google_id"] = google_id
        if picture:
            u["picture"] = picture
        _save_users(users)
        return UserResponse(
            id=existing_user_id,
            username=u.get("username", name),
            email=u.get("email", email),
            picture=u.get("picture", picture),
            is_guest=False
        )

    # 2. Register brand new user from Google
    user_id = f"user_{secrets.token_hex(6)}"
    username = name if name else email.split("@")[0]
    
    # Make sure username is unique
    existing_usernames = {u.get("username", "").lower() for u in users.values()}
    final_username = username
    if final_username.lower() in existing_usernames:
        final_username = f"{username}_{secrets.token_hex(2)}"

    users[user_id] = {
        "id": user_id,
        "username": final_username,
        "email": email,
        "google_id": google_id,
        "picture": picture,
        "hashed_password": None, # Google OAuth users don't need a local password
        "is_guest": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _save_users(users)
    return UserResponse(id=user_id, username=final_username, email=email, picture=picture, is_guest=False)

def create_guest_user() -> UserResponse:
    guest_id = f"guest_{secrets.token_hex(4)}"
    return UserResponse(id=guest_id, username=f"Guest_{guest_id[-4:]}", email=f"{guest_id}@demo.local", is_guest=True)

def get_current_user() -> UserResponse:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # Default fallback to demo guest user if not logged in
        return create_guest_user()
    
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1].strip()
    payload = decode_access_token(token)
    if not payload:
        raise AuthError(status_code=401, detail="Invalid or expired authentication token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError(status_code=401, detail="Invalid token payload")
        
    if payload.get("is_guest", False):
        return UserResponse(id=user_id, username=payload.get("username", "Guest"), email="guest@demo.local", is_guest=True)

    users = _load_users()
    u = users.get(user_id)
    if not u:
        raise AuthError(status_code=401, detail="User not found")
        
    return UserResponse(
        id=user_id, 
        username=u.get("username", "User"), 
        email=u.get("email", ""), 
        picture=u.get("picture"),
        is_guest=False
    )

