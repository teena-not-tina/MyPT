# cv-service/main.py
from dotenv import load_dotenv
import os

# .env 파일 로드 (가장 먼저 실행)
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import traceback
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

# YOLO 모델 로드
print("YOLO 모델 로딩 중...")
model = load_yolo_model()
print("✅ YOLO 모델 로드 성공" if model else "❌ YOLO 모델 로드 실패")

# 환경 변수 확인
print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")

@app.get("/")
async def root():
    return {
        "message": "Food Detection API",
        "status": "running",
        "model_loaded": model is not None,
        "env_vars": {
            "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
            "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
            "gemini_key": bool(os.environ.get('GEMINI_API_KEY'))
        }
    }

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

# 추가 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": os.environ.get("TZ", "UTC"),
        "model_status": "loaded" if model else "error",
        "temp_dir_exists": os.path.exists("temp")
    }

# 환경 변수 확인 엔드포인트 (디버깅용)
@app.get("/debug/env")
async def debug_env():
    """환경 변수 상태 확인 (디버깅용)"""
    return {
        "clova_ocr_url": bool(os.environ.get('CLOVA_OCR_API_URL')),
        "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
        "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
        "working_directory": os.getcwd(),
        "temp_directory": os.path.exists("temp"),
        "model_loaded": model is not None
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 서버 시작 중...")
    print(f"📍 서버 주소: http://0.0.0.0:8000")
    print(f"📋 API 문서: http://0.0.0.0:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)