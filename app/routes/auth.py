from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.auth.jwt import create_tokens, verify_refresh_token
from app.auth.security import hash_password, verify_password
from app.routes.deps import get_current_user_id
from app.schemas.user import SignupRequest, LoginRequest, UpdateUserRequest, UserResponse

router = APIRouter(tags=["auth"])


def _user_to_dict(user: User):
    return {
        "id": user.id,
        "email": user.email,
        "name": getattr(user, 'name', None),
        "role": getattr(user, 'role', None),
        "phone": getattr(user, 'phone', None),
        "created_at": user.created_at,
    }


# ---------------- LOGIN ----------------
@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    tokens = create_tokens(user.id)
    return {**tokens, "user": _user_to_dict(user)}


# ---------------- SIGNUP ----------------
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    tokens = create_tokens(user.id)
    return {**tokens, "user": _user_to_dict(user)}


# ---------------- REFRESH TOKEN ----------------
@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    tokens = create_tokens(user.id)
    return {**tokens, "user": _user_to_dict(user)}


# ---------------- GET CURRENT USER ----------------
@router.get("/me", response_model=UserResponse)
def get_me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ---------------- UPDATE PROFILE ----------------
@router.patch("/update", response_model=UserResponse)
def update_profile(req: UpdateUserRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.name is not None:
        user.name = req.name
    if req.role is not None:
        user.role = req.role
    if req.phone is not None:
        user.phone = req.phone

    db.commit()
    db.refresh(user)
    return user
