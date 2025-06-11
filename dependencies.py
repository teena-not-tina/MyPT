# modules/auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from mongodb import get_database
from models import UserInDB, TokenData
from utils import decode_token
import random
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# async def get_user(email: str) -> UserInDB:
#     """Get user by email from database"""
#     db = await get_database()
#     users_collection = db["users"]
#     user = await users_collection.find_one({"email": email})
#     if user:
#         return UserInDB(**user)
#     return None
async def get_user(email: str):
    db = await get_database()
    user = await db["users"].find_one({"email": email})
    if user:
        user["hashed_password"] = user["password"]  # 해시된 비밀번호를 hashed_password로 복사
        return UserInDB(**user)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.JWTError:
        raise credentials_exception
    
    user = await get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_random_user_id() -> int:
    """Generate a random user_id that does not exist in the DB"""
    db = await get_database()
    users_collection = db["users"]
    max_attempts = 10
    for _ in range(max_attempts):
        user_id = random.randint(100000, 999999)  # 원하는 범위로 조정
        exists = await users_collection.find_one({"user_id": user_id})
        if not exists:
            return user_id
    raise Exception("Failed to generate a unique user_id after multiple attempts")