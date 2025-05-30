from dotenv import load_dotenv
import os

# .env 파일 로드 (가장 먼저 실행)
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import traceback
import motor.motor_asyncio
from datetime import datetime

# 기존 모듈들
from modules.yolo_detector import detect_objects, load_yolo_model
from modules.ocr_processor import extract_text_with_ocr
from modules.gemini import analyze_text_with_gemini

# FastAPI 앱 생성
app = FastAPI(title="Food Detection API", version="1.0.0")

# CORS 설정 강화
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.19:3000",
        "*"  # 개발 중에만 사용
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# MongoDB 설정 - 사용자 정의 설정
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@192.168.0.199:27017")
DB_NAME =  "test"  # 임시 DB명 (회의 후 변경)
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "be-fit")  # 냉장고 식재료 컬렉션

if MONGODB_URI:
    try:
        # 로컬 MongoDB 설정 (Docker나 로컬 설치)
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URI,
            # 로컬 MongoDB이므로 SSL 설정 불필요
            serverSelectionTimeoutMS=5000,   # 타임아웃 단축
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            # 재시도 설정
            retryWrites=True,
            retryReads=True,
            # 연결 풀 설정
            maxPoolSize=10,
            minPoolSize=1
        )
        
        # 사용자 정의 데이터베이스와 컬렉션 사용
        db = client[DB_NAME]
        fridge_collection = db[COLLECTION_NAME]
        
        print(f"✅ MongoDB 연결 설정 완료")
        print(f"📍 URI: {MONGODB_URI}")
        print(f"🗄️ 데이터베이스: {DB_NAME}")
        print(f"📊 컬렉션: {COLLECTION_NAME}")
        
    except Exception as e:
        print(f"❌ MongoDB 클라이언트 생성 실패: {e}")
        client = None
        db = None
        fridge_collection = None
else:
    print("⚠️ MONGODB_URI가 설정되지 않음 - MongoDB 기능 비활성화")
    client = None
    db = None
    fridge_collection = None

# Pydantic 모델 정의 (냉장고 식재료 데이터용)
class Ingredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: Optional[float] = 0.8
    source: str = "analysis"  # detection, ocr, ocr_smart, analysis
    bbox: Optional[List[float]] = None  # YOLO bbox 정보
    originalClass: Optional[str] = None  # 원본 영어 클래스명
    
    class Config:
        from_attributes = True

class FridgeData(BaseModel):
    userId: str
    ingredients: List[Ingredient]
    timestamp: str
    totalCount: int
    totalTypes: int
    analysisMethod: Optional[str] = "mixed"  # detection, ocr, mixed
    deviceInfo: Optional[str] = None  # 기기 정보
    
    class Config:
        from_attributes = True

# YOLO 모델 로드
print("YOLO 모델 로딩 중...")
model = load_yolo_model()
print("✅ YOLO 모델 로드 성공" if model else "❌ YOLO 모델 로드 실패")

# 환경 변수 확인
print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"MONGODB_URI 설정: {bool(MONGODB_URI)}")

@app.get("/")
async def root():
    return {
        "message": "Food Detection API with Custom MongoDB",
        "status": "running",
        "model_loaded": model is not None,
        "mongodb_connected": fridge_collection is not None,
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri_host": MONGODB_URI.split('@')[1] if '@' in MONGODB_URI else "unknown"
        },
        "env_vars": {
            "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
            "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
            "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
            "mongodb_uri": bool(MONGODB_URI)
        }
    }

# ===== 기존 API 엔드포인트들 =====

@app.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.5):
    """YOLO 식품 탐지"""
    if model is None:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"📁 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"🔍 YOLO 탐지 시작 (신뢰도: {confidence})")
        detections, _ = detect_objects(model, image_path, confidence)
        print(f"✅ 탐지 완료: {len(detections)}개 객체")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {"detections": detections}
        
    except Exception as e:
        print(f"❌ 탐지 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")

@app.post("/api/ocr")
async def extract_ocr_text(file: UploadFile = File(...)):
    """OCR 텍스트 추출"""
    try:
        print(f"📁 OCR 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"📄 OCR 텍스트 추출 시작")
        ocr_text = extract_text_with_ocr(image_path)
        print(f"✅ OCR 완료: {len(ocr_text) if ocr_text else 0}자")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {"text": ocr_text}
        
    except Exception as e:
        print(f"❌ OCR 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR 오류: {str(e)}")

@app.post("/api/analyze")
async def analyze_with_gemini(request_data: dict):
    """Gemini AI 분석"""
    try:
        text = request_data.get("text", "")
        detection_results = request_data.get("detection_results")
        
        print(f"🧠 Gemini 분석 시작 - 텍스트 길이: {len(text)}")
        analysis = analyze_text_with_gemini(text, detection_results)
        print(f"✅ Gemini 분석 완료")
        
        return {"analysis": analysis}
        
    except Exception as e:
        print(f"❌ Gemini 분석 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini 분석 오류: {str(e)}")

# ===== MongoDB 냉장고 식재료 관리 API =====

@app.post("/api/fridge/save")
async def save_fridge_data(fridge_data: FridgeData):
    """냉장고 식재료 데이터를 MongoDB에 저장"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"💾 냉장고 데이터 저장 시작 - 사용자: {fridge_data.userId}")
        print(f"🗄️ 저장 위치: {DB_NAME}.{COLLECTION_NAME}")
        
        # Pydantic V2 호환: model_dump() 사용
        ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]
        
        # MongoDB 연결 상태 확인
        try:
            await client.admin.command('ping')
            print("✅ MongoDB 연결 상태 정상")
        except Exception as conn_err:
            print(f"❌ MongoDB 연결 확인 실패: {conn_err}")
            raise HTTPException(status_code=503, detail="MongoDB 연결이 불안정합니다")
        
        # 데이터 저장 (upsert: 없으면 생성, 있으면 업데이트)
        current_time = datetime.now().isoformat()
        
        # $set에는 업데이트할 필드들만 포함 (createdAt 제외)
        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "timestamp": fridge_data.timestamp,
            "totalCount": fridge_data.totalCount,
            "totalTypes": fridge_data.totalTypes,
            "analysisMethod": fridge_data.analysisMethod or "mixed",
            "deviceInfo": fridge_data.deviceInfo or "web_app",
            "updatedAt": current_time
        }
        
        # $setOnInsert에는 새 문서 생성 시에만 설정할 필드들
        insert_only_document = {
            "createdAt": current_time
        }
        
        result = await fridge_collection.update_one(
            {"userId": fridge_data.userId},
            {
                "$set": update_document,
                "$setOnInsert": insert_only_document
            },
            upsert=True
        )
        
        print(f"✅ MongoDB 저장 완료")
        print(f"   - 사용자: {fridge_data.userId}")
        print(f"   - 식재료: {fridge_data.totalTypes}종류 {fridge_data.totalCount}개")
        print(f"   - 신규 생성: {result.upserted_id is not None}")
        
        return {
            "success": True,
            "message": f"냉장고 데이터가 {DB_NAME}.{COLLECTION_NAME}에 성공적으로 저장되었습니다",
            "userId": fridge_data.userId,
            "totalTypes": fridge_data.totalTypes,
            "totalCount": fridge_data.totalCount,
            "isNew": result.upserted_id is not None,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "documentId": str(result.upserted_id) if result.upserted_id else "updated"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ MongoDB 저장 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"저장 중 오류 발생: {str(e)}")

@app.get("/api/fridge/load/{user_id}")
async def load_fridge_data(user_id: str):
    """MongoDB에서 사용자별 냉장고 데이터 불러오기"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"📥 냉장고 데이터 로드 시작 - 사용자: {user_id}")
        print(f"🗄️ 검색 위치: {DB_NAME}.{COLLECTION_NAME}")
        
        # MongoDB에서 사용자 데이터 검색
        fridge_data = await fridge_collection.find_one({"userId": user_id})
        
        if not fridge_data:
            print(f"⚠️ 데이터 없음 - 사용자: {user_id}")
            return {
                "success": False,
                "message": "저장된 냉장고 데이터가 없습니다",
                "ingredients": [],
                "totalTypes": 0,
                "totalCount": 0,
                "storage": {
                    "database": DB_NAME,
                    "collection": COLLECTION_NAME
                }
            }
        
        # _id 필드 제거 (JSON 직렬화를 위해)
        fridge_data.pop("_id", None)
        
        print(f"✅ MongoDB 로드 완료")
        print(f"   - 사용자: {user_id}")
        print(f"   - 식재료: {fridge_data.get('totalTypes', 0)}종류")
        
        return {
            "success": True,
            "message": f"{DB_NAME}.{COLLECTION_NAME}에서 데이터를 성공적으로 불러왔습니다",
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            },
            **fridge_data
        }
    
    except Exception as e:
        print(f"❌ MongoDB 로드 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"데이터 로드 중 오류 발생: {str(e)}")

@app.get("/api/fridge/users")
async def get_all_users():
    """모든 사용자의 냉장고 데이터 목록 조회 (관리용)"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"👥 전체 사용자 목록 조회 - {DB_NAME}.{COLLECTION_NAME}")
        
        users = await fridge_collection.find(
            {}, 
            {
                "userId": 1, 
                "totalTypes": 1, 
                "totalCount": 1, 
                "timestamp": 1, 
                "updatedAt": 1,
                "analysisMethod": 1,
                "deviceInfo": 1
            }
        ).to_list(length=None)
        
        # _id 필드 제거
        for user in users:
            user.pop("_id", None)
        
        print(f"✅ 사용자 목록 조회 완료 - 총 {len(users)}명")
        
        return {
            "success": True,
            "users": users,
            "totalUsers": len(users),
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            }
        }
    
    except Exception as e:
        print(f"❌ 사용자 목록 조회 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 중 오류 발생: {str(e)}")

@app.delete("/api/fridge/delete/{user_id}")
async def delete_fridge_data(user_id: str):
    """특정 사용자의 냉장고 데이터 삭제"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"🗑️ 데이터 삭제 시작 - 사용자: {user_id}")
        
        result = await fridge_collection.delete_one({"userId": user_id})
        
        if result.deleted_count == 0:
            print(f"⚠️ 삭제할 데이터 없음 - 사용자: {user_id}")
            raise HTTPException(status_code=404, detail="삭제할 냉장고 데이터가 없습니다")
        
        print(f"✅ 데이터 삭제 완료 - 사용자: {user_id}")
        
        return {
            "success": True,
            "message": f"{DB_NAME}.{COLLECTION_NAME}에서 데이터가 성공적으로 삭제되었습니다",
            "userId": user_id,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 데이터 삭제 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"데이터 삭제 중 오류 발생: {str(e)}")

# ===== 통계 및 분석 API =====

@app.get("/api/fridge/stats")
async def get_fridge_stats():
    """냉장고 데이터 통계 조회"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print("📊 냉장고 데이터 통계 조회")
        
        # 기본 통계
        total_users = await fridge_collection.count_documents({})
        
        # 인기 식재료 통계 (집계 파이프라인)
        pipeline = [
            {"$unwind": "$ingredients"},
            {"$group": {
                "_id": "$ingredients.name",
                "count": {"$sum": "$ingredients.quantity"},
                "users": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        popular_ingredients = await fridge_collection.aggregate(pipeline).to_list(length=10)
        
        # 분석 방법별 통계
        method_stats = await fridge_collection.aggregate([
            {"$group": {
                "_id": "$analysisMethod",
                "count": {"$sum": 1}
            }}
        ]).to_list(length=None)
        
        return {
            "success": True,
            "statistics": {
                "totalUsers": total_users,
                "popularIngredients": popular_ingredients,
                "analysisMethodStats": method_stats
            },
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            }
        }
    
    except Exception as e:
        print(f"❌ 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류 발생: {str(e)}")

# ===== 임시 저장 기능 (MongoDB 문제 시 대안) =====

temp_storage = {}

@app.post("/api/fridge/save/temp")
async def save_fridge_data_temp(fridge_data: FridgeData):
    """임시 메모리 저장 (MongoDB 연결 실패 시 대안)"""
    try:
        print(f"💾 임시 저장 시작 - 사용자: {fridge_data.userId}")
        
        # 메모리에 저장
        temp_storage[fridge_data.userId] = {
            "ingredients": [ingredient.model_dump() for ingredient in fridge_data.ingredients],
            "timestamp": fridge_data.timestamp,
            "totalCount": fridge_data.totalCount,
            "totalTypes": fridge_data.totalTypes,
            "analysisMethod": fridge_data.analysisMethod,
            "updatedAt": datetime.now().isoformat()
        }
        
        print(f"✅ 임시 저장 완료 - 사용자: {fridge_data.userId}")
        
        return {
            "success": True,
            "message": "데이터가 임시로 저장되었습니다 (MongoDB 연결 후 동기화 필요)",
            "userId": fridge_data.userId,
            "totalTypes": fridge_data.totalTypes,
            "totalCount": fridge_data.totalCount,
            "storage": "temporary_memory"
        }
    
    except Exception as e:
        print(f"❌ 임시 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"임시 저장 오류: {str(e)}")

@app.get("/api/fridge/load/temp/{user_id}")
async def load_fridge_data_temp(user_id: str):
    """임시 저장된 데이터 불러오기"""
    if user_id not in temp_storage:
        return {
            "success": False,
            "message": "임시 저장된 데이터가 없습니다",
            "storage": "temporary_memory"
        }
    
    data = temp_storage[user_id]
    return {
        "success": True,
        "message": "임시 저장된 데이터를 불러왔습니다",
        "userId": user_id,
        "storage": "temporary_memory",
        **data
    }

# ===== 시스템 상태 확인 API =====

@app.get("/health")
async def health_check():
    """전체 시스템 상태 확인"""
    mongodb_status = "connected" if fridge_collection is not None else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "yolo_model": "loaded" if model else "error",
            "mongodb": mongodb_status,
            "ocr": "configured" if os.environ.get('CLOVA_OCR_API_URL') else "not_configured",
            "gemini": "configured" if os.environ.get('GEMINI_API_KEY') else "not_configured"
        },
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None
        },
        "temp_dir_exists": os.path.exists("temp")
    }

@app.get("/debug/env")
async def debug_env():
    """환경 변수 및 설정 상태 확인 (디버깅용)"""
    return {
        "environment_variables": {
            "clova_ocr_url": bool(os.environ.get('CLOVA_OCR_API_URL')),
            "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
            "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
            "mongodb_uri": bool(MONGODB_URI)
        },
        "mongodb_config": {
            "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None,
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "connected": fridge_collection is not None
        },
        "system_info": {
            "working_directory": os.getcwd(),
            "temp_directory": os.path.exists("temp"),
            "model_loaded": model is not None
        }
    }

@app.get("/api/fridge/test")
async def test_mongodb_connection():
    """MongoDB 연결 테스트"""
    if fridge_collection is None:
        return {
            "success": False,
            "message": "MongoDB 클라이언트가 초기화되지 않았습니다",
            "config": {
                "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None,
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            }
        }
    
    try:
        # 연결 테스트
        start_time = datetime.now()
        await client.admin.command('ping')
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 컬렉션 정보 조회
        doc_count = await fridge_collection.count_documents({})
        
        return {
            "success": True,
            "message": "MongoDB 연결이 정상입니다",
            "config": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "document_count": doc_count
            },
            "performance": {
                "response_time_ms": round(response_time, 2)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"MongoDB 연결 테스트 실패: {str(e)}",
            "error": str(e),
            "config": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            }
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Food Detection API 서버 시작 중...")
    print(f"📍 서버 주소: http://0.0.0.0:8000")
    print(f"📋 API 문서: http://0.0.0.0:8000/docs")
    print(f"🔗 MongoDB 연결: {'✅ 성공' if fridge_collection is not None else '❌ 실패'}")
    print(f"🗄️ 저장 위치: {DB_NAME}.{COLLECTION_NAME}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# # cv-service/main.py 기본
# from dotenv import load_dotenv
# import os

# # .env 파일 로드 (가장 먼저 실행)
# load_dotenv()

# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import shutil
# import traceback
# from modules.yolo_detector import detect_objects, load_yolo_model
# from modules.ocr_processor import extract_text_with_ocr
# from modules.gemini import analyze_text_with_gemini

# # FastAPI 앱 생성
# app = FastAPI(title="Food Detection API", version="1.0.0")

# # CORS 설정 강화
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",
#         "http://127.0.0.1:3000",
#         "http://192.168.0.19:3000",
#         "*"  # 개발 중에만 사용
#     ],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
# )

# # YOLO 모델 로드
# print("YOLO 모델 로딩 중...")
# model = load_yolo_model()
# print("✅ YOLO 모델 로드 성공" if model else "❌ YOLO 모델 로드 실패")

# # 환경 변수 확인
# print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
# print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
# print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")

# @app.get("/")
# async def root():
#     return {
#         "message": "Food Detection API",
#         "status": "running",
#         "model_loaded": model is not None,
#         "env_vars": {
#             "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
#             "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
#             "gemini_key": bool(os.environ.get('GEMINI_API_KEY'))
#         }
#     }

# @app.post("/api/detect")
# async def detect_food(file: UploadFile = File(...), confidence: float = 0.5):
#     """YOLO 식품 탐지"""
#     if model is None:
#         raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
#     try:
#         print(f"📁 파일 업로드: {file.filename}")
#         os.makedirs("temp", exist_ok=True)
#         image_path = f"temp/{file.filename}"
        
#         with open(image_path, "wb") as f:
#             shutil.copyfileobj(file.file, f)
        
#         print(f"🔍 YOLO 탐지 시작 (신뢰도: {confidence})")
#         detections, _ = detect_objects(model, image_path, confidence)
#         print(f"✅ 탐지 완료: {len(detections)}개 객체")
        
#         try:
#             os.remove(image_path)
#         except:
#             pass
        
#         return {"detections": detections}
        
#     except Exception as e:
#         print(f"❌ 탐지 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")

# @app.post("/api/ocr")
# async def extract_ocr_text(file: UploadFile = File(...)):
#     """OCR 텍스트 추출"""
#     try:
#         print(f"📁 OCR 파일 업로드: {file.filename}")
#         os.makedirs("temp", exist_ok=True)
#         image_path = f"temp/{file.filename}"
        
#         with open(image_path, "wb") as f:
#             shutil.copyfileobj(file.file, f)
        
#         print(f"📄 OCR 텍스트 추출 시작")
#         ocr_text = extract_text_with_ocr(image_path)
#         print(f"✅ OCR 완료: {len(ocr_text) if ocr_text else 0}자")
        
#         try:
#             os.remove(image_path)
#         except:
#             pass
        
#         return {"text": ocr_text}
        
#     except Exception as e:
#         print(f"❌ OCR 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"OCR 오류: {str(e)}")

# @app.post("/api/analyze")
# async def analyze_with_gemini(request_data: dict):
#     """Gemini AI 분석"""
#     try:
#         text = request_data.get("text", "")
#         detection_results = request_data.get("detection_results")
        
#         print(f"🧠 Gemini 분석 시작 - 텍스트 길이: {len(text)}")
#         analysis = analyze_text_with_gemini(text, detection_results)
#         print(f"✅ Gemini 분석 완료")
        
#         return {"analysis": analysis}
        
#     except Exception as e:
#         print(f"❌ Gemini 분석 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Gemini 분석 오류: {str(e)}")

# # 추가 헬스체크 엔드포인트
# @app.get("/health")
# async def health_check():
#     """서버 상태 확인"""
#     return {
#         "status": "healthy",
#         "timestamp": os.environ.get("TZ", "UTC"),
#         "model_status": "loaded" if model else "error",
#         "temp_dir_exists": os.path.exists("temp")
#     }

# # 환경 변수 확인 엔드포인트 (디버깅용)
# @app.get("/debug/env")
# async def debug_env():
#     """환경 변수 상태 확인 (디버깅용)"""
#     return {
#         "clova_ocr_url": bool(os.environ.get('CLOVA_OCR_API_URL')),
#         "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
#         "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
#         "working_directory": os.getcwd(),
#         "temp_directory": os.path.exists("temp"),
#         "model_loaded": model is not None
#     }

# if __name__ == "__main__":
#     import uvicorn
#     print("🚀 서버 시작 중...")
#     print(f"📍 서버 주소: http://0.0.0.0:8000")
#     print(f"📋 API 문서: http://0.0.0.0:8000/docs")
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# #cv-service/main.py 몽고db저장버전1
# # MongoDB SSL 연결 오류 해결을 위한 수정된 main.py

# from dotenv import load_dotenv
# import os

# # .env 파일 로드 (가장 먼저 실행)
# load_dotenv()

# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Optional
# import shutil
# import traceback
# import motor.motor_asyncio
# from datetime import datetime
# import ssl

# # 기존 모듈들
# from modules.yolo_detector import detect_objects, load_yolo_model
# from modules.ocr_processor import extract_text_with_ocr
# from modules.gemini import analyze_text_with_gemini

# # FastAPI 앱 생성
# app = FastAPI(title="Food Detection API", version="1.0.0")

# # CORS 설정 강화
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",
#         "http://127.0.0.1:3000",
#         "http://192.168.0.19:3000",
#         "*"  # 개발 중에만 사용
#     ],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
# )

# # MongoDB 설정 - SSL 문제 해결
# MONGODB_URI = os.getenv("MONGODB_URI")
# if MONGODB_URI:
#     try:
#         # SSL 설정을 통한 연결 개선
#         client = motor.motor_asyncio.AsyncIOMotorClient(
#             MONGODB_URI,
#             # SSL 연결 문제 해결을 위한 설정들
#             tls=True,
#             tlsAllowInvalidCertificates=True,  # 개발 환경에서만 사용
#             tlsAllowInvalidHostnames=True,     # 개발 환경에서만 사용
#             serverSelectionTimeoutMS=10000,   # 타임아웃 단축
#             connectTimeoutMS=10000,
#             socketTimeoutMS=10000,
#             # 재시도 설정
#             retryWrites=True,
#             retryReads=True,
#             # 연결 풀 설정
#             maxPoolSize=10,
#             minPoolSize=1
#         )
        
#         db = client.food_detection_db
#         fridge_collection = db.fridge_data
#         print("✅ MongoDB 연결 설정 완료")
        
#         # 연결 테스트를 별도로 수행
#         async def test_connection():
#             try:
#                 await client.admin.command('ping')
#                 print("✅ MongoDB 연결 테스트 성공")
#                 return True
#             except Exception as e:
#                 print(f"❌ MongoDB 연결 테스트 실패: {e}")
#                 return False
        
#     except Exception as e:
#         print(f"❌ MongoDB 클라이언트 생성 실패: {e}")
#         client = None
#         db = None
#         fridge_collection = None
# else:
#     print("⚠️ MONGODB_URI가 설정되지 않음 - MongoDB 기능 비활성화")
#     client = None
#     db = None
#     fridge_collection = None

# # Pydantic 모델 정의 (냉장고 데이터용) - V2 호환
# class Ingredient(BaseModel):
#     id: int
#     name: str
#     quantity: int
#     confidence: Optional[float] = 0.8
#     source: str = "analysis"
    
#     class Config:
#         # Pydantic V2 호환성을 위한 설정
#         from_attributes = True

# class FridgeData(BaseModel):
#     userId: str
#     ingredients: List[Ingredient]
#     timestamp: str
#     totalCount: int
#     totalTypes: int
    
#     class Config:
#         from_attributes = True

# # YOLO 모델 로드
# print("YOLO 모델 로딩 중...")
# model = load_yolo_model()
# print("✅ YOLO 모델 로드 성공" if model else "❌ YOLO 모델 로드 실패")

# # 환경 변수 확인
# print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
# print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
# print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")
# print(f"MONGODB_URI 설정: {bool(os.environ.get('MONGODB_URI'))}")

# @app.get("/")
# async def root():
#     return {
#         "message": "Food Detection API with MongoDB",
#         "status": "running",
#         "model_loaded": model is not None,
#         "mongodb_connected": fridge_collection is not None,
#         "env_vars": {
#             "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
#             "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
#             "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
#             "mongodb_uri": bool(os.environ.get('MONGODB_URI'))
#         }
#     }

# # ===== MongoDB 관련 API 엔드포인트 - SSL 문제 해결 버전 =====

# @app.post("/api/fridge/save")
# async def save_fridge_data(fridge_data: FridgeData):
#     """냉장고 데이터 MongoDB에 저장 - SSL 문제 해결 버전"""
#     if fridge_collection is None:
#         raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
#     try:
#         print(f"💾 냉장고 데이터 저장 시작 - 사용자: {fridge_data.userId}")
        
#         # Pydantic V2 호환: model_dump() 사용
#         ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]
        
#         # MongoDB 연결 재확인
#         try:
#             await client.admin.command('ping')
#             print("✅ MongoDB 연결 상태 양호")
#         except Exception as conn_err:
#             print(f"❌ MongoDB 연결 확인 실패: {conn_err}")
#             # 연결 재시도
#             try:
#                 await client.close()
#                 print("🔄 MongoDB 연결 재시도 중...")
#                 # 새 클라이언트 생성은 하지 않고, 기존 연결 재사용 시도
#                 await client.admin.command('ping')
#                 print("✅ MongoDB 재연결 성공")
#             except:
#                 raise HTTPException(status_code=503, detail="MongoDB 연결이 불안정합니다. 잠시 후 다시 시도해주세요.")
        
#         # 기존 데이터 업데이트 또는 새로 생성
#         result = await fridge_collection.update_one(
#             {"userId": fridge_data.userId},
#             {
#                 "$set": {
#                     "ingredients": ingredients_dict,
#                     "timestamp": fridge_data.timestamp,
#                     "totalCount": fridge_data.totalCount,
#                     "totalTypes": fridge_data.totalTypes,
#                     "updatedAt": datetime.now().isoformat()
#                 }
#             },
#             upsert=True
#         )
        
#         print(f"✅ MongoDB 저장 완료 - 사용자: {fridge_data.userId}, 식재료: {fridge_data.totalTypes}종류")
        
#         return {
#             "success": True,
#             "message": "냉장고 데이터가 성공적으로 저장되었습니다",
#             "userId": fridge_data.userId,
#             "totalTypes": fridge_data.totalTypes,
#             "totalCount": fridge_data.totalCount,
#             "isNew": result.upserted_id is not None
#         }
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ MongoDB 저장 오류: {e}")
#         traceback.print_exc()
        
#         # SSL 관련 오류인 경우 특별 처리
#         if "SSL" in str(e) or "TLS" in str(e):
#             raise HTTPException(
#                 status_code=503, 
#                 detail="MongoDB SSL 연결 오류가 발생했습니다. 네트워크 연결을 확인하고 잠시 후 다시 시도해주세요."
#             )
#         else:
#             raise HTTPException(status_code=500, detail=f"저장 중 오류 발생: {str(e)}")

# # MongoDB 연결 상태를 지속적으로 모니터링하는 헬스체크
# @app.get("/api/fridge/health")
# async def mongodb_health_check():
#     """MongoDB 연결 상태 상세 확인"""
#     if fridge_collection is None:
#         return {
#             "mongodb_connected": False,
#             "error": "MongoDB 클라이언트가 초기화되지 않았습니다",
#             "mongodb_uri_set": bool(os.environ.get('MONGODB_URI'))
#         }
    
#     try:
#         # 단순한 ping 명령으로 연결 확인
#         start_time = datetime.now()
#         await client.admin.command('ping')
#         response_time = (datetime.now() - start_time).total_seconds() * 1000
        
#         return {
#             "mongodb_connected": True,
#             "response_time_ms": round(response_time, 2),
#             "database": db.name,
#             "collection": fridge_collection.name,
#             "status": "healthy"
#         }
    
#     except Exception as e:
#         return {
#             "mongodb_connected": False,
#             "error": str(e),
#             "error_type": type(e).__name__,
#             "status": "unhealthy"
#         }

# # 임시 저장 기능 (MongoDB 문제 시 대안)
# temp_storage = {}

# @app.post("/api/fridge/save/temp")
# async def save_fridge_data_temp(fridge_data: FridgeData):
#     """임시 메모리 저장 (MongoDB 문제 시 대안)"""
#     try:
#         print(f"💾 임시 저장 시작 - 사용자: {fridge_data.userId}")
        
#         # 메모리에 저장
#         temp_storage[fridge_data.userId] = {
#             "ingredients": [ingredient.model_dump() for ingredient in fridge_data.ingredients],
#             "timestamp": fridge_data.timestamp,
#             "totalCount": fridge_data.totalCount,
#             "totalTypes": fridge_data.totalTypes,
#             "updatedAt": datetime.now().isoformat()
#         }
        
#         print(f"✅ 임시 저장 완료 - 사용자: {fridge_data.userId}")
        
#         return {
#             "success": True,
#             "message": "데이터가 임시로 저장되었습니다 (MongoDB 연결 후 동기화 필요)",
#             "userId": fridge_data.userId,
#             "totalTypes": fridge_data.totalTypes,
#             "totalCount": fridge_data.totalCount,
#             "storage": "temporary"
#         }
    
#     except Exception as e:
#         print(f"❌ 임시 저장 오류: {e}")
#         raise HTTPException(status_code=500, detail=f"임시 저장 오류: {str(e)}")

# @app.get("/api/fridge/load/temp/{user_id}")
# async def load_fridge_data_temp(user_id: str):
#     """임시 저장된 데이터 불러오기"""
#     if user_id not in temp_storage:
#         return {
#             "success": False,
#             "message": "임시 저장된 데이터가 없습니다",
#             "storage": "temporary"
#         }
    
#     data = temp_storage[user_id]
#     return {
#         "success": True,
#         "message": "임시 저장된 데이터를 불러왔습니다",
#         "userId": user_id,
#         "storage": "temporary",
#         **data
#     }

# # 나머지 기존 엔드포인트들은 동일하게 유지...
# # (여기서는 핵심 수정사항만 표시)