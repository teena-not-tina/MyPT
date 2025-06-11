# main.py - 초간단 버전 (100줄 이내)
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv
from config.database import DB_NAME, COLLECTION_NAME

print("=" * 60)
print("Starting Food Detection API - Ultra Slim Version")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print("=" * 60)

# 환경 변수 로드
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from detection_routes import detection_router
from ocr_routes import ocr_router  
from fridge_routes import fridge_router
from analysis_routes import analysis_router

from services.model_loader import load_ensemble_models, create_enhanced_detector
from config.database import init_mongodb
from utils.data_converter import convert_v3_to_current_format

print("\n--- Module imports ---")
print("✓ All routers and services imported successfully")

# FastAPI 앱 생성
app = FastAPI(
    title="Food Detection API with Enhanced OCR Inference", 
    version="4.0.0-ultra-slim"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(detection_router)
app.include_router(ocr_router)
app.include_router(fridge_router)
app.include_router(analysis_router)

# 전역 변수들
ensemble_models = {}
enhanced_detector = None
client = None
db = None
fridge_collection = None

def initialize_app():
    """앱 초기화"""
    global ensemble_models, enhanced_detector, client, db, fridge_collection

    print("\n=== APP INITIALIZATION ===")

    # 1. MongoDB 초기화
    client, db, fridge_collection = init_mongodb()

    # 2. 모델 로딩
    print("\n--- Loading Models ---")
    ensemble_models = load_ensemble_models()

    # 3. Enhanced 탐지기 생성
    enhanced_detector = create_enhanced_detector(ensemble_models)

    print("✅ App initialization complete!")
    return len(ensemble_models), fridge_collection is not None

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 초기화"""
    models_count, db_connected = initialize_app()
    print(f"🚀 API Server Ready - Models: {models_count}, DB: {db_connected}")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Food Detection API - Ultra Slim Version",
        "version": "4.0.0-ultra-slim",
        "status": "running",
        "models_loaded": len(ensemble_models),
        "mongodb_connected": fridge_collection is not None,
        "features": [
            "3-Model YOLO Ensemble",
            "Enhanced OCR Inference", 
            "Pattern Matching",
            "Web Search Integration",
            "MongoDB Storage"
        ],
        "routers": [
            "detection_router - /api/detect/*",
            "ocr_router - /api/ocr/*",
            "fridge_router - /api/fridge/*", 
            "analysis_router - /api/search, /api/analyze, /health"
        ]
    }

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("🚀 ULTRA SLIM FOOD DETECTION API")
    print("=" * 60)
    print("📁 Architecture:")
    print("   - main.py: 95줄 (라우터 등록 + 초기화)")
    print("   - detection_routes.py: 탐지 API들")
    print("   - ocr_routes.py: OCR API들")
    print("   - fridge_routes.py: 냉장고 데이터 API들")
    print("   - analysis_routes.py: 분석/검색 API들")
    print("   - utils/: 유틸리티 함수들")
    print("   - services/: 비즈니스 로직")
    print("   - config/: 설정 파일들")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)