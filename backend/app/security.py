import hashlib, hmac, os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import JWT_SECRET

bearer = HTTPBearer()

def create_token(user_id: int, role:str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_jwt(creds:HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(*roles):
    def checker(token: dict = Depends(decode_jwt)):
        if token["role"] not in roles:
            raise HTTPException(status_code=403, detail="Not allowed")
        return token
    return checker

def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"

def hash_otp(code: str) -> str:
    return hashlib.sha256((code + JWT_SECRET).encode()).hexdigest()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored) -> bool:
    if not stored:
        return False
    try:
        salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
    return hmac.compare_digest(digest.hex(), digest_hex)