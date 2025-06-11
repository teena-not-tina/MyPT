from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# load_dotenv 함수 호출로 수정
load_dotenv()

# 환경 변수에서 MongoDB 설정 가져오기
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:example@192.168.0.199:27017/?authSource=admin")
DATABASE_NAME = os.getenv("DATABASE_NAME", "test")

client = None
db = None

async def get_database():
    """Get database instance"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    return db

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    print(f"Connected to MongoDB at {MONGODB_URL}")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")