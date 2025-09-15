from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.jwt import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return user_id
