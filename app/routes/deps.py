from fastapi import Depends, Header, HTTPException
from app.auth.jwt import verify_access_token

def get_current_user_id(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split()[1]
    user_id = verify_access_token(token)
    return user_id