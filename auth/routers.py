from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.auth_util import get_current_user, get_token_from_header
from auth.model import User
from auth.schema import UserResponse, UserSignup, TokenResponse, UserLogin
from core.jwt_utils import create_access_token, create_refresh_token, verify_access_token, blacklist_token, \
    verify_refresh_token
from core.security import hash_password, verify_password
from core.utils import response_schema
from database.session import get_db
from core.global_constants import ErrorMessage, SuccessMessage, GlobalConstants

router = APIRouter()

@router.post("/user-signup", response_model=UserResponse)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, ErrorMessage.EMAIL_ALREADY_EXISTS.value)

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_id=GlobalConstants.TEACHER_ROLE_ID
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email,User.is_active == True).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail=ErrorMessage.INVALID_CREDENTIALS.value)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    user_response = UserResponse.model_validate(user)
    return_data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user_response
    }
    return response_schema(return_data, SuccessMessage.LOGIN_SUCCESS.value, status.HTTP_200_OK)


@router.post("/logout")
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), token: str = Depends(get_token_from_header)):

    user_id = verify_access_token(token, db)
    if not user_id:
        raise HTTPException(status_code=401, detail=ErrorMessage.INVALID_TOKEN.value)
    if blacklist_token(token, db):
        return response_schema({}, SuccessMessage.LOGOUT_SUCCESS.value, status.HTTP_200_OK)
    else:
        raise HTTPException(status_code=400, detail=ErrorMessage.LOGOUT_FAILED.value)

@router.post("/refresh")
def refresh(refresh_token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), access_token: str = Depends(get_token_from_header)):
    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail=ErrorMessage.INVALID_TOKEN.value)

    # blacklist the old access token if it is not blacklisted
    try:
        blacklist_token(access_token, db)
    except:
        pass

    access_token = create_access_token(user_id)
    user_response = UserResponse.model_validate(current_user)
    return_data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user_response,
    }
    return response_schema(return_data, SuccessMessage.LOGIN_SUCCESS.value, status.HTTP_200_OK)


@router.post("/super-admin-signup", response_model=UserResponse)
def super_admin_signup(payload: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, ErrorMessage.EMAIL_ALREADY_EXISTS.value)

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_id=GlobalConstants.SUPERADMIN_ROLE_ID
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user