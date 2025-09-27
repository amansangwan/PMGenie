from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ----------- Requests -----------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str
    phone: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None


# ----------- Responses -----------

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
