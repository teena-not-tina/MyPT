from fastapi import APIRouter
import asyncio
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from urllib.parse import unquote
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB 설정
MONGO_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client.test  # MongoDB 데이터베이스 이름
user_stats_collection = db.users

# 스케줄러 인스턴스
scheduler = AsyncIOScheduler()

# 사용자 통계 모델
class UserStats(BaseModel):
    user_id: str
    progress: int = 0
    level: int = 4  # 기본값 4 (1~7 범위)
    created_at: datetime
    updated_at: datetime

async def weekly_update_task():
    """일주일마다 실행되는 업데이트 작업"""
    try:
        logger.info("Starting weekly update task...")
        
        # 모든 사용자의 통계 정보 가져오기
        cursor = user_stats_collection.find({})
        user_stats = await cursor.to_list(length=None)
        
        updated_count = 0
        
        for user_stat in user_stats:
            current_progress = user_stat.get('progress', 0)
            current_character = user_stat.get('level', 4)  # 기본값 4
            new_character = current_character
            
            # level 값에 따른 character 업데이트 로직
            if current_progress >= 4:
                new_character = min(current_character + 1, 7)  # 최댓값 7로 제한
                logger.info(f"User {user_stat['user_id']}: level {current_progress} >= 4, character {current_character} -> {new_character} (+1)")
            elif current_progress == 0:
                new_character = max(current_character - 1, 1)  # 최솟값 1로 제한
                logger.info(f"User {user_stat['user_id']}: level {current_progress} == 0, character {current_character} -> {new_character} (-1)")
            elif 1 <= current_progress <= 3:
                # character 값 유지
                logger.info(f"User {user_stat['user_id']}: level {current_progress} (1-3), character {current_character} maintained")
            
            # character 값이 변경된 경우에만 업데이트
            if new_character != current_character:
                await user_stats_collection.update_one(
                    {"_id": user_stat["_id"]},
                    {
                        "$set": {
                            "level": new_character,
                            "updated_at": datetime.now()
                        }
                    }
                )
                updated_count += 1
            # level을 0으로 초기화
            await user_stats_collection.update_one(
                {"_id": user_stat["_id"]},
                {
                    "$set": {
                        "progress": 0,
                        "updated_at": datetime.now()
                    }
                }
            )
        
        logger.info(f"Weekly update task completed. Updated {updated_count} users.")
        
    except Exception as e:
        logger.error(f"Error in weekly update task: {str(e)}")

# FastAPI 앱 생명주기 관리
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 앱 시작 시
    logger.info("Starting scheduler...")
    
    # 매주 월요일 00:00에 실행 (일요일 -> 월요일 전환 시점)
    scheduler.add_job(
        weekly_update_task,
        CronTrigger(day_of_week=0, hour=0, minute=0),  # 0 = 월요일
        id="weekly_update",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    yield
    
    # 앱 종료 시
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()

# FastAPI 앱 생성
app = FastAPI(lifespan=app_lifespan, title="User Stats Scheduler", version="1.0.0")

# ---------------------------------------------------------------------------------------

# 사용자 통계 초기화/조회 엔드포인트
@router.post("/init-user-stats")
async def init_user_stats(user_id: str, initial_level: int = 0, initial_character: int = 4):
    """사용자 통계 초기화"""
    # character 값 유효성 검사
    if not (1 <= initial_character <= 7):
        raise HTTPException(status_code=400, detail="Character value must be between 1 and 7")
    
    existing = await user_stats_collection.find_one({"user_id": user_id})
    
    if existing:
        return {
            "message": "User stats already exist", 
            "email": user_id, 
            "progress": existing["progress"],
            "level": existing.get("level", 4)
        }
    
    user_stat = UserStats(
        user_id=user_id,
        progress=initial_level,
        level=initial_character,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    result = await user_stats_collection.insert_one(user_stat.dict())
    
    return {
        "message": "User stats initialized",
        "user_id": user_id,
        "progress": initial_level,
        "level": initial_character,
        "stats_id": str(result.inserted_id)
    }

@router.get("/get-user-stats/{user_id}")
async def get_user_stats(user_id: str):
    """사용자 통계 조회"""
    # URL 디코딩 추가
    decoded_user_id = unquote(user_id)
    logger.info(f"Original user_id: {user_id}, Decoded user_id: {decoded_user_id}")
    
    user_stat = await user_stats_collection.find_one({"email": decoded_user_id})
    
    if not user_stat:
        raise HTTPException(status_code=404, detail=f"User stats not found for user_id: {decoded_user_id}")
    
    user_stat["_id"] = str(user_stat["_id"])
    return user_stat

@router.put("/update-user-character/{user_id}")
async def update_user_character(user_id: str, new_level: int):
    """사용자 character 수동 업데이트"""
    # URL 디코딩 추가
    decoded_user_id = unquote(user_id)
    logger.info(f"Original user_id: {user_id}, Decoded user_id: {decoded_user_id}")

    # character 값 유효성 검사
    if not (1 <= new_level <= 7):
        raise HTTPException(status_code=400, detail="Character value must be between 1 and 7")
    
    result = await user_stats_collection.update_one(
        {"email": decoded_user_id},
        {
            "$set": {
                "level": new_level,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User stats not found")
    
    return {"message": "User level updated", "user_id": user_id, "new_level": new_level}

@router.put("/update-user-level/{user_id}")
async def update_user_level(user_id: str, new_progress: int):
    """사용자 level 수동 업데이트"""
    # URL 디코딩 추가
    decoded_user_id = unquote(user_id)
    logger.info(f"Original user_id: {user_id}, Decoded user_id: {decoded_user_id}")

    result = await user_stats_collection.update_one(
        {"user_id": decoded_user_id},
        {
            "$set": {
                "progress": new_progress,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User stats not found")
    
    return {"message": "User progress updated", "user_id": user_id, "new_progress": new_progress}

# 수동으로 주간 업데이트 실행하는 엔드포인트 (테스트용)
@router.get("/trigger-weekly-update")
async def trigger_weekly_update():
    """수동으로 주간 업데이트 실행 (테스트용)"""
    await weekly_update_task()
    return {"message": "Weekly update task executed"}

# 스케줄러 상태 확인 엔드포인트
@router.get("/scheduler-status")
async def get_scheduler_status():
    """스케줄러 상태 확인"""
    jobs = scheduler.get_jobs()
    return {
        "scheduler_running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ]
    }


