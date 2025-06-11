# modules/auth/routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from mongodb import get_database
from models import User, UserCreate, Token, UserLogin
from datetime import timedelta
from dependencies import get_user, get_current_user, get_random_user_id
from utils import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

@router.post("/signup", response_model=User)
async def signup(user_create: UserCreate):
    """Create a new user account"""
    db = await get_database()
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = await get_random_user_id()
    hashed_password = get_password_hash(user_create.password)
    
    new_user = {
        "user_id": user_id,
        "email": user_create.email,
        "password": hashed_password,
        "level": 4,  # Default level
        "progress": 0  # Default progress
    }
    
    await users_collection.insert_one(new_user)
    
    return User(
        email=new_user["email"],
        user_id=new_user["user_id"],
        level=new_user["level"],
        progress=new_user["progress"]
    )

# @router.post("/login", response_model=Token)
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     """Login with email and password"""
#     # OAuth2PasswordRequestForm uses 'username' field, but we use email
#     user = await get_user(form_data.username)
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
async def login_json(user_login: UserLogin):
    """Login with email and password (JSON body instead of form data)"""
    
    user = await get_user(user_login.email)
    print(f"User found: {user}")  # Debugging line to check user retrieval
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.user_id},  # Include user_id in token data
        expires_delta=access_token_expires
    )
    print(f"Access token created: {access_token}")
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user.user_id,
        "email": user.email
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return User(
        email=current_user.email,
        user_id=current_user.user_id,
        level=current_user.level,
        progress=current_user.progress
    )

@router.post("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "email": current_user.email}