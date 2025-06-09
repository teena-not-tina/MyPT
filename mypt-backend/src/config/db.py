# src/config/db.py (데이터베이스 연결 설정)
from pymongo import MongoClient
import time

MONGO_URI = "mongodb://root:example@192.168.0.199:27017/?authSource=admin"
DB_NAME = "test"

_mongo_client = None

def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI)
    return _mongo_client

def get_mongo_collection(collection_name):
    try:
        client = get_mongo_client()
        db = client[DB_NAME]
        return db[collection_name]
    except Exception as e:
        print(f"MongoDB 연결 오류: {str(e)}")
        raise e

def test_connection():
    try:
        client = get_mongo_client()
        db = client[DB_NAME]
        db.command('ping')
        print(f"MongoDB 연결 성공: {MONGO_URI}")
        return True
    except Exception as e:
        print(f"MongoDB 연결 실패: {str(e)}")
        return False

def connect_db():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        print(f"MongoDB 연결 성공: {MONGO_URI}")
        return db
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")
        return None

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def save_food_image(user_id, image_base64):
    try:
        collection = get_mongo_collection('user_image')
        
        # 기존 문서 찾기 또는 새로 생성
        document = collection.find_one({'user_id': user_id})
        
        if document:
            # 기존 문서 업데이트
            collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'images.food': {
                            'image_data': image_base64,
                            'created_at': time.time()
                        }
                    }
                }
            )
        else:
            # 새 문서 생성
            document = {
                'user_id': user_id,
                'images': {
                    'very fat': {},  # 기존 구조 유지
                    'food': {
                        'image_data': image_base64,
                        'created_at': time.time()
                    }
                }
            }
            collection.insert_one(document)
        
        print(f"이미지가 MongoDB에 저장됨 (user_id: {user_id})")
        return True
        
    except Exception as e:
        print(f"MongoDB 이미지 저장 실패: {e}")
        return False
