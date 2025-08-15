from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.db.session import get_db
from app.models.user import User
from app.auth.jwt import create_tokens

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # auto-create minimal user for MVP
        password_hash = bcrypt.hash(req.password)
        user = User(email=req.email, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not bcrypt.verify(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_tokens(user.id)