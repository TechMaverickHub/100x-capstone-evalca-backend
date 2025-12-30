from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.model import User
from auth.schema import UserResponse, UserSignup
from core.security import hash_password
from database.session import get_db
from core.global_constants import ErrorMessage

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, ErrorMessage.EMAIL_ALREADY_EXISTS.value)

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
