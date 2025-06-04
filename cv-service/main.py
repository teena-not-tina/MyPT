from dotenv import load_dotenv
import os

# .env 파일 로드 (가장 먼저 실행)
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import shutil
import traceback
import motor.motor_asyncio
from datetime import datetime
import numpy as np

# 기존 모듈들
from modules.yolo_detector import detect_objects, load_yolo_model
from modules.ocr_processor import extract_text_with_ocr
from modules.gemini import analyze_text_with_gemini

# FastAPI 앱 생성
app = FastAPI(title="Food Detection API with 3-Model Ensemble YOLO", version="3.0.0")

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
DB_NAME = "test"  # 임시 DB명 (회의 후 변경)
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
    source: str = "analysis"  # detection, ocr, ocr_smart, analysis, ensemble
    bbox: Optional[List[float]] = None  # YOLO bbox 정보
    originalClass: Optional[str] = None  # 원본 영어 클래스명
    ensemble_info: Optional[Dict] = None  # 앙상블 상세 정보
    
    class Config:
        from_attributes = True

class FridgeData(BaseModel):
    userId: str
    ingredients: List[Ingredient]
    timestamp: str
    totalCount: int
    totalTypes: int
    analysisMethod: Optional[str] = "ensemble"  # detection, ocr, mixed, ensemble
    deviceInfo: Optional[str] = None  # 기기 정보
    
    class Config:
        from_attributes = True

# ===== 간소화된 데이터 모델 (사용자 요구사항에 맞춤) =====
class SimpleIngredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: float
    source: str

class SimpleFridgeData(BaseModel):
    userId: str
    ingredients: List[SimpleIngredient]

# ===== 버전3 데이터 마이그레이션 관련 모델 =====
class V3IngredientData(BaseModel):
    """버전3 호환 식재료 데이터 모델"""
    name: Optional[str] = None
    ingredient: Optional[str] = None  # 버전3에서 사용했을 수 있는 필드명
    food: Optional[str] = None
    foodName: Optional[str] = None
    quantity: Optional[int] = 1
    count: Optional[int] = None
    amount: Optional[int] = None
    confidence: Optional[float] = 0.5
    source: Optional[str] = "v3_migration"

def convert_v3_to_current_format(v3_data):
    """버전3 데이터를 현재 형식으로 변환"""
    if not v3_data:
        return []
    
    converted_ingredients = []
    
    for idx, item in enumerate(v3_data):
        # 다양한 형태의 버전3 데이터 처리
        if isinstance(item, str):
            # 단순 문자열인 경우
            converted_ingredients.append({
                "id": idx + 1,
                "name": item,
                "quantity": 1,
                "confidence": 0.7,
                "source": "v3_text_migration"
            })
        elif isinstance(item, dict):
            # 딕셔너리인 경우 필드명 매핑
            name = (item.get("name") or 
                   item.get("ingredient") or 
                   item.get("food") or 
                   item.get("foodName") or 
                   "알 수 없는 식재료")
            
            quantity = (item.get("quantity") or 
                       item.get("count") or 
                       item.get("amount") or 1)
            
            converted_ingredients.append({
                "id": item.get("id", idx + 1),
                "name": name,
                "quantity": max(1, int(quantity)),
                "confidence": item.get("confidence", 0.5),
                "source": item.get("source", "v3_migration")
            })
    
    return converted_ingredients

# ===== 3가지 YOLO 모델 앙상블 =====
def load_ensemble_models():
    """3가지 YOLO 앙상블 모델들을 로드"""
    models = {}
    model_paths = {
        'yolo11s': 'models/yolo11s.pt',
        'best': 'models/best.pt',
        'best_friged': 'models/best_fri.pt'  # 새로 추가된 세 번째 모델
    }
    
    print("🤖 3가지 YOLO 앙상블 모델 로딩 중...")
    
    for model_name, model_path in model_paths.items():
        try:
            if os.path.exists(model_path):
                model = load_yolo_model(model_path)
                if model:
                    models[model_name] = model
                    print(f"✅ {model_name} 모델 로드 성공: {model_path}")
                else:
                    print(f"❌ {model_name} 모델 로드 실패: {model_path}")
            else:
                print(f"⚠️ {model_name} 모델 파일 없음: {model_path}")
        except Exception as e:
            print(f"❌ {model_name} 모델 로드 오류: {e}")
    
    print(f"📊 총 {len(models)}개 모델 로드 완료: {list(models.keys())}")
    
    # 최소 1개 모델은 필요
    if len(models) == 0:
        print("⚠️ 경고: 로드된 모델이 없습니다!")
    elif len(models) < 3:
        print(f"⚠️ 경고: 3개 모델 중 {len(models)}개만 로드됨")
    
    return models

def calculate_iou(box1, box2):
    """두 바운딩 박스 간의 IoU(Intersection over Union) 계산"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # 교집합 영역 계산
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)
    
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0
    
    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    
    # 합집합 영역 계산
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0

def ensemble_detections(detections_dict, iou_threshold=0.5, confidence_weights=None):
    """
    여러 모델의 탐지 결과를 앙상블하여 최종 결과 생성
    
    Args:
        detections_dict: {model_name: detections_list} 형태의 딕셔너리
        iou_threshold: NMS를 위한 IoU 임계값
        confidence_weights: 각 모델의 가중치 {model_name: weight}
    """
    if not detections_dict:
        return []
    
    # 3가지 모델에 최적화된 기본 가중치 설정
    if confidence_weights is None:
        confidence_weights = {
            'yolo11s': 1.1,      # 범용 모델
            'best': 1.1,         # 커스텀 학습 모델 (높은 가중치)
            'best_friged': 0.8   # 냉장고 특화 모델 (중간 가중치)
        }
    
    # 모든 탐지 결과를 하나의 리스트로 통합
    all_detections = []
    
    for model_name, detections in detections_dict.items():
        model_weight = confidence_weights.get(model_name, 1.0)
        
        for detection in detections:
            # 신뢰도에 모델 가중치 적용
            weighted_confidence = detection['confidence'] * model_weight
            
            enhanced_detection = {
                **detection,
                'confidence': weighted_confidence,
                'original_confidence': detection['confidence'],
                'model_source': model_name,
                'model_weight': model_weight
            }
            all_detections.append(enhanced_detection)
    
    # 신뢰도 기준으로 정렬
    all_detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    # NMS 적용하여 중복 제거
    final_detections = []
    
    for current_detection in all_detections:
        should_keep = True
        current_bbox = current_detection['bbox']
        
        for kept_detection in final_detections:
            kept_bbox = kept_detection['bbox']
            
            # 같은 클래스이고 IoU가 임계값보다 높으면 중복으로 판단
            if (current_detection['class'] == kept_detection['class'] and 
                calculate_iou(current_bbox, kept_bbox) > iou_threshold):
                should_keep = False
                
                # 앙상블 정보 업데이트 (여러 모델에서 탐지된 경우)
                if 'ensemble_sources' not in kept_detection:
                    kept_detection['ensemble_sources'] = [kept_detection['model_source']]
                    kept_detection['ensemble_confidences'] = [kept_detection['original_confidence']]
                    kept_detection['ensemble_weights'] = [kept_detection['model_weight']]
                
                kept_detection['ensemble_sources'].append(current_detection['model_source'])
                kept_detection['ensemble_confidences'].append(current_detection['original_confidence'])
                kept_detection['ensemble_weights'].append(current_detection['model_weight'])
                
                # 가중 평균 신뢰도로 업데이트
                weighted_sum = sum(conf * weight for conf, weight in 
                                 zip(kept_detection['ensemble_confidences'], kept_detection['ensemble_weights']))
                weight_sum = sum(kept_detection['ensemble_weights'])
                kept_detection['confidence'] = weighted_sum / weight_sum if weight_sum > 0 else kept_detection['confidence']
                kept_detection['ensemble_count'] = len(kept_detection['ensemble_sources'])
                
                break
        
        if should_keep:
            # 단일 모델 탐지 정보 추가
            current_detection['ensemble_sources'] = [current_detection['model_source']]
            current_detection['ensemble_confidences'] = [current_detection['original_confidence']]
            current_detection['ensemble_weights'] = [current_detection['model_weight']]
            current_detection['ensemble_count'] = 1
            final_detections.append(current_detection)
    
    # 앙상블 메타데이터 추가
    for detection in final_detections:
        detection['ensemble_info'] = {
            'models_used': detection['ensemble_sources'],
            'individual_confidences': dict(zip(detection['ensemble_sources'], detection['ensemble_confidences'])),
            'model_weights': dict(zip(detection['ensemble_sources'], detection['ensemble_weights'])),
            'ensemble_count': detection['ensemble_count'],
            'final_confidence': detection['confidence'],
            'is_consensus': detection['ensemble_count'] >= 2  # 2개 이상 모델에서 탐지됨
        }
    
    return final_detections

def detect_objects_ensemble(models, image_path, confidence=0.5, ensemble_weights=None):
    """3가지 앙상블 모델을 사용한 객체 탐지"""
    if not models:
        raise ValueError("로드된 모델이 없습니다")
    
    print(f"🔍 3가지 모델 앙상블 탐지 시작 - 모델 수: {len(models)}")
    
    # 각 모델별 탐지 결과 수집
    all_detections = {}
    total_detections = 0
    
    for model_name, model in models.items():
        try:
            print(f"   📊 {model_name} 모델 탐지 중...")
            detections, _ = detect_objects(model, image_path, confidence)
            all_detections[model_name] = detections
            total_detections += len(detections)
            print(f"   ✅ {model_name}: {len(detections)}개 객체 탐지")
        except Exception as e:
            print(f"   ❌ {model_name} 탐지 오류: {e}")
            all_detections[model_name] = []

    print(f"📊 원본 탐지 결과: 총 {total_detections}개 객체 (앙상블 전)")
    
    # 3가지 모델에 최적화된 앙상블 가중치 설정
    if ensemble_weights is None:
        ensemble_weights = {
            'yolo11s': 1.0,      # 범용 모델 기준
            'best': 1.1,         # 커스텀 학습 모델 (가장 높은 가중치)
            'best_friged': 0.9   # 냉장고 특화 모델 (중간 가중치)
        }
    
    # 앙상블 수행
    final_detections = ensemble_detections(all_detections, confidence_weights=ensemble_weights)
    
    print(f"✅ 3가지 모델 앙상블 완료: {len(final_detections)}개 최종 객체")
    
    # 상세 통계 정보 출력
    ensemble_stats = {}
    consensus_count = 0
    
    for detection in final_detections:
        count = detection['ensemble_count']
        if count not in ensemble_stats:
            ensemble_stats[count] = 0
        ensemble_stats[count] += 1
        
        if detection['ensemble_info']['is_consensus']:
            consensus_count += 1
    
    print(f"📊 앙상블 통계:")
    print(f"   - 1개 모델 탐지: {ensemble_stats.get(1, 0)}개")
    print(f"   - 2개 모델 합의: {ensemble_stats.get(2, 0)}개")
    print(f"   - 3개 모델 합의: {ensemble_stats.get(3, 0)}개")
    print(f"   - 전체 합의 객체: {consensus_count}개 ({consensus_count/len(final_detections)*100:.1f}%)")
    
    return final_detections, all_detections

# 3가지 YOLO 앙상블 모델 로드
ensemble_models = load_ensemble_models()

# 환경 변수 확인
print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"MONGODB_URI 설정: {bool(MONGODB_URI)}")

@app.get("/")
async def root():
    return {
        "message": "Food Detection API with 3-Model Ensemble YOLO",
        "version": "3.0.0",
        "status": "running",
        "ensemble_models": {
            "loaded_models": list(ensemble_models.keys()),
            "model_count": len(ensemble_models),
            "target_models": ["yolo11s", "best", "best_friged"],
            "ensemble_enabled": len(ensemble_models) > 1,
            "full_ensemble": len(ensemble_models) == 3
        },
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

# ===== 수정된 API 엔드포인트들 =====

@app.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.5, use_ensemble: bool = True):
    """3가지 YOLO 앙상블 식품 탐지"""
    if not ensemble_models:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"📁 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        if use_ensemble and len(ensemble_models) > 1:
            print(f"🤖 3가지 모델 앙상블 탐지 시작 (신뢰도: {confidence})")
            detections, model_results = detect_objects_ensemble(ensemble_models, image_path, confidence)
            
            # 합의 객체와 단독 탐지 분류
            consensus_detections = [d for d in detections if d['ensemble_info']['is_consensus']]
            single_detections = [d for d in detections if not d['ensemble_info']['is_consensus']]
            
            response = {
                "detections": detections,
                "ensemble_info": {
                    "models_used": list(ensemble_models.keys()),
                    "total_detections": len(detections),
                    "consensus_detections": len(consensus_detections),
                    "single_detections": len(single_detections),
                    "consensus_rate": f"{len(consensus_detections)/len(detections)*100:.1f}%" if detections else "0%",
                    "individual_results": {
                        model_name: len(results) for model_name, results in model_results.items()
                    },
                    "ensemble_ready": len(ensemble_models) == 3
                }
            }
        else:
            # 단일 모델 사용 (첫 번째 사용 가능한 모델)
            model_name, model = next(iter(ensemble_models.items()))
            print(f"🔍 단일 모델 탐지 시작: {model_name} (신뢰도: {confidence})")
            detections, _ = detect_objects(model, image_path, confidence)
            
            response = {
                "detections": detections,
                "model_used": model_name,
                "ensemble_enabled": False,
                "available_models": list(ensemble_models.keys())
            }
        
        print(f"✅ 탐지 완료: {len(detections)}개 객체")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return response
        
    except Exception as e:
        print(f"❌ 탐지 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")

@app.post("/api/detect/single/{model_name}")
async def detect_food_single_model(model_name: str, file: UploadFile = File(...), confidence: float = 0.5):
    """특정 단일 모델로 식품 탐지 (3가지 모델 중 선택)"""
    if model_name not in ensemble_models:
        available_models = list(ensemble_models.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"모델 '{model_name}'을 찾을 수 없습니다. 사용 가능한 모델: {available_models}"
        )
    
    try:
        print(f"📁 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"🔍 {model_name} 모델 단독 탐지 시작 (신뢰도: {confidence})")
        model = ensemble_models[model_name]
        detections, _ = detect_objects(model, image_path, confidence)
        print(f"✅ {model_name} 탐지 완료: {len(detections)}개 객체")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "detections": detections,
            "model_used": model_name,
            "total_detections": len(detections),
            "other_available_models": [m for m in ensemble_models.keys() if m != model_name]
        }
        
    except Exception as e:
        print(f"❌ {model_name} 탐지 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{model_name} 탐지 오류: {str(e)}")

@app.get("/api/models/info")
async def get_models_info():
    """로드된 3가지 모델 정보 조회"""
    model_info = {}
    target_models = ["yolo11s", "best", "best_friged"]
    
    for model_name in target_models:
        if model_name in ensemble_models:
            try:
                model = ensemble_models[model_name]
                model_info[model_name] = {
                    "loaded": True,
                    "model_type": str(type(model).__name__),
                    "available": True,
                    "status": "ready"
                }
            except Exception as e:
                model_info[model_name] = {
                    "loaded": False,
                    "error": str(e),
                    "available": False,
                    "status": "error"
                }
        else:
            model_info[model_name] = {
                "loaded": False,
                "available": False,
                "status": "not_found",
                "file_path": f"models/{model_name}.pt"
            }
    
    return {
        "target_models": target_models,
        "ensemble_models": model_info,
        "loaded_count": len(ensemble_models),
        "target_count": len(target_models),
        "ensemble_ready": len(ensemble_models) > 1,
        "full_ensemble": len(ensemble_models) == 3,
        "missing_models": [name for name in target_models if name not in ensemble_models]
    }

@app.post("/api/detect/ensemble/custom")
async def detect_food_custom_ensemble(
    file: UploadFile = File(...), 
    confidence: float = 0.5,
    yolo11s_weight: float = 1.0,
    best_weight: float = 1.2,
    best_friged_weight: float = 1.1,
    iou_threshold: float = 0.5
):
    """커스텀 가중치로 3가지 모델 앙상블 탐지"""
    if not ensemble_models:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"📁 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 커스텀 가중치 설정
        custom_weights = {
            'yolo11s': yolo11s_weight,
            'best': best_weight,
            'best_friged': best_friged_weight
        }
        
        print(f"🤖 커스텀 가중치 앙상블 탐지 시작")
        print(f"   가중치: {custom_weights}")
        print(f"   IoU 임계값: {iou_threshold}")
        
        # 각 모델별 탐지
        all_detections = {}
        for model_name, model in ensemble_models.items():
            try:
                detections, _ = detect_objects(model, image_path, confidence)
                all_detections[model_name] = detections
                print(f"   {model_name}: {len(detections)}개 탐지")
            except Exception as e:
                print(f"   {model_name} 오류: {e}")
                all_detections[model_name] = []
        
        # 커스텀 앙상블 수행
        final_detections = ensemble_detections(
            all_detections, 
            iou_threshold=iou_threshold, 
            confidence_weights=custom_weights
        )
        
        print(f"✅ 커스텀 앙상블 완료: {len(final_detections)}개 최종 객체")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "detections": final_detections,
            "custom_ensemble_info": {
                "weights_used": custom_weights,
                "iou_threshold": iou_threshold,
                "models_used": list(ensemble_models.keys()),
                "total_detections": len(final_detections),
                "individual_results": {
                    model_name: len(results) for model_name, results in all_detections.items()
                }
            }
        }
        
    except Exception as e:
        print(f"❌ 커스텀 앙상블 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"커스텀 앙상블 오류: {str(e)}")

# ===== 기존 API 엔드포인트들 (OCR, Gemini) =====

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
            "analysisMethod": fridge_data.analysisMethod or "ensemble",
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

# ===== 간소화된 저장 API 엔드포인트 =====

@app.post("/api/fridge/save-simple")
async def save_simple_fridge_data(fridge_data: SimpleFridgeData):
    """간소화된 형식으로 냉장고 식재료 데이터를 MongoDB에 저장"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"💾 간소화된 냉장고 데이터 저장 시작 - 사용자: {fridge_data.userId}")
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
        
        # 간소화된 데이터 저장 (사용자가 원하는 형식만)
        current_time = datetime.now().isoformat()
        
        # $setOnInsert에는 새 문서 생성 시에만 설정할 필드들
        insert_only_document = {
            "createdAt": current_time
        }
        
        # $set에는 업데이트할 필드들 (createdAt 제외)
        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "updatedAt": current_time
        }
        
        result = await fridge_collection.update_one(
            {"userId": fridge_data.userId},
            {
                "$set": update_document,
                "$setOnInsert": insert_only_document
            },
            upsert=True
        )
        
        print(f"✅ 간소화된 MongoDB 저장 완료")
        print(f"   - 사용자: {fridge_data.userId}")
        print(f"   - 식재료: {len(fridge_data.ingredients)}개")
        print(f"   - 신규 생성: {result.upserted_id is not None}")
        print(f"   - 저장된 필드: userId, ingredients, createdAt")
        
        return {
            "success": True,
            "message": f"간소화된 냉장고 데이터가 {DB_NAME}.{COLLECTION_NAME}에 성공적으로 저장되었습니다",
            "userId": fridge_data.userId,
            "totalIngredients": len(fridge_data.ingredients),
            "isNew": result.upserted_id is not None,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "documentId": str(result.upserted_id) if result.upserted_id else "updated",
                "format": "simplified"
            },
            "savedFields": ["userId", "ingredients", "createdAt"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 간소화된 MongoDB 저장 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"간소화된 저장 중 오류 발생: {str(e)}")

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

# 간소화된 불러오기 API
@app.get("/api/fridge/load-simple/{user_id}")
async def load_simple_fridge_data(user_id: str):
    """간소화된 형식으로 사용자별 냉장고 데이터 불러오기"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"📥 간소화된 냉장고 데이터 로드 시작 - 사용자: {user_id}")
        
        # MongoDB에서 사용자 데이터 검색
        fridge_data = await fridge_collection.find_one({"userId": user_id})
        
        if not fridge_data:
            print(f"⚠️ 데이터 없음 - 사용자: {user_id}")
            return {
                "success": False,
                "message": "저장된 냉장고 데이터가 없습니다",
                "ingredients": []
            }
        
        # _id 필드 제거 (JSON 직렬화를 위해)
        fridge_data.pop("_id", None)
        
        # 간소화된 형식으로 반환 (필요한 필드만)
        simplified_data = {
            "userId": fridge_data.get("userId"),
            "ingredients": fridge_data.get("ingredients", []),
            "createdAt": fridge_data.get("createdAt")
        }
        
        print(f"✅ 간소화된 MongoDB 로드 완료")
        print(f"   - 사용자: {user_id}")
        print(f"   - 식재료: {len(simplified_data['ingredients'])}개")
        
        return {
            "success": True,
            "message": f"간소화된 데이터를 {DB_NAME}.{COLLECTION_NAME}에서 성공적으로 불러왔습니다",
            **simplified_data
        }
    
    except Exception as e:
        print(f"❌ 간소화된 MongoDB 로드 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"간소화된 데이터 로드 중 오류 발생: {str(e)}")

# ===== 버전3 데이터 마이그레이션 API =====

@app.get("/api/fridge/load-v3/{user_id}")
async def load_v3_fridge_data(user_id: str):
    """버전3에서 저장된 냉장고 데이터를 현재 형식으로 변환하여 불러오기"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"📥 버전3 데이터 로드 시작 - 사용자: {user_id}")
        
        # 여러 가능한 버전3 컬렉션/필드에서 데이터 검색
        v3_collections = [
            f"{COLLECTION_NAME}_v3",
            f"{COLLECTION_NAME}_old", 
            "fridge_v3",
            "ingredients_v3",
            "food_data_v3"
        ]
        
        v3_data = None
        found_collection = None
        
        # 버전3 컬렉션들에서 데이터 검색
        for collection_name in v3_collections:
            try:
                v3_collection = db[collection_name]
                data = await v3_collection.find_one({"userId": user_id})
                if data:
                    v3_data = data
                    found_collection = collection_name
                    break
            except Exception as e:
                print(f"   컬렉션 {collection_name} 검색 실패: {e}")
                continue
        
        # 현재 컬렉션에서 이전 형식 데이터 검색
        if not v3_data:
            current_data = await fridge_collection.find_one({"userId": user_id})
            if current_data:
                # 이미 현재 형식이면 그대로 반환
                if "ingredients" in current_data and isinstance(current_data["ingredients"], list):
                    if current_data["ingredients"]:
                        print(f"✅ 현재 컬렉션에서 데이터 발견: {len(current_data['ingredients'])}개")
                        return {
                            "success": True,
                            "data": current_data["ingredients"],
                            "source": "current_format",
                            "collection": COLLECTION_NAME,
                            "message": "현재 형식의 데이터를 반환했습니다"
                        }
                
                # 이전 형식일 수 있는 데이터 처리
                v3_data = current_data
                found_collection = COLLECTION_NAME
        
        if not v3_data:
            return {
                "success": False,
                "message": "버전3 또는 이전 형식의 데이터를 찾을 수 없습니다",
                "searched_collections": v3_collections + [COLLECTION_NAME]
            }
        
        # 버전3 데이터 변환
        v3_ingredients = None
        
        # 다양한 필드명에서 재료 데이터 추출
        for field_name in ["ingredients", "data", "items", "foods", "detected_items"]:
            if field_name in v3_data and v3_data[field_name]:
                v3_ingredients = v3_data[field_name]
                break
        
        if not v3_ingredients:
            return {
                "success": False,
                "message": "버전3 데이터에서 식재료 정보를 찾을 수 없습니다",
                "available_fields": list(v3_data.keys()),
                "source_collection": found_collection
            }
        
        # 현재 형식으로 변환
        converted_data = convert_v3_to_current_format(v3_ingredients)
        
        print(f"✅ 버전3 데이터 변환 완료")
        print(f"   - 원본: {len(v3_ingredients)}개 항목")
        print(f"   - 변환: {len(converted_data)}개 항목") 
        print(f"   - 출처: {found_collection}")
        
        return {
            "success": True,
            "data": converted_data,
            "source": "v3_migration",
            "collection": found_collection,
            "original_count": len(v3_ingredients),
            "converted_count": len(converted_data),
            "message": f"버전3 데이터를 성공적으로 변환했습니다 ({found_collection})"
        }
        
    except Exception as e:
        print(f"❌ 버전3 데이터 로드 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"버전3 데이터 로드 중 오류 발생: {str(e)}")

@app.post("/api/fridge/migrate-v3/{user_id}")
async def migrate_v3_to_current(user_id: str):
    """버전3 데이터를 찾아서 현재 형식으로 마이그레이션"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"🔄 버전3 데이터 마이그레이션 시작 - 사용자: {user_id}")
        
        # 버전3 데이터 불러오기
        v3_response = await load_v3_fridge_data(user_id)
        
        if not v3_response["success"]:
            return {
                "success": False,
                "message": "마이그레이션할 버전3 데이터가 없습니다",
                "details": v3_response
            }
        
        converted_data = v3_response["data"]
        
        # 현재 형식으로 저장
        current_time = datetime.now().isoformat()
        
        migration_document = {
            "userId": user_id,
            "ingredients": converted_data,
            "timestamp": current_time,
            "totalCount": sum(item["quantity"] for item in converted_data),
            "totalTypes": len(converted_data),
            "analysisMethod": "v3_migration",
            "deviceInfo": "migration_tool",
            "migrationInfo": {
                "sourceCollection": v3_response["collection"],
                "migrationDate": current_time,
                "originalCount": v3_response["original_count"],
                "convertedCount": v3_response["converted_count"]
            },
            "updatedAt": current_time,
            "createdAt": current_time
        }
        
        # 기존 데이터 덮어쓰기
        result = await fridge_collection.replace_one(
            {"userId": user_id},
            migration_document,
            upsert=True
        )
        
        print(f"✅ 버전3 데이터 마이그레이션 완료")
        print(f"   - 변환된 항목: {len(converted_data)}개")
        print(f"   - 저장 위치: {DB_NAME}.{COLLECTION_NAME}")
        
        return {
            "success": True,
            "message": "버전3 데이터를 현재 형식으로 성공적으로 마이그레이션했습니다",
            "migrationInfo": {
                "userId": user_id,
                "sourceCollection": v3_response["collection"],
                "migratedItems": len(converted_data),
                "totalCount": migration_document["totalCount"],
                "totalTypes": migration_document["totalTypes"],
                "targetCollection": f"{DB_NAME}.{COLLECTION_NAME}",
                "migrationDate": current_time
            }
        }
        
    except Exception as e:
        print(f"❌ 버전3 마이그레이션 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"마이그레이션 중 오류 발생: {str(e)}")

# ===== 시스템 상태 확인 API =====

@app.get("/health")
async def health_check():
    """전체 시스템 상태 확인"""
    mongodb_status = "connected" if fridge_collection is not None else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0 - 3-Model Ensemble + V3 Migration + Simple Save",
        "services": {
            "ensemble_models": {
                "target_models": ["yolo11s", "best", "best_friged"],
                "loaded_models": list(ensemble_models.keys()),
                "loaded_count": len(ensemble_models),
                "target_count": 3,
                "ensemble_ready": len(ensemble_models) > 1,
                "full_ensemble": len(ensemble_models) == 3
            },
            "mongodb": mongodb_status,
            "ocr": "configured" if os.environ.get('CLOVA_OCR_API_URL') else "not_configured",
            "gemini": "configured" if os.environ.get('GEMINI_API_KEY') else "not_configured",
            "v3_migration": "available",
            "simple_save": "available"
        },
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None
        },
        "temp_dir_exists": os.path.exists("temp"),
        "missing_models": [name for name in ["yolo11s", "best", "best_friged"] if name not in ensemble_models],
        "new_features": [
            "V3 데이터 마이그레이션 지원",
            "3가지 YOLO 모델 앙상블",
            "커스텀 가중치 앙상블",
            "MongoDB 냉장고 데이터 관리",
            "간소화된 저장 형식 지원 (/api/fridge/save-simple)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 3-Model Ensemble Food Detection API + V3 Migration + Simple Save 서버 시작 중...")
    print(f"📍 서버 주소: http://0.0.0.0:8000")
    print(f"📋 API 문서: http://0.0.0.0:8000/docs")
    print(f"🤖 타겟 앙상블 모델: yolo11s.pt, best.pt, best_friged.pt")
    print(f"🤖 로드된 모델: {list(ensemble_models.keys())} ({len(ensemble_models)}/3)")
    print(f"🔗 MongoDB 연결: {'✅ 성공' if fridge_collection is not None else '❌ 실패'}")
    print(f"🗄️ 저장 위치: {DB_NAME}.{COLLECTION_NAME}")
    print(f"🔄 V3 마이그레이션: ✅ 지원됨")
    print(f"💾 간소화된 저장: ✅ /api/fridge/save-simple")
    if len(ensemble_models) < 3:
        print(f"⚠️ 경고: 3개 모델 중 {len(ensemble_models)}개만 로드됨")
    uvicorn.run(app, host="0.0.0.0", port=8000)