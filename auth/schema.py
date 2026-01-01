from pydantic import BaseModel
from pydantic import EmailStr


# Signup payload
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


# Login payload
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Response payload after login (JWT + refresh token)
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Response payload for user details
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role_id: int

    model_config = {
        "from_attributes": True
    }
