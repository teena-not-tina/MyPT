from fastapi import APIRouter
from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import base64
from typing import Optional
import os
import jwt
from dotenv import load_dotenv
from urllib.parse import unquote
import bson
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()
security = HTTPBearer()

# MongoDB 연결 설정
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME_USER_IMAGE = os.getenv("DATABASE_NAME_USER_IMAGE", "user_image")
DATABASE_NAME_USER_STATS = os.getenv("DATABASE_NAME_USER_STATS", "user_stats")

# MongoDB 클라이언트 초기화
client = None
db_user_image = None
db_user_stats = None


# Character 값과 Tag 매핑
CHARACTER_TAG_MAPPING = {
    1: "very fat",
    2: "fat", 
    3: "a little fat",
    4: "average",
    5: "slightly muscular",
    6: "muscular",
    7: "very muscular"
}





async def get_database_connection():
    """MongoDB 연결을 초기화하고 반환"""
    global client, db_user_image, db_user_stats
    
    if client is None:
        try:
            client = AsyncIOMotorClient(MONGODB_URL)
            # 연결 테스트
            await client.admin.command('ping')
            
            db_user_image = client[DATABASE_NAME_USER_IMAGE]
            db_user_stats = client[DATABASE_NAME_USER_STATS]
            
            logger.info("MongoDB 연결 성공")
        except Exception as e:
            logger.error(f"MongoDB 연결 실패: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    return db_user_image, db_user_stats

@router.get("/")
async def root():
    return {"message": "FastAPI MongoDB Image Server"}


@router.get("/user/{user_id}/image")
async def get_user_image(user_id: int):
    """
    user_id를 기반으로 user_stat의 character 값에 따라 
    food 필드가 있으면 food 이미지를, 없으면 images 딕셔너리에서 반환
    """
    # decoded_user_id = unquote(user_id)
    logger.info(f"이미지 요청: user_id={user_id}")

    try:
        db_user_image, db_user_stats = await get_database_connection()
        
        # 1. user_stat에서 character 값 조회
        user_stat = await db_user_stats.users.find_one({"user_id": user_id})
        if not user_stat:
            logger.warning(f"사용자 통계 정보 없음: {user_id}")
            raise HTTPException(status_code=404, detail="User stat not found")
        
        character = user_stat.get("level")
        if not character or character not in CHARACTER_TAG_MAPPING:
            logger.warning(f"잘못된 level 값: {character}")
            raise HTTPException(status_code=400, detail="Invalid character value")
        
        required_tag = CHARACTER_TAG_MAPPING[character]
        logger.info(f"태그 매핑: character={character} -> tag={required_tag}")
        
        # 2. user_image에서 이미지 조회
        user_img_doc = await db_user_image.user_image.find_one({
            "user_id": user_id
        })
        if not user_img_doc:
            logger.warning(f"이미지 없음: user_id={user_id}")
            raise HTTPException(status_code=404, detail="Image not found for user {decoded_user_id}")

        # 2-1. 최상위 food 필드 우선 반환
        if "food" in user_img_doc and user_img_doc["food"]:
            image_info = user_img_doc["food"]
            tag_used = "food"
        # 2-2. images 딕셔너리에서 tag로 반환
        elif "images" in user_img_doc and required_tag in user_img_doc["images"]:
            image_info = user_img_doc["images"][required_tag]
            tag_used = required_tag
        else:
            logger.warning(f"이미지 없음: user_id={user_id}, tag={required_tag} 또는 food")
            raise HTTPException(
                status_code=404, 
                detail=f"Image not found for user {user_id} with tag '{required_tag}' or 'food'"
            )

        image_data = image_info.get("image_data")
        if not image_data:
            raise HTTPException(status_code=404, detail="Image data not found")

        # Binary 타입이면 bytes로 변환해서 base64 인코딩
        if isinstance(image_data, bson.binary.Binary):
            base64_image = base64.b64encode(bytes(image_data)).decode('utf-8')
        # 이미 str이면 그대로 사용
        elif isinstance(image_data, str):
            base64_image = image_data
        # bytes 타입이면 인코딩
        elif isinstance(image_data, bytes):
            base64_image = base64.b64encode(image_data).decode('utf-8')
        else:
            raise HTTPException(status_code=500, detail="Unsupported image_data type")

        
        logger.info(f"이미지 반환 성공: user_id={user_id}, tag={tag_used}")
        return {
            "user_id": user_id,
            "character": character,
            "tag": tag_used,
            "image_data": base64_image,
            "image_format": image_info.get("content_type", "image/png")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
     
@router.get("/user/{user_id}/image/direct")
async def get_user_image_direct(user_id: int):
    """
    이미지를 직접 반환 (img src로 사용 가능)
    """
    # decoded_user_id = unquote(user_id)
    
    try:
        db_user_image, db_user_stats = await get_database_connection()
        
        # user_stats에서 character 값 조회
        user_stat = await db_user_stats.users.find_one({"user_id": user_id})
        
        if not user_stat:
            raise HTTPException(status_code=404, detail="User stat not found")
        
        character = user_stat.get("level")
        if not character or character not in CHARACTER_TAG_MAPPING:
            raise HTTPException(status_code=400, detail="Invalid character value")
        
        required_tag = CHARACTER_TAG_MAPPING[character]
        
        # user_image에서 이미지 조회
        user_img = await db_user_image.user_results.find_one({
            "user_id": user_id,
            "tag": required_tag
        })
        
        if not user_img:
            raise HTTPException(
                status_code=404, 
                detail=f"Image not found for user {user_id} with tag '{required_tag}'"
            )
        
        image_data = user_img.get("image_data")
        if not image_data:
            raise HTTPException(status_code=404, detail="Image data not found")
        
        # 이미지 포맷 결정 (기본값: jpeg)
        image_format = user_img.get("image_format", "jpeg")
        media_type = f"image/{image_format}"
        
        return Response(content=image_data, media_type=media_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"직접 이미지 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/user/{user_id}/character-info")
async def get_user_character_info(user_id: str):
    """
    사용자의 character 정보와 해당하는 tag 정보를 반환
    """
    decoded_user_id = unquote(user_id)
    
    try:
        db_user_image, db_user_stats = await get_database_connection()
        
        user_stat = await db_user_stats.users.find_one({"user_id": decoded_user_id})
        
        if not user_stat:
            raise HTTPException(status_code=404, detail="User stat not found")
        
        character = user_stat.get("level")
        if not character or character not in CHARACTER_TAG_MAPPING:
            raise HTTPException(status_code=400, detail="Invalid level value")
        
        return {
            "user_id": decoded_user_id,
            "character": character,
            "tag": CHARACTER_TAG_MAPPING[character],
            "all_mappings": CHARACTER_TAG_MAPPING
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캐릭터 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @router.get("/api/user/profile")
# async def get_user_profile(user_id: int = Depends(verify_token)):
#     """사용자 프로필 정보 조회"""
#     try:
#         db_user_image, db_user_stats = await get_database_connection()
#         # users 컬렉션으로 명확히 지정
#         users_collection = db_user_stats.users

#         # 사용자의 모든 생성된 이미지 수 조회
#         total_images = await users_collection.count_documents({"user_id": user_id})
        
#         # 가장 최근 생성 날짜 조회
#         latest_creation = await users_collection.find_one(
#             {"user_id": user_id},
#             sort=[("created_at", -1)]
#         )
        
#         return {
#             "user_id": user_id,
#             "total_images": total_images,
#             "latest_creation": latest_creation.get("created_at") if latest_creation else None
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



# @router.get("/api/user/profile")
# async def get_user_profile(user_id: int = Depends(verify_token)):
#     """사용자 프로필 정보 조회"""
#     try:
#         # 사용자의 모든 생성된 이미지 수 조회
#         total_images = await db_user_stats.count_documents({"user_id": user_id})
        
#         # 가장 최근 생성 날짜 조회
#         latest_creation = await db_user_stats.find_one(
#             {"user_id": user_id},
#             sort=[("created_at", -1)]
#         )
        
#         return {
#             "user_id": user_id,
#             "total_images": total_images,
#             "latest_creation": latest_creation.get("created_at") if latest_creation else None
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)