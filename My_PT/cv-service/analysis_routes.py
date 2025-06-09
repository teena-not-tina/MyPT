# analysis_routes.py - 분석 및 검색 관련 라우터들 (수정됨)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import traceback
import os
import sys
from datetime import datetime

# 🔧 새로운 모델 로더 import
from services.model_loader import get_loaded_models, debug_status

# 라우터 생성
analysis_router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    include_images: Optional[bool] = False
    safe_search: Optional[str] = "moderate"

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    source: str

@analysis_router.post("/api/search")
async def web_search(request: SearchRequest):
    """웹 검색 API"""
    try:
        print(f"\n=== Web Search API Called ===")
        print(f"Query: {request.query}")
        
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Search query required")
        
        # 🔧 직접 검색 함수 import
        try:
            from utils.search import perform_google_search
            search_results = await perform_google_search(request.query)
        except ImportError:
            print("검색 모듈을 찾을 수 없습니다")
            search_results = []
        
        print(f"Search complete: {len(search_results)} results")
        
        return {
            "results": search_results[:request.max_results],
            "query": request.query,
            "total_results": len(search_results),
            "search_engine": "google_custom_search" if os.getenv("GOOGLE_API_KEY") else "mock_search"
        }
        
    except Exception as e:
        print(f"\nERROR in web_search:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Web search error: {str(e)}")

@analysis_router.post("/api/analyze")
async def analyze_with_gemini(request_data: dict):
    """Gemini 분석 API"""
    try:
        print(f"\n=== Gemini Analysis API Called ===")
        
        text = request_data.get("text", "")
        detection_results = request_data.get("detection_results")
        
        print(f"Text length: {len(text)}")
        print(f"Has detection results: {detection_results is not None}")
        
        from modules.gemini import analyze_text_with_gemini
        analysis = analyze_text_with_gemini(text, detection_results)
        print(f"Analysis complete")
        
        return {"analysis": analysis}
        
    except Exception as e:
        print(f"\nERROR in analyze_with_gemini:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini analysis error: {str(e)}")

@analysis_router.get("/health")
async def health_check():
    """헬스 체크 API"""
    print(f"\n=== Health Check API Called ===")
    
    # 🔧 새로운 방식으로 모델 정보 가져오기
    models = get_loaded_models()
    debug_info = debug_status()
    
    # 환경 변수 및 설정 확인
    mongodb_status = "unknown"
    try:
        # DB 정보는 config에서 가져오기
        from config.database import MONGODB_URI, DB_NAME, COLLECTION_NAME
        mongodb_status = "configured" if MONGODB_URI else "not_configured"
    except:
        mongodb_status = "not_configured"
        DB_NAME = "unknown"
        COLLECTION_NAME = "unknown" 
        MONGODB_URI = None
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0 - Enhanced OCR Inference + Web Search + 3-Model Ensemble - DEBUG",
        "features": [
            "3-Model YOLO Ensemble",
            "Enhanced OCR Inference with Pattern Matching",
            "Google Custom Search Integration", 
            "Ingredient Validation API",
            "MongoDB Storage",
            "V3 Data Migration",
            "Simple Save Format"
        ],
        "services": {
            "ensemble_models": {
                "target_models": ["yolo11s", "best", "best_friged"],
                "loaded_models": list(models.keys()),
                "loaded_count": len(models),
                "target_count": 3,
                "ensemble_ready": len(models) > 1,
                "full_ensemble": len(models) == 3
            },
            "mongodb": mongodb_status,
            "ocr": "configured" if os.environ.get('CLOVA_OCR_API_URL') else "not_configured",
            "gemini": "configured" if os.environ.get('GEMINI_API_KEY') else "not_configured",
            "google_search": "configured" if os.environ.get('GOOGLE_API_KEY') else "mock_mode",
            "enhanced_ocr": "available",
            "pattern_matching": "available",
            "web_search": "available",
            "v3_migration": "available",
            "simple_save": "available"
        },
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None
        },
        "temp_dir_exists": os.path.exists("temp"),
        "missing_models": [name for name in ["yolo11s", "best", "best_friged"] if name not in models],
        "enhanced_features": [
            "Pattern-based ingredient inference",
            "Google Custom Search integration",
            "Keyword extraction and summary",
            "Ingredient name validation API",
            "Enhanced debugging system"
        ],
        "debug_info": {
            "working_directory": os.getcwd(),
            "python_version": sys.version,
            "models_loaded": len(models),
            "directories": {
                "models": os.path.exists("models"),
                "modules": os.path.exists("modules"),
                "temp": os.path.exists("temp")
            },
            "model_debug": debug_info
        }
    }
