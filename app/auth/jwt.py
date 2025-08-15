import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import jwt
from fastapi import HTTPException, status
from jose import JWTError

load_dotenv("creds.env")
SECRET = os.getenv("JWT_SECRET", "change_me")
ALGO = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TTL = int(os.getenv("JWT_ACCESS_TTL_MIN", "60"))
REFRESH_TTL = int(os.getenv("JWT_REFRESH_TTL_MIN", "10080"))

def _encode(payload: dict, ttl_min: int) -> str:
    to_encode = payload.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=ttl_min)})
    return jwt.encode(to_encode, SECRET, algorithm=ALGO)

def create_tokens(user_id: int):
    access = _encode({"sub": str(user_id), "type": "access"}, ACCESS_TTL)
    refresh = _encode({"sub": str(user_id), "type": "refresh"}, REFRESH_TTL)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

def verify_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
