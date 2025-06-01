from dotenv import load_dotenv
import os

# ===== FatSecret API 관련 추가 =====
import requests
import base64
import json
from urllib.parse import urlencode


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
#from modules.yolo_detector import detect_objects, load_yolo_model
# 25.06.01 추가  
from modules.yolo_detector import (
    YOLODetector, 
    detector_instance, 
    load_yolo_model,
    detect_objects,
    analyze_food_with_properties,
    detect_with_integrated_system,
    enhanced_identify_item_from_image,
    AdvancedAnalyzer,
    performance_monitor
)
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

# 25.06.01 추가    
class DetectionRequest(BaseModel):
    strategy: Optional[str] = "smart"
    confidence: Optional[float] = 0.5
    use_gpt: Optional[bool] = True
    include_analysis: Optional[bool] = True

class BatchDetectionRequest(BaseModel):
    confidence: Optional[float] = 0.5
    use_gpt: Optional[bool] = False
    max_images: Optional[int] = 10

class AnalysisComparisonRequest(BaseModel):
    confidence: Optional[float] = 0.5
    include_gpt: Optional[bool] = True 

# YOLO 모델 로드
print("YOLO 모델 로딩 중...")
openai_api_key = os.getenv("openai_api_key")
if openai_api_key:
    detector_instance.openai_api_key = openai_api_key
    print("open_api_key 설정 완료 ")
model = load_yolo_model()
print("✅ YOLO 모델 로드 성공" if model else "❌ YOLO 모델 로드 실패")

# 고급 분석기 초기화
advanced_analyzer = AdvancedAnalyzer(detector_instance)
# 환경 변수 확인
print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"OPENAI_API_KEY 설정: {bool(os.environ.get('openai_api_key'))}")
print(f"MONGODB_URI 설정: {bool(MONGODB_URI)}")

@app.get("/")
async def root():
    return {
        "message": "향상된 Food Detection API with Custom MongoDB",
        "status": "running",
        "model_loaded": model is not None,
        "mongodb_connected": fridge_collection is not None,
        # 25.06.01 추가 
        "features": {
            "yolo_detection": True,
            "color_shape_analysis": True,
            "gpt_vision": bool(openai_api_key),
            "smart_strategy": True,
            "batch_processing": True,
            "performance_monitoring": True
        },
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri_host": MONGODB_URI.split('@')[1] if '@' in MONGODB_URI else "unknown"
        },
        "env_vars": {
            "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
            "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
            "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
            "openai_api_key": bool(os.getenv("openai_api_key")),
            "mongodb_uri": bool(MONGODB_URI),
        }
    }


@app.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.7):
    """YOLO 식품 탐지 - 모든 고급 기능 통합"""
    if model is None:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"🔥 종합 분석 탐지 시작: {file.filename}")
        
        start_time = datetime.now()
        file_content = await file.read()
        
        # ===== 1단계: 스마트 전략으로 최적 방법 선택 =====
        smart_result = detector_instance.smart_detection_strategy(file_content, confidence)
        # 스마트 전략 성공 후, "item" 클래스가 있으면 채소 전용 분석 추가 실행
        if smart_result.get("success"):
            detections = smart_result.get("detections", [])
            if not detections and "yolo_detections" in smart_result:
                detections = smart_result["yolo_detections"].get("items", [])
            
            # "item" 클래스가 있는지 확인
            has_item_class = any(det.get("class") in ["item", "unknown", "object"] for det in detections)
            
            if has_item_class:
                print("🥗 item 클래스 발견 - 채소 전용 분석 추가 실행")
                vegetable_result = detector_instance.enhanced_vegetable_analysis(file_content, confidence)
                
                if vegetable_result.get("success"):
                    # 채소 분석 결과로 "item" 클래스들을 교체
                    vegetable_detections = vegetable_result.get("detections", [])
                    for i, detection in enumerate(detections):
                        if detection.get("class") in ["item", "unknown", "object"]:
                            # 채소 분석 결과가 있으면 교체
                            if vegetable_detections:
                                detections[i] = vegetable_detections[0]  # 가장 확실한 결과 사용
                                print(f"✅ 채소 분석으로 교체: {detection.get('class')} → {vegetable_detections[0].get('class')}")
                    
                    # 업데이트된 결과로 smart_result 갱신
                    smart_result["detections"] = detections
                    smart_result["vegetable_enhanced"] = True
        final_detections = []
        analysis_info = {
            "strategy_used": smart_result.get("strategy", "unknown"),
            "gpt_used": False,
            "color_analysis_used": False,
            "shape_analysis_used": False
        }
        
        if smart_result.get("success"):
            print(f"📊 스마트 전략 결과: {smart_result.get('strategy')}")
            
            # YOLO 결과 추출
            if "detections" in smart_result:
                yolo_detections = smart_result["detections"]
            elif "yolo_detections" in smart_result:
                yolo_detections = smart_result["yolo_detections"].get("items", [])
            else:
                yolo_detections = []
            # ===== 25.06.01 🆕 채소 강화 로직 추가 =====
            has_item_class = any(det.get("class") in ["item", "unknown", "object"] for det in yolo_detections)
            
            if has_item_class:
                print("🥗 item 클래스 발견 - 채소 전용 분석 추가 실행")
                vegetable_result = detector_instance.enhanced_vegetable_analysis(file_content, confidence)
                
                if vegetable_result.get("success"):
                    vegetable_detections = vegetable_result.get("detections", [])
                    for i, detection in enumerate(yolo_detections):
                        if detection.get("class") in ["item", "unknown", "object"]:
                            if vegetable_detections:
                                yolo_detections[i] = vegetable_detections[0]
                                print(f"✅ 채소 분석으로 교체: {detection.get('class')} → {vegetable_detections[0].get('class')}")
                    
                    smart_result["detections"] = yolo_detections
                    smart_result["vegetable_enhanced"] = True
            
            # ===== 2단계: "item" 클래스에 대한 고급 분석 =====
            for detection in yolo_detections:
                original_class = detection.get("class", "")
                enhanced_detection = detection.copy()
                if original_class in ["item", "unknown", "object"] or detection.get("confidence", 0) < 0.6:
                    print(f"🔍 '{original_class}' 클래스 발견 - 고급 분석 수행")
                    
                    # 이미지 전처리
                    image = detector_instance.preprocess_image(file_content)
                    if image is not None:
                        # enhanced_detection = detection.copy()
                        
                        # ===== 색상/모양 분석 =====
                        bbox = detection.get("bbox", [])
                        if len(bbox) >= 4:
                            # 바운딩 박스 영역 추출
                            x1, y1, x2, y2 = map(int, bbox)
                            x1, y1 = max(0, x1), max(0, y1)
                            x2 = min(image.shape[1], x2)
                            y2 = min(image.shape[0], y2)
                            
                            if x2 > x1 and y2 > y1:
                                cropped_image = image[y1:y2, x1:x2]
                                
                                # 색상 분석
                                color_analysis = detector_instance.analyze_colors(cropped_image)
                                print(f"🎨 색상 분석 결과: {color_analysis}")
                                analysis_info["color_analysis_used"] = True
                                
                                # 모양 분석
                                shape_analysis = detector_instance.analyze_shapes(cropped_image)
                                print(f"📐 모양 분석 결과: {shape_analysis}")
                                analysis_info["shape_analysis_used"] = True
                                
                                # 색상+모양 기반 식재료 예측
                                primary_color = color_analysis.get("primary_color", "")
                                primary_shape = shape_analysis.get("primary_shape", "")

                                print(f"🔍 분석된 속성 - 색상: '{primary_color}', 형태: '{primary_shape}'")
                                
                                predicted_foods = detector_instance._predict_food_by_properties(
                                    primary_color, primary_shape, {}
                                )
                                print(f"🍎 예측 결과: {predicted_foods}")

                                if predicted_foods:
                                    enhanced_detection["class"] = predicted_foods[0]
                                    enhanced_detection["originalClass"] = original_class
                                    enhanced_detection["confidence"] = min(0.85, detection.get("confidence", 0.5) + 0.2)
                                    enhanced_detection["source"] = "color_shape_analysis"
                                    enhanced_detection["analysis_details"] = {
                                        "primary_color": primary_color,
                                        "primary_shape": primary_shape,
                                        "predicted_foods": predicted_foods
                                    }
                                    
                                    print(f"✅ 색상/모양 분석: '{original_class}' → '{predicted_foods[0]}'")
                                    print(f"   색상: {primary_color}, 형태: {primary_shape}")
                        
                        # ===== GPT 분석 (저신뢰도 or 여전히 불분명한 경우) =====
                        if (enhanced_detection.get("confidence", 0) < 0.7 or 
                            enhanced_detection.get("class") in ["item", "unknown"] or
                            openai_api_key):  # GPT 사용 가능하면 추가 검증
                            
                            print(f"🤖 GPT 분석 수행...")
                            
                            # 이미지 속성 정보 준비
                            properties = None
                            if "analysis_details" in enhanced_detection:
                                properties = {
                                    "colors": {"primary_color": enhanced_detection["analysis_details"].get("primary_color")},
                                    "shapes": {"primary_shape": enhanced_detection["analysis_details"].get("primary_shape")}
                                }
                            
                            gpt_result = detector_instance.enhanced_gpt_analysis_with_properties(
                                image, properties
                            )
                            
                            if gpt_result and "identified_items" in str(gpt_result):
                                analysis_info["gpt_used"] = True
                                
                                try:
                                    # JSON 파싱 시도
                                    if isinstance(gpt_result, str):
                                        import json
                                        # JSON 부분만 추출
                                        start_idx = gpt_result.find("{")
                                        end_idx = gpt_result.rfind("}") + 1
                                        if start_idx != -1 and end_idx != -1:
                                            json_str = gpt_result[start_idx:end_idx]
                                            gpt_data = json.loads(json_str)
                                            
                                            identified_items = gpt_data.get("identified_items", [])
                                            if identified_items:
                                                gpt_item = identified_items[0]
                                                gpt_name = gpt_item.get("name", "")
                                                
                                                if gpt_name and gpt_name not in ["item", "unknown", "object"]:
                                                    enhanced_detection["class"] = gpt_name
                                                    enhanced_detection["originalClass"] = original_class
                                                    enhanced_detection["confidence"] = 0.9
                                                    enhanced_detection["source"] = "gpt_enhanced"
                                                    enhanced_detection["gpt_analysis"] = gpt_data
                                                    
                                                    print(f"✅ GPT 분석: '{original_class}' → '{gpt_name}'")
                                    
                                except Exception as json_error:
                                    print(f"⚠️ GPT 결과 파싱 오류: {json_error}")
                                    # GPT 텍스트에서 키워드 추출
                                    gpt_lower = gpt_result.lower()
                                    food_keywords = ["양배추", "cabbage", "사과", "apple", "바나나", "banana", 
                                                   "토마토", "tomato", "당근", "carrot", "오이", "cucumber"]
                                    
                                    for keyword in food_keywords:
                                        if keyword in gpt_lower:
                                            if keyword in ["cabbage"]:
                                                enhanced_detection["class"] = "양배추"
                                            elif keyword in ["apple"]:
                                                enhanced_detection["class"] = "사과"
                                            elif keyword in ["banana"]:
                                                enhanced_detection["class"] = "바나나"
                                            elif keyword in ["tomato"]:
                                                enhanced_detection["class"] = "토마토"
                                            elif keyword in ["carrot"]:
                                                enhanced_detection["class"] = "당근"
                                            elif keyword in ["cucumber"]:
                                                enhanced_detection["class"] = "오이"
                                            else:
                                                enhanced_detection["class"] = keyword
                                            
                                            enhanced_detection["originalClass"] = original_class
                                            enhanced_detection["confidence"] = 0.8
                                            enhanced_detection["source"] = "gpt_keyword"
                                            
                                            print(f"✅ GPT 키워드 추출: '{original_class}' → '{enhanced_detection['class']}'")
                                            break
                
                final_detections.append(enhanced_detection)
                
            # ===== 3단계: 추가 검증 및 정리 =====
            # 중복 제거 및 신뢰도 순 정렬
            final_detections.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
        else:
            # 스마트 전략 실패 시 기본 YOLO 실행
            print("⚠️ 스마트 전략 실패 - 기본 YOLO 실행")
            basic_detections, _ = detector_instance.detect_objects(file_content, confidence)
            final_detections = basic_detections
            analysis_info["strategy_used"] = "fallback_yolo"
        
        # ===== 처리 시간 계산 =====
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # ===== 성능 모니터링 =====
        performance_monitor.record_detection(start_time, end_time, len(final_detections) > 0)
        
        print(f"✅ 종합 분석 완료: {processing_time:.3f}초")
        print(f"📊 최종 결과: {len(final_detections)}개 객체")
        print(f"🎯 분석 정보: {analysis_info}")
        
        # ===== 기존 프론트엔드 호환 형식으로 반환 =====
        return {
            "detections": final_detections,
            # 추가 정보 (프론트엔드에서 선택적 사용 가능)
            "_analysis_meta": {
                "processing_time": round(processing_time, 3),
                "strategy_used": analysis_info["strategy_used"],
                "enhanced_analysis": {
                    "gpt_used": analysis_info["gpt_used"],
                    "color_analysis_used": analysis_info["color_analysis_used"],
                    "shape_analysis_used": analysis_info["shape_analysis_used"]
                },
                "api_version": "enhanced_v1.0"
            }
        }
        
    except Exception as e:
        print(f"❌ 종합 탐지 오류: {e}")
        traceback.print_exc()
        
        # 오류 시 기본 YOLO로 폴백
        try:
            print("🔄 기본 YOLO로 폴백 시도...")
            file_content = await file.read() if hasattr(file, 'read') else file_content
            detections, _ = detector_instance.detect_objects(file_content, confidence)
            return {
                "detections": detections,
                "_analysis_meta": {
                    "fallback_used": True,
                    "error": str(e),
                    "api_version": "fallback_v1.0"
                }
            }
        except:
            raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")

# ===== 추가로 필요한 함수 (yolo_detector.py에 추가) =====

def detect_with_integrated_system(image_input, strategy="smart", confidence_threshold=0.5, openai_api_key=None):
    """통합 시스템으로 탐지 (기존 enhanced 엔드포인트에서 사용)"""
    try:
        if strategy == "smart":
            return detector_instance.smart_detection_strategy(image_input, confidence_threshold)
        elif strategy == "comprehensive":
            return detector_instance.comprehensive_analysis(
                image_input, 
                use_gpt=bool(openai_api_key), 
                confidence=confidence_threshold
            )
        else:
            # 기본 YOLO
            detections, image = detector_instance.detect_objects(image_input, confidence_threshold)
            return {
                "success": True,
                "strategy": "basic_yolo",
                "detections": detections
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "strategy": strategy
        }
    
# ===== 기존 API 엔드포인트들 =====

# 25.06.01 confidence 0.5 -> 0.7 수정, try-catch 부분 수정  
# @app.post("/api/detect")
# async def detect_food(file: UploadFile = File(...), confidence: float = 0.7):
#     """YOLO 식품 탐지 - 강화된 분석 포함"""
#     if model is None:
#         raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
#     try:
#         print(f"📁 파일 업로드: {file.filename}")
        
#         # 파일을 바이트로 읽기
#         file_content = await file.read()
        
#         print(f"🔍 YOLO 탐지 시작 (신뢰도: {confidence})")
        
#         # 통합 탐지기로 처리
#         detections, _ = detector_instance.detect_objects(file_content, confidence)
#         print(f"✅ 탐지 완료: {len(detections)}개 객체")
        
#         return {"detections": detections}
        
#     except Exception as e:
#         print(f"❌ 탐지 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")
#     # try:
#     #     print(f"📁 파일 업로드: {file.filename}")
#     #     os.makedirs("temp", exist_ok=True)
#     #     image_path = f"temp/{file.filename}"
        
#     #     with open(image_path, "wb") as f:
#     #         shutil.copyfileobj(file.file, f)
        
#     #     print(f"🔍 YOLO 탐지 시작 (신뢰도: {confidence})")
#     #     detections, _ = detect_objects(model, image_path, confidence)
#     #     print(f"✅ 탐지 완료: {len(detections)}개 객체")
        
#     #     try:
#     #         os.remove(image_path)
#     #     except:
#     #         pass
        
#     #     return {"detections": detections}
        
#     # except Exception as e:
#     #     print(f"❌ 탐지 오류: {e}")
#     #     traceback.print_exc()
#     #     raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")

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
# #25.06.01 추
# @app.post("/api/detect/enhanced")
# async def enhanced_detect_food(
#     file: UploadFile = File(...), 
#     request: DetectionRequest = DetectionRequest()
# ):
#     """향상된 식품 탐지 - 통합 시스템 사용"""
#     try:
#         print(f"🔥 향상된 탐지 시작: {file.filename}")
        
#         start_time = datetime.now()
#         file_content = await file.read()
        
#         result = detect_with_integrated_system(
#             file_content, 
#             strategy=request.strategy,
#             confidence_threshold=request.confidence,
#             openai_api_key=openai_api_key if request.use_gpt else None
#         )
        
#         end_time = datetime.now()
#         processing_time = (end_time - start_time).total_seconds()
        
#         performance_monitor.record_detection(start_time, end_time, result.get("success", False))
        
#         if request.include_analysis and result.get("success"):
#             detections = result.get("detections", [])
#             if not detections and "yolo_detections" in result:
#                 detections = result["yolo_detections"].get("items", [])
            
#             image = detector_instance.preprocess_image(file_content)
#             if image is not None and detections:
#                 quality_analysis = detector_instance.validate_detection_quality(detections, image)
#                 statistics = detector_instance.get_detection_statistics(detections)
                
#                 result["quality_analysis"] = quality_analysis
#                 result["statistics"] = statistics
        
#         result["processing_time"] = round(processing_time, 3)
#         result["api_version"] = "v2.0"
        
#         print(f"✅ 향상된 탐지 완료: {processing_time:.3f}초")
#         return result
        
#     except Exception as e:
#         print(f"❌ 향상된 탐지 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"향상된 탐지 오류: {str(e)}")

# @app.post("/api/detect/smart")
# async def smart_detect_food(file: UploadFile = File(...), confidence: float = 0.5):
#     """스마트 탐지 전략 - 이미지 특성에 따라 최적 방법 자동 선택"""
#     try:
#         print(f"🤖 스마트 탐지 시작: {file.filename}")
        
#         start_time = datetime.now()
#         file_content = await file.read()
        
#         result = detector_instance.smart_detection_strategy(file_content, confidence)
        
#         end_time = datetime.now()
#         processing_time = (end_time - start_time).total_seconds()
        
#         result["processing_time"] = round(processing_time, 3)
#         result["api_version"] = "smart_v2.0"
        
#         print(f"✅ 스마트 탐지 완료: {processing_time:.3f}초")
#         print(f"📊 사용 전략: {result.get('strategy', 'unknown')}")
        
#         return result
        
#     except Exception as e:
#         print(f"❌ 스마트 탐지 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"스마트 탐지 오류: {str(e)}")

# @app.post("/api/detect/comprehensive")
# async def comprehensive_food_analysis(file: UploadFile = File(...), confidence: float = 0.5):
#     """종합적인 식품 분석 (YOLO + 색상/모양 + GPT)"""
#     try:
#         print(f"🔬 종합 분석 시작: {file.filename}")
        
#         start_time = datetime.now()
#         file_content = await file.read()
        
#         result = detector_instance.comprehensive_analysis(
#             file_content, 
#             use_gpt=bool(openai_api_key), 
#             confidence=confidence
#         )
        
#         end_time = datetime.now()
#         processing_time = (end_time - start_time).total_seconds()
        
#         result["processing_time"] = round(processing_time, 3)
#         result["analysis_type"] = "comprehensive"
        
#         print(f"✅ 종합 분석 완료: {processing_time:.3f}초")
        
#         return result
        
#     except Exception as e:
#         print(f"❌ 종합 분석 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"종합 분석 오류: {str(e)}")

# @app.post("/api/detect/compare")
# async def compare_detection_methods(
#     file: UploadFile = File(...), 
#     request: AnalysisComparisonRequest = AnalysisComparisonRequest()
# ):
#     """탐지 방법 비교 분석"""
#     try:
#         print(f"🔬 방법 비교 분석 시작: {file.filename}")
        
#         start_time = datetime.now()
#         file_content = await file.read()
        
#         result = advanced_analyzer.compare_detection_methods(file_content, request.confidence)
        
#         end_time = datetime.now()
#         processing_time = (end_time - start_time).total_seconds()
        
#         result["processing_time"] = round(processing_time, 3)
#         result["comparison_type"] = "full_analysis"
        
#         print(f"✅ 방법 비교 완료: {processing_time:.3f}초")
        
#         return result
        
#     except Exception as e:
#         print(f"❌ 방법 비교 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"방법 비교 오류: {str(e)}")

# @app.post("/api/detect/batch")
# async def batch_detect_food(
#     files: List[UploadFile] = File(...),
#     request: BatchDetectionRequest = BatchDetectionRequest()
# ):
#     """배치 탐지 - 여러 이미지 한번에 처리"""
#     try:
#         if len(files) > request.max_images:
#             raise HTTPException(status_code=400, detail=f"최대 {request.max_images}개 이미지까지 처리 가능합니다")
        
#         print(f"📦 배치 탐지 시작: {len(files)}개 이미지")
        
#         start_time = datetime.now()
        
#         image_data = []
#         for file in files:
#             file_content = await file.read()
#             image_data.append(file_content)
        
#         result = detector_instance.batch_detection(
#             image_data, 
#             confidence=request.confidence, 
#             use_gpt=request.use_gpt
#         )
        
#         end_time = datetime.now()
#         processing_time = (end_time - start_time).total_seconds()
        
#         result["processing_time"] = round(processing_time, 3)
#         result["batch_info"] = {
#             "requested_images": len(files),
#             "processed_images": len(image_data),
#             "avg_time_per_image": round(processing_time / len(files), 3) if files else 0
#         }
        
#         print(f"✅ 배치 탐지 완료: {processing_time:.3f}초")
        
#         return result
        
#     except Exception as e:
#         print(f"❌ 배치 탐지 오류: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"배치 탐지 오류: {str(e)}")

# @app.get("/api/performance")
# async def get_performance_stats():
#     """성능 통계 조회"""
#     try:
#         stats = performance_monitor.get_performance_stats()
        
#         return {
#             "success": True,
#             "performance_stats": stats,
#             "system_info": {
#                 "model_loaded": model is not None,
#                 "gpt_available": bool(openai_api_key),
#                 "mongodb_connected": fridge_collection is not None
#             },
#             "timestamp": datetime.now().isoformat()
#         }
        
#     except Exception as e:
#         print(f"❌ 성능 통계 오류: {e}")
#         raise HTTPException(status_code=500, detail=f"성능 통계 오류: {str(e)}")
# FatSecret API 설정 (환경 변수에서 가져오기)
FATSECRET_CLIENT_ID = os.getenv("REACT_APP_FATSECRET_CLIENT_ID", "076cf9e5df224eb080cbff8525540a0b")
FATSECRET_CLIENT_SECRET = os.getenv("REACT_APP_FATSECRET_CLIENT_SECRET", "8e8c2c7d484a4507af68f28b960a3559")

# FatSecret API 관련 Pydantic 모델
class FatSecretTokenRequest(BaseModel):
    pass

class FatSecretSearchRequest(BaseModel):
    foodName: str
    accessToken: str

class FatSecretDetailsRequest(BaseModel):
    foodId: str
    accessToken: str

class FatSecretCalorieRequest(BaseModel):
    foodName: str

# 25.05.30추가  ===== FatSecret API 엔드포인트들 =====

@app.post("/api/fatsecret/token")
async def get_fatsecret_access_token():
    """FatSecret OAuth 2.0 Access Token 발급"""
    try:
        print("🔑 FatSecret Access Token 요청 시작")
        
        if not FATSECRET_CLIENT_ID or not FATSECRET_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="FatSecret API 키가 설정되지 않았습니다")
        
        # OAuth 2.0 Client Credentials 방식
        auth_string = f"{FATSECRET_CLIENT_ID}:{FATSECRET_CLIENT_SECRET}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'basic'
        }
        
        # FatSecret Token API 호출
        response = requests.post(
            'https://oauth.fatsecret.com/connect/token',
            headers=headers,
            data=urlencode(data),
            timeout=30
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            print(f"✅ FatSecret Access Token 발급 성공")
            
            return {
                "success": True,
                "access_token": access_token,
                "token_type": token_data.get('token_type', 'Bearer'),
                "expires_in": token_data.get('expires_in', 3600)
            }
        else:
            print(f"❌ FatSecret Token 요청 실패: {response.status_code}")
            print(f"응답: {response.text}")
            raise HTTPException(
                status_code=500, 
                detail=f"FatSecret Token 발급 실패: {response.status_code}"
            )
    
    except requests.exceptions.Timeout:
        print("❌ FatSecret API 타임아웃")
        raise HTTPException(status_code=504, detail="FatSecret API 타임아웃")
    except Exception as e:
        print(f"❌ FatSecret Token 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Token 발급 오류: {str(e)}")

@app.post("/api/fatsecret/search")
async def search_food_in_fatsecret(request: FatSecretSearchRequest):
    """FatSecret에서 식품 검색"""
    try:
        print(f"🔍 FatSecret 식품 검색: '{request.foodName}'")
        
        headers = {
            'Authorization': f'Bearer {request.accessToken}',
            'Content-Type': 'application/json'
        }
        
        # 검색 쿼리 구성 (한글과 영문 모두 지원)
        search_query = request.foodName.strip()
        
        params = {
            'method': 'foods.search',
            'search_expression': search_query,
            'page_number': 0,
            'max_results': 10,
            'format': 'json'
        }
        
        # FatSecret Search API 호출
        response = requests.get(
            'https://platform.fatsecret.com/rest/server.api',
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # 검색 결과 파싱
            foods = []
            if 'foods' in result_data and 'food' in result_data['foods']:
                food_list = result_data['foods']['food']
                
                # 단일 결과인 경우 리스트로 변환
                if isinstance(food_list, dict):
                    food_list = [food_list]
                
                for food in food_list:
                    foods.append({
                        'food_id': food.get('food_id'),
                        'food_name': food.get('food_name'),
                        'food_type': food.get('food_type', 'Generic'),
                        'food_url': food.get('food_url', ''),
                        'brand_name': food.get('brand_name', '')
                    })
            
            print(f"✅ FatSecret 검색 완료: {len(foods)}개 결과")
            
            return {
                "success": True,
                "result": {
                    'foods': foods,
                    'total_results': len(foods),
                    'search_term': search_query
                }
            }
        else:
            print(f"❌ FatSecret 검색 실패: {response.status_code}")
            raise HTTPException(
                status_code=500, 
                detail=f"식품 검색 실패: {response.status_code}"
            )
    
    except requests.exceptions.Timeout:
        print("❌ FatSecret 검색 타임아웃")
        raise HTTPException(status_code=504, detail="검색 타임아웃")
    except Exception as e:
        print(f"❌ FatSecret 검색 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 오류: {str(e)}")

@app.post("/api/fatsecret/details")
async def get_food_details_from_fatsecret(request: FatSecretDetailsRequest):
    """FatSecret에서 식품 상세 영양정보 조회"""
    try:
        print(f"📊 FatSecret 상세 정보 조회: {request.foodId}")
        
        headers = {
            'Authorization': f'Bearer {request.accessToken}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'method': 'food.get',
            'food_id': request.foodId,
            'format': 'json'
        }
        
        # FatSecret Food Details API 호출
        response = requests.get(
            'https://platform.fatsecret.com/rest/server.api',
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            food_data = response.json()
            
            # 영양정보 파싱
            nutrition_info = {}
            
            if 'food' in food_data:
                food = food_data['food']
                
                # 서빙 정보 추출
                servings = food.get('servings', {}).get('serving', [])
                if isinstance(servings, dict):
                    servings = [servings]
                
                # 첫 번째 서빙 정보 사용 (보통 100g 기준)
                if servings:
                    serving = servings[0]
                    nutrition_info = {
                        'food_name': food.get('food_name', ''),
                        'serving_description': serving.get('serving_description', '100g'),
                        'calories': float(serving.get('calories', 0)),
                        'carbohydrate': float(serving.get('carbohydrate', 0)),
                        'protein': float(serving.get('protein', 0)),
                        'fat': float(serving.get('fat', 0)),
                        'fiber': float(serving.get('fiber', 0)),
                        'sugar': float(serving.get('sugar', 0)),
                        'sodium': float(serving.get('sodium', 0))
                    }
            
            print(f"✅ FatSecret 상세 정보 조회 완료")
            
            return {
                "success": True,
                "nutritionInfo": nutrition_info
            }
        else:
            print(f"❌ FatSecret 상세 조회 실패: {response.status_code}")
            raise HTTPException(
                status_code=500, 
                detail=f"상세 정보 조회 실패: {response.status_code}"
            )
    
    except requests.exceptions.Timeout:
        print("❌ FatSecret 상세 조회 타임아웃")
        raise HTTPException(status_code=504, detail="상세 조회 타임아웃")
    except Exception as e:
        print(f"❌ FatSecret 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"상세 조회 오류: {str(e)}")

@app.post("/api/fatsecret/calorie")
async def get_calorie_info_integrated(request: FatSecretCalorieRequest):
    """통합 칼로리 정보 조회 (Token 발급 → 검색 → 상세 조회 일괄 처리)"""
    try:
       # print(f"🍎 통합 칼로리 조회 시작: '{request.foodName}'")
        english_name = translate_korean_to_english(request.foodName)
        search_name = english_name if english_name != request.foodName else request.foodName
        print(f"🔍 검색어: '{request.foodName}' → '{search_name}'")
        
        # 1단계: Access Token 발급
        token_response = await get_fatsecret_access_token()
        if not token_response.get("success"):
            raise HTTPException(status_code=500, detail="Access Token 발급 실패")
        
        access_token = token_response["access_token"]
        
        # 2단계: 식품 검색
        search_request = FatSecretSearchRequest(
            #foodName=request.foodName,
            foodName=search_name, 
            accessToken=access_token
        )
        search_response = await search_food_in_fatsecret(search_request)
        
        if not search_response.get("success") or not search_response["result"]["foods"]:
            # 검색 결과가 없으면 모의 데이터 반환
            print(f"⚠️ FatSecret에서 '{request.foodName}' 검색 결과 없음 - 모의 데이터 사용")
            return get_mock_nutrition_data(request.foodName)
        
        # 첫 번째 검색 결과 사용
        first_food = search_response["result"]["foods"][0]
        food_id = first_food["food_id"]
        
        # 3단계: 상세 영양정보 조회
        details_request = FatSecretDetailsRequest(
            foodId=food_id,
            accessToken=access_token
        )
        details_response = await get_food_details_from_fatsecret(details_request)
        
        if details_response.get("success") and details_response["nutritionInfo"]:
            nutrition = details_response["nutritionInfo"]
            
            print(f"✅ 통합 칼로리 조회 성공: {nutrition.get('calories', 0)}kcal")
            
            return {
                "success": True,
                "food_name": nutrition.get('food_name', request.foodName),
                "calories": nutrition.get('calories', 0),
                "carbohydrate": nutrition.get('carbohydrate', 0),
                "protein": nutrition.get('protein', 0),
                "fat": nutrition.get('fat', 0),
                "fiber": nutrition.get('fiber', 0),
                "sugar": nutrition.get('sugar', 0),
                "sodium": nutrition.get('sodium', 0),
                "serving_description": nutrition.get('serving_description', '100g'),
                "source": "fatsecret_api"
            }
        else:
            # 상세 정보 조회 실패시 모의 데이터 사용
            print(f"⚠️ FatSecret 상세 정보 조회 실패 - 모의 데이터 사용")
            return get_mock_nutrition_data(request.foodName)
    
    except Exception as e:
        print(f"❌ 통합 칼로리 조회 오류: {e}")
        # 오류 발생시 모의 데이터로 폴백
        return get_mock_nutrition_data(request.foodName)

# ===== 모의 영양 데이터 함수 =====
def translate_korean_to_english(korean_food_name):
    """한글 식품명을 영어로 번역"""
    translation_map = {
        '양배추': 'cabbage',
        '사과': 'apple', 
        '바나나': 'banana',
        '당근': 'carrot',
        '오이': 'cucumber',
        '토마토': 'tomato',
        '감자': 'potato',
        '양파': 'onion',
        '브로콜리': 'broccoli',
        '시금치': 'spinach',
        '배추': 'chinese cabbage',
        '상추': 'lettuce',
        '고추': 'pepper',
        '마늘': 'garlic',
        '생강': 'ginger',
        '계란': 'egg',
        '달걀': 'egg',
        '닭고기': 'chicken',
        '소고기': 'beef',
        '돼지고기': 'pork',
        '우유': 'milk',
        '치즈': 'cheese',
        '요거트': 'yogurt',
        '빵': 'bread',
        '쌀': 'rice',
        '김치': 'kimchi'
    }
    return translation_map.get(korean_food_name, korean_food_name)

def get_mock_nutrition_data(food_name: str):
    """모의 영양 데이터 (FatSecret API 실패시 대체용)"""
    print(f"📊 모의 영양 데이터 사용: '{food_name}'")
    
    # 프론트엔드와 동일한 모의 데이터
    mock_data = {
        # 음료류
        '아몬드우유': {'calories': 50, 'carbohydrate': 4.5, 'protein': 1.2, 'fat': 2.8},
        '오렌지주스': {'calories': 45, 'carbohydrate': 11, 'protein': 0.7, 'fat': 0.2},
        '토마토주스': {'calories': 17, 'carbohydrate': 4, 'protein': 0.8, 'fat': 0.1},
        '두유': {'calories': 54, 'carbohydrate': 4.2, 'protein': 3.3, 'fat': 1.8},
        '오트밀크': {'calories': 80, 'carbohydrate': 16, 'protein': 3, 'fat': 1.5},
        '바나나우유': {'calories': 150, 'carbohydrate': 22, 'protein': 8, 'fat': 3.5},
        '딸기우유': {'calories': 130, 'carbohydrate': 20, 'protein': 8, 'fat': 2.5},
        '사과주스': {'calories': 46, 'carbohydrate': 11.3, 'protein': 0.1, 'fat': 0.1},
        '포도주스': {'calories': 60, 'carbohydrate': 15, 'protein': 0.2, 'fat': 0.1},
        '복숭아주스': {'calories': 39, 'carbohydrate': 9.5, 'protein': 0.6, 'fat': 0.1},
        '코코넛밀크': {'calories': 230, 'carbohydrate': 6, 'protein': 2.3, 'fat': 24},
        '초콜릿우유': {'calories': 208, 'carbohydrate': 26, 'protein': 8, 'fat': 8.5},
        '우유': {'calories': 150, 'carbohydrate': 12, 'protein': 8, 'fat': 8},
        
        # 과일류
        '사과': {'calories': 52, 'carbohydrate': 14, 'protein': 0.3, 'fat': 0.2},
        '바나나': {'calories': 89, 'carbohydrate': 23, 'protein': 1.1, 'fat': 0.3},
        '오렌지': {'calories': 47, 'carbohydrate': 12, 'protein': 0.9, 'fat': 0.1},
        '토마토': {'calories': 18, 'carbohydrate': 3.9, 'protein': 0.9, 'fat': 0.2},
        '딸기': {'calories': 32, 'carbohydrate': 7.7, 'protein': 0.7, 'fat': 0.3},
        '포도': {'calories': 62, 'carbohydrate': 16, 'protein': 0.6, 'fat': 0.2},
        '복숭아': {'calories': 39, 'carbohydrate': 9.5, 'protein': 0.9, 'fat': 0.3},
        
        # 채소류
        '양배추': {'calories': 24, 'carbohydrate': 5.58, 'protein': 1.44, 'fat': 0.12},
        '상추': {'calories': 15, 'carbohydrate': 2.9, 'protein': 1.4, 'fat': 0.2},
        '양상추': {'calories': 15, 'carbohydrate': 2.9, 'protein': 1.4, 'fat': 0.2},
        '케일': {'calories': 35, 'carbohydrate': 4.4, 'protein': 2.9, 'fat': 1.5},
        '무': {'calories': 18, 'carbohydrate': 4.1, 'protein': 0.6, 'fat': 0.1},
        '호박': {'calories': 20, 'carbohydrate': 4.9, 'protein': 0.8, 'fat': 0.1},
        '당근': {'calories': 41, 'carbohydrate': 10, 'protein': 0.9, 'fat': 0.2},
        '양파': {'calories': 40, 'carbohydrate': 9.3, 'protein': 1.1, 'fat': 0.1},
        '감자': {'calories': 77, 'carbohydrate': 17, 'protein': 2, 'fat': 0.1},
        '오이': {'calories': 16, 'carbohydrate': 4, 'protein': 0.7, 'fat': 0.1},
        '브로콜리': {'calories': 34, 'carbohydrate': 7, 'protein': 2.8, 'fat': 0.4},
        '상추': {'calories': 15, 'carbohydrate': 2.9, 'protein': 1.4, 'fat': 0.2},
        '배추': {'calories': 13, 'carbohydrate': 3, 'protein': 1.3, 'fat': 0.1},
        '시금치': {'calories': 23, 'carbohydrate': 3.6, 'protein': 2.9, 'fat': 0.4},
        '고추': {'calories': 40, 'carbohydrate': 9, 'protein': 2, 'fat': 0.2},
        '마늘': {'calories': 149, 'carbohydrate': 33, 'protein': 6.4, 'fat': 0.5},
        '생강': {'calories': 80, 'carbohydrate': 18, 'protein': 1.8, 'fat': 0.8},
        
        # 단백질류
        '계란': {'calories': 155, 'carbohydrate': 1.1, 'protein': 13, 'fat': 11},
        '달걀': {'calories': 155, 'carbohydrate': 1.1, 'protein': 13, 'fat': 11},
        '닭고기': {'calories': 239, 'carbohydrate': 0, 'protein': 27, 'fat': 14},
        '소고기': {'calories': 250, 'carbohydrate': 0, 'protein': 26, 'fat': 15},
        '돼지고기': {'calories': 242, 'carbohydrate': 0, 'protein': 27, 'fat': 14},
        '생선': {'calories': 206, 'carbohydrate': 0, 'protein': 22, 'fat': 12},
        '새우': {'calories': 99, 'carbohydrate': 0.2, 'protein': 24, 'fat': 0.3},
        '햄': {'calories': 145, 'carbohydrate': 1.5, 'protein': 21, 'fat': 5.5},
        '소시지': {'calories': 301, 'carbohydrate': 1.5, 'protein': 12, 'fat': 27},
        
        # 유제품류
        '치즈': {'calories': 113, 'carbohydrate': 1, 'protein': 7, 'fat': 9},
        '버터': {'calories': 717, 'carbohydrate': 0.1, 'protein': 0.9, 'fat': 81},
        '요거트': {'calories': 59, 'carbohydrate': 3.6, 'protein': 10, 'fat': 0.4},
        
        # 곡물류
        '빵': {'calories': 265, 'carbohydrate': 49, 'protein': 9, 'fat': 3.2},
        '쌀': {'calories': 130, 'carbohydrate': 28, 'protein': 2.7, 'fat': 0.3},
        '면': {'calories': 220, 'carbohydrate': 44, 'protein': 8, 'fat': 1.3},
        '라면': {'calories': 436, 'carbohydrate': 56, 'protein': 10, 'fat': 19},
        '파스타': {'calories': 220, 'carbohydrate': 44, 'protein': 8, 'fat': 1.3},
        
        # 발효식품류
        '김치': {'calories': 23, 'carbohydrate': 4, 'protein': 1.6, 'fat': 0.6},
        '된장': {'calories': 44, 'carbohydrate': 6, 'protein': 3, 'fat': 1.3},
        '고추장': {'calories': 40, 'carbohydrate': 9, 'protein': 1.5, 'fat': 0.3},
        '간장': {'calories': 8, 'carbohydrate': 0.8, 'protein': 1.3, 'fat': 0},
        
        # 기타
        '설탕': {'calories': 387, 'carbohydrate': 100, 'protein': 0, 'fat': 0},
        '소금': {'calories': 0, 'carbohydrate': 0, 'protein': 0, 'fat': 0},
        '기름': {'calories': 884, 'carbohydrate': 0, 'protein': 0, 'fat': 100},
        '버섯': {'calories': 22, 'carbohydrate': 3.3, 'protein': 3.1, 'fat': 0.3},
        '콩': {'calories': 347, 'carbohydrate': 30, 'protein': 36, 'fat': 20},
        '견과': {'calories': 607, 'carbohydrate': 7, 'protein': 15, 'fat': 61},
        '아몬드': {'calories': 579, 'carbohydrate': 22, 'protein': 21, 'fat': 50}
    }
    
    # 식품명으로 데이터 검색
    nutrition = mock_data.get(food_name)
    
    if nutrition:
        return {
            "success": True,
            "food_name": food_name,
            "calories": nutrition['calories'],
            "carbohydrate": nutrition['carbohydrate'],
            "protein": nutrition['protein'],
            "fat": nutrition['fat'],
            "fiber": 0,  # 모의 데이터에는 없음
            "sugar": 0,  # 모의 데이터에는 없음
            "sodium": 0, # 모의 데이터에는 없음
            "serving_description": "100g 기준 (모의 데이터)",
            "source": "mock_data"
        }
    else:
        return {
            "success": False,
            "message": f"'{food_name}' 영양정보를 찾을 수 없습니다.",
            "food_name": food_name,
            "calories": 0,
            "carbohydrate": 0,
            "protein": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0,
            "serving_description": "정보 없음",
            "source": "unknown"
        }
    
    
    
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
            "gemini": "configured" if os.environ.get('GEMINI_API_KEY') else "not_configured",
            "openai": "configured" if os.environ.get('openai_api_key') else "not_configured"
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

 
 