import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import jwt
from fastapi import HTTPException, status
from jose import JWTError

load_dotenv("creds.env")
SECRET_KEY = os.getenv("JWT_SECRET", "change_me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MIN", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TTL_DAYS", "7"))

def create_tokens(user_id: int):
    access_exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = jwt.encode(
        {"sub": str(user_id), "exp": access_exp}, SECRET_KEY, algorithm=ALGORITHM
    )
    refresh_token = jwt.encode(
        {"sub": str(user_id), "exp": refresh_exp, "type": "refresh"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except JWTError:
        return None


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return int(payload.get("sub"))
    except JWTError:
        return None