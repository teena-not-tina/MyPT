from fastapi import FastAPI
from models import MsgPayload
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from stable_diffusion import contact_comfyui, character_update
from stable_diffusion.img_output import get_current_img
import routes
from contextlib import asynccontextmanager
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv

# MongoDB 설정
MONGO_URL = "mongodb://root:example@192.168.0.199:27017/?authSource=admin"
# MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.test  # MongoDB 데이터베이스 이름
users_collection = db.users

app = FastAPI()

messages_list: dict[int, MsgPayload] = {}

# CORS 설정 (React 앱에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contact_comfyui.router, prefix="")
app.include_router(character_update.router, prefix="")
app.include_router(get_current_img.router, prefix="")
app.include_router(routes.router, prefix="")

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello"}


# About page route
@app.get("/about")
def about() -> dict[str, str]:
    return {"message": "This is the about page."}


# Route to add a message
@app.post("/messages/{msg_name}/")
def add_msg(msg_name: str) -> dict[str, MsgPayload]:
    # Generate an ID for the item based on the highest ID in the messages_list
    msg_id = max(messages_list.keys()) + 1 if messages_list else 0
    messages_list[msg_id] = MsgPayload(msg_id=msg_id, msg_name=msg_name)

    return {"message": messages_list[msg_id]}


# Route to list all messages
@app.get("/messages")
def message_items() -> dict[str, dict[int, MsgPayload]]:
    return {"messages:": messages_list}

# @app.post("/login")
# def login(username: str, password: str) -> dict[str, str]:
#     user = await users_collection.find_one({"email": username, "password": password})
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid username or password")
#     return {"message": "Login successful", "user_id": str(user["_id"])}


async def get_database():
    """Get database instance"""
    return db

async def connect_to_mongo():
    """Create database connection"""
    global client, db
    # client = AsyncIOMotorClient(MONGO_URL)
    # db = client[DATABASE_NAME]
    print(f"Connected to MongoDB at {MONGO_URL}")

async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")
