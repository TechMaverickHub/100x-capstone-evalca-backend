# app/jwt_utils.py
import os

import jwt
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from auth.model import BlacklistedToken

load_dotenv()
SECRET = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE = 3600   # 1 hour
REFRESH_TOKEN_EXPIRE = 7*24*3600  # 7 days

def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET, algorithm="HS256")

def create_refresh_token(user_id: int):
    expire = datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRE)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET, algorithm="HS256")

def verify_access_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        blacklisted = db.query(BlacklistedToken).filter_by(token=token).first()
        if blacklisted:
            return None
        return int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def blacklist_token(token: str, db: Session):

    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"])

        # Save token to blacklist
        blacklisted = BlacklistedToken(token=token, expires_at=exp)
        db.add(blacklisted)
        db.commit()
        return True

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    except Exception as e:
        return None

def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        return int(payload.get("sub"))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
