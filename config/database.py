# config/database.py - 데이터베이스 설정

import os
import motor.motor_asyncio

# MongoDB 설정
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@192.168.0.199:27017")
DB_NAME = "test"
COLLECTION_NAME = "fridge_ingredients"

def init_mongodb():
    """MongoDB 초기화"""
    print("\n--- MongoDB Setup ---")
    if MONGODB_URI:
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True,
                retryReads=True,
                maxPoolSize=10,
                minPoolSize=1
            )
            db = client[DB_NAME]
            fridge_collection = db[COLLECTION_NAME]
            print(f"✓ MongoDB connection configured")
            print(f"  URI: {MONGODB_URI}")
            print(f"  Database: {DB_NAME}")
            print(f"  Collection: {COLLECTION_NAME}")
            return client, db, fridge_collection
        except Exception as e:
            print(f"✗ MongoDB client creation failed: {e}")
            return None, None, None
    else:
        print("✗ MONGODB_URI not set - MongoDB features disabled")
        return None, None, None