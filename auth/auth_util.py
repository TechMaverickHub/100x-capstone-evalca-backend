from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth.model import User
from core.global_constants import ErrorMessage, ErrorKeys
from core.jwt_utils import verify_access_token
from core.utils import response_schema
from database.session import get_db

# Swagger will now show simple "Authorize" for Bearer token
bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),db: Session = Depends(get_db)):
    token = credentials.credentials
    user_id = verify_access_token(token,db)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    user = db.query(User).filter(User.id == user_id,User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

def get_token_from_header(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=ErrorMessage.AUTHORIZATION_HEADER_MISSING_OR_INVALID.value)
    return auth_header.split("Bearer ")[1]


def require_role(role_id: int):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role_id != role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorMessage.NOT_AUTHORIZED.value
            )
        return current_user

    return role_checker
