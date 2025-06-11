from typing import Optional
from pydantic import BaseModel

# modules/auth/models.py

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    user_id: int
    email: str
    hashed_password: str  # password → hashed_password로 변경
    level: int = 4
    progress: int = 0

class User(UserBase):
    user_id: int
    level: int
    progress: int

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str

class TokenData(BaseModel):
    email: Optional[str] = None



class MsgPayload(BaseModel):
    msg_id: Optional[int]
    msg_name: str
