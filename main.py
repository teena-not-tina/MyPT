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
import cv2
import base64
import json
from io import BytesIO
from PIL import Image as PILImage
from collections import Counter

# 기존 모듈들
from modules.yolo_detector import detect_objects, load_yolo_model
from modules.ocr_processor import extract_text_with_ocr, analyze_brands_in_text, smart_ocr_analysis
from modules.gemini import analyze_text_with_gemini

# ===== 🆕 통합: 고도화된 분석 클래스들 =====
class EnhancedAnalyzer:
    """향상된 이미지 분석 클래스 - 팀원 버전과 완전 통합"""
    
    def __init__(self, models_dict):
        self.models = models_dict
    
    def analyze_colors(self, image):
        """향상된 색상 분석 - 채소 최적화"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 배경 마스킹 추가
            _, mask = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 30, 255, cv2.THRESH_BINARY)
            mask2 = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 240, 255, cv2.THRESH_BINARY_INV)[1]
            final_mask = cv2.bitwise_and(mask, mask2)
            
            # 채소별 최적화된 색상 범위
            color_ranges = {
                "양배추초록": [(25, 20, 40), (85, 150, 220)],
                "양배추노랑": [(20, 30, 60), (45, 120, 200)],
                "진한빨간색": [(0, 150, 100), (10, 255, 255)],
                "연한빨간색": [(0, 80, 80), (10, 150, 200)],
                "진한주황색": [(11, 120, 100), (20, 255, 255)],
                "연한주황색": [(11, 60, 80), (25, 150, 200)],
                "진한노란색": [(20, 120, 100), (30, 255, 255)],
                "연한노란색": [(25, 40, 80), (35, 120, 200)],
                "진한초록색": [(40, 120, 80), (70, 255, 200)],
                "중간초록색": [(35, 80, 60), (75, 180, 180)],
                "연한초록색": [(30, 30, 40), (85, 120, 160)],
                "황록색": [(25, 40, 60), (40, 120, 180)],
                "진한보라색": [(120, 120, 80), (140, 255, 200)],
                "연한보라색": [(110, 60, 60), (130, 150, 150)],
                "진한갈색": [(8, 50, 30), (20, 180, 120)],
                "연한갈색": [(10, 20, 40), (25, 80, 140)],
                "베이지색": [(15, 15, 60), (30, 60, 160)],
                "흰색": [(0, 0, 200), (180, 30, 255)],
                "회색": [(0, 0, 80), (180, 20, 180)]
            }
            
            # 마스크된 영역에서만 색상 계산
            color_percentages = {}
            total_pixels = np.sum(final_mask > 0)
            
            if total_pixels > 0:
                for color_name, (lower, upper) in color_ranges.items():
                    lower = np.array(lower)
                    upper = np.array(upper)
                    
                    color_mask = cv2.inRange(hsv, lower, upper)
                    color_mask = cv2.bitwise_and(color_mask, final_mask)
                    color_pixels = np.sum(color_mask > 0)
                    
                    percentage = (color_pixels / total_pixels) * 100
                    if percentage > 3:
                        color_percentages[color_name] = round(percentage, 1)
            
            # 색상 그룹별 통합 분석
            grouped_colors = self._group_similar_colors(color_percentages)
            
            # 주요 색상 순서대로 정렬
            dominant_colors = sorted(color_percentages.items(), key=lambda x: x[1], reverse=True)
            
            # 채소 인식 우선 색상 선택
            primary_color = self._select_primary_color_for_vegetables(grouped_colors, dominant_colors)
            
            return {
                "dominant_colors": dominant_colors[:3],
                "color_distribution": color_percentages,
                "grouped_colors": grouped_colors,
                "primary_color": primary_color
            }
            
        except Exception as e:
            print(f"❌ 색상 분석 실패: {e}")
            return {"dominant_colors": [], "color_distribution": {}, "primary_color": "알수없음"}
    
    def _group_similar_colors(self, color_percentages):
        """유사 색상 그룹화"""
        groups = {
            "빨간계열": ["진한빨간색", "연한빨간색"],
            "주황계열": ["진한주황색", "연한주황색"],
            "노란계열": ["진한노란색", "연한노란색"],
            "초록계열": ["진한초록색", "중간초록색", "연한초록색", "황록색"],
            "보라계열": ["진한보라색", "연한보라색"],
            "갈색계열": ["진한갈색", "연한갈색", "베이지색"],
            "흰색계열": ["흰색", "회색"]
        }
        
        grouped = {}
        for group_name, colors in groups.items():
            total_percentage = sum(color_percentages.get(color, 0) for color in colors)
            if total_percentage > 5:
                grouped[group_name] = {
                    "total_percentage": total_percentage,
                    "dominant_color": max(colors, key=lambda c: color_percentages.get(c, 0))
                }
        
        return grouped
    
    def _select_primary_color_for_vegetables(self, grouped_colors, dominant_colors):
        """채소 인식에 최적화된 주요 색상 선택"""
        if "초록계열" in grouped_colors:
            return grouped_colors["초록계열"]["dominant_color"]
        
        return dominant_colors[0][0] if dominant_colors else "알수없음"
    
    def analyze_shapes(self, image):
        """모양 분석"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes_found = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:
                    continue
                
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                
                shape_info = self._classify_shape(approx, aspect_ratio, area)
                shape_info.update({
                    "area": int(area),
                    "aspect_ratio": round(aspect_ratio, 2),
                    "bounding_box": [x, y, w, h]
                })
                
                shapes_found.append(shape_info)
            
            shapes_found.sort(key=lambda x: x["area"], reverse=True)
            
            return {
                "total_objects": len(shapes_found),
                "shapes": shapes_found[:5],
                "primary_shape": shapes_found[0]["shape"] if shapes_found else "알수없음"
            }
            
        except Exception as e:
            print(f"❌ 모양 분석 실패: {e}")
            return {"total_objects": 0, "shapes": [], "primary_shape": "알수없음"}
    
    def _classify_shape(self, approx, aspect_ratio, area):
        """모양 분류"""
        vertices = len(approx)
        
        if vertices == 3:
            return {"shape": "삼각형", "description": "뾰족한 형태"}
        elif vertices == 4:
            if 0.95 <= aspect_ratio <= 1.05:
                return {"shape": "정사각형", "description": "네모난 형태"}
            else:
                return {"shape": "직사각형", "description": "길쭉한 형태"}
        elif vertices > 8:
            perimeter = cv2.arcLength(approx, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularity > 0.7:
                if aspect_ratio > 1.5:
                    return {"shape": "타원형", "description": "길쭉한 원형 (바나나형)"}
                else:
                    return {"shape": "원형", "description": "둥근 형태 (사과, 토마토형)"}
            else:
                return {"shape": "불규칙형", "description": "복잡한 형태"}
        else:
            return {"shape": f"{vertices}각형", "description": "다각형 형태"}
    
    def predict_vegetable_by_properties(self, color, shape):
        """색상과 모양으로 채소 예측"""
        predictions = []
        
        # 색상 + 모양 조합 규칙
        detailed_rules = {
            ("진한빨간색", "원형"): ["토마토", "빨간파프리카"],
            ("진한빨간색", "불규칙형"): ["빨간파프리카", "토마토"],
            ("진한주황색", "원형"): ["단호박", "당근"],
            ("진한주황색", "직사각형"): ["당근"],
            ("진한주황색", "타원형"): ["당근", "고구마"],
            ("진한초록색", "불규칙형"): ["브로콜리", "시금치", "케일"],
            ("진한초록색", "원형"): ["브로콜리", "양배추심"],
            ("중간초록색", "직사각형"): ["오이", "피망"],
            ("중간초록색", "불규칙형"): ["피망", "청경채", "상추"],
            ("연한초록색", "불규칙형"): ["양배추", "상추", "배추", "청경채"],
            ("연한초록색", "원형"): ["양배추", "상추"],
            ("황록색", "불규칙형"): ["연한양배추", "셀러리", "배추"],
            ("진한보라색", "타원형"): ["가지"],
            ("진한보라색", "원형"): ["자색양파", "가지"],
            ("흰색", "불규칙형"): ["양배추", "무", "양파", "마늘", "배추"],
            ("흰색", "원형"): ["양파", "마늘", "무"]
        }
        
        # 정확한 매칭 시도
        key = (color, shape)
        if key in detailed_rules:
            predictions.extend(detailed_rules[key])
            print(f"🎯 정확 매칭: {color} + {shape} → {detailed_rules[key]}")
            return predictions
        
        # 색상만으로 예측
        color_priority_rules = {
            "진한초록색": ["브로콜리", "시금치", "케일", "피망"],
            "중간초록색": ["오이", "피망", "상추", "청경채"],
            "연한초록색": ["양배추", "상추", "배추", "청경채"],
            "황록색": ["양배추", "셀러리", "배추", "파"],
            "진한빨간색": ["토마토", "빨간파프리카", "고추"],
            "진한주황색": ["당근", "단호박", "고구마"],
            "진한보라색": ["가지", "자색양파", "보라양배추"],
            "흰색": ["양배추", "무", "양파", "마늘", "배추", "대파"]
        }
        
        if color in color_priority_rules:
            predictions.extend(color_priority_rules[color])
            print(f"🎨 색상 우선 예측: {color} → {color_priority_rules[color]}")
        
        if not predictions:
            predictions = ["양배추", "상추", "무", "당근", "감자"]
            print(f"❓ 기본 채소 예측: {predictions}")
        
        return predictions[:3]

    def enhanced_vegetable_analysis(self, image, confidence=0.5):
        """채소 전용 향상 분석"""
        try:
            print("🥗 채소 전용 분석 시작...")
            
            # 1. 향상된 색상 분석
            color_analysis = self.analyze_colors(image)
            
            # 2. 모양 분석
            shape_analysis = self.analyze_shapes(image)
            
            # 3. 채소 특화 예측
            primary_color = color_analysis.get("primary_color", "")
            primary_shape = shape_analysis.get("primary_shape", "")
            
            vegetable_predictions = self.predict_vegetable_by_properties(primary_color, primary_shape)
            
            # 4. 신뢰도 계산
            base_score = 0.6
            if primary_color != "알수없음":
                base_score += 0.2
            if primary_shape != "알수없음":
                base_score += 0.15
            
            confidence_score = min(0.95, base_score)
            
            result = {
                "success": True,
                "vegetable_analysis": {
                    "predicted_vegetables": vegetable_predictions,
                    "confidence": confidence_score,
                    "color_analysis": color_analysis,
                    "shape_analysis": shape_analysis,
                    "analysis_method": "vegetable_specialized"
                }
            }
            
            print(f"✅ 채소 분석 완료: {vegetable_predictions}")
            return result
            
        except Exception as e:
            print(f"❌ 채소 분석 실패: {e}")
            return {"success": False, "error": f"채소 분석 오류: {str(e)}"}

# FastAPI 앱 생성
app = FastAPI(title="통합 Food Detection API with 3-Model Ensemble + Enhanced Analysis", version="4.0.0")

# CORS 설정 강화 (팀원 버전 유지)
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

# MongoDB 설정 - 팀원 방식 완전 유지
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@192.168.0.199:27017")
DB_NAME = "test"  # 팀원 설정 유지
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "be-fit")  # 팀원 설정 유지

if MONGODB_URI:
    try:
        # 팀원의 MongoDB 설정 방식 완전 유지
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

# Pydantic 모델 정의 (팀원 버전 + 고도화 필드 추가)
class Ingredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: Optional[float] = 0.8
    source: str = "analysis"
    bbox: Optional[List[float]] = None
    originalClass: Optional[str] = None
    ensemble_info: Optional[Dict] = None
    color_info: Optional[str] = None  # 🆕 추가
    shape_info: Optional[str] = None  # 🆕 추가
    
    class Config:
        from_attributes = True

class FridgeData(BaseModel):
    userId: str
    ingredients: List[Ingredient]
    timestamp: str
    totalCount: int
    totalTypes: int
    analysisMethod: Optional[str] = "ensemble"
    deviceInfo: Optional[str] = None
    
    class Config:
        from_attributes = True

# ===== 간소화된 데이터 모델 (팀원 버전 유지) =====
class SimpleIngredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: float
    source: str

class SimpleFridgeData(BaseModel):
    userId: str
    ingredients: List[SimpleIngredient]

# ===== 버전3 데이터 마이그레이션 관련 모델 (팀원 버전 유지) =====
class V3IngredientData(BaseModel):
    """버전3 호환 식재료 데이터 모델"""
    name: Optional[str] = None
    ingredient: Optional[str] = None
    food: Optional[str] = None
    foodName: Optional[str] = None
    quantity: Optional[int] = 1
    count: Optional[int] = None
    amount: Optional[int] = None
    confidence: Optional[float] = 0.5
    source: Optional[str] = "v3_migration"

def convert_v3_to_current_format(v3_data):
    """버전3 데이터를 현재 형식으로 변환 (팀원 버전 유지)"""
    if not v3_data:
        return []
    
    converted_ingredients = []
    
    for idx, item in enumerate(v3_data):
        if isinstance(item, str):
            converted_ingredients.append({
                "id": idx + 1,
                "name": item,
                "quantity": 1,
                "confidence": 0.7,
                "source": "v3_text_migration"
            })
        elif isinstance(item, dict):
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

# ===== 3가지 YOLO 모델 앙상블 (팀원 버전 + 확장) =====
def load_ensemble_models():
    """3가지 YOLO 앙상블 모델들을 로드 (팀원 코드 기반)"""
    models = {}
    model_paths = {
        'yolo11s': 'models/yolo11s.pt',
        'best': 'models/best.pt',
        'best_friged': 'models/best_fri.pt'  # 팀원 버전 유지
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
    
    if len(models) == 0:
        print("⚠️ 경고: 로드된 모델이 없습니다!")
    elif len(models) < 3:
        print(f"⚠️ 경고: 3개 모델 중 {len(models)}개만 로드됨")
    
    return models

def calculate_iou(box1, box2):
    """두 바운딩 박스 간의 IoU(Intersection over Union) 계산 (팀원 버전 유지)"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)
    
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0
    
    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0

def ensemble_detections(detections_dict, iou_threshold=0.5, confidence_weights=None):
    """여러 모델의 탐지 결과를 앙상블하여 최종 결과 생성 (팀원 버전 유지)"""
    if not detections_dict:
        return []
    
    # 3가지 모델에 최적화된 기본 가중치 설정 (팀원 버전)
    if confidence_weights is None:
        confidence_weights = {
            'yolo11s': 1.1,      
            'best': 1.1,         
            'best_friged': 0.8   
        }
    
    all_detections = []
    
    for model_name, detections in detections_dict.items():
        model_weight = confidence_weights.get(model_name, 1.0)
        
        for detection in detections:
            weighted_confidence = detection['confidence'] * model_weight
            
            enhanced_detection = {
                **detection,
                'confidence': weighted_confidence,
                'original_confidence': detection['confidence'],
                'model_source': model_name,
                'model_weight': model_weight
            }
            all_detections.append(enhanced_detection)
    
    all_detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    final_detections = []
    
    for current_detection in all_detections:
        should_keep = True
        current_bbox = current_detection['bbox']
        
        for kept_detection in final_detections:
            kept_bbox = kept_detection['bbox']
            
            if (current_detection['class'] == kept_detection['class'] and 
                calculate_iou(current_bbox, kept_bbox) > iou_threshold):
                should_keep = False
                
                if 'ensemble_sources' not in kept_detection:
                    kept_detection['ensemble_sources'] = [kept_detection['model_source']]
                    kept_detection['ensemble_confidences'] = [kept_detection['original_confidence']]
                    kept_detection['ensemble_weights'] = [kept_detection['model_weight']]
                
                kept_detection['ensemble_sources'].append(current_detection['model_source'])
                kept_detection['ensemble_confidences'].append(current_detection['original_confidence'])
                kept_detection['ensemble_weights'].append(current_detection['model_weight'])
                
                weighted_sum = sum(conf * weight for conf, weight in 
                                 zip(kept_detection['ensemble_confidences'], kept_detection['ensemble_weights']))
                weight_sum = sum(kept_detection['ensemble_weights'])
                kept_detection['confidence'] = weighted_sum / weight_sum if weight_sum > 0 else kept_detection['confidence']
                kept_detection['ensemble_count'] = len(kept_detection['ensemble_sources'])
                
                break
        
        if should_keep:
            current_detection['ensemble_sources'] = [current_detection['model_source']]
            current_detection['ensemble_confidences'] = [current_detection['original_confidence']]
            current_detection['ensemble_weights'] = [current_detection['model_weight']]
            current_detection['ensemble_count'] = 1
            final_detections.append(current_detection)
    
    for detection in final_detections:
        detection['ensemble_info'] = {
            'models_used': detection['ensemble_sources'],
            'individual_confidences': dict(zip(detection['ensemble_sources'], detection['ensemble_confidences'])),
            'model_weights': dict(zip(detection['ensemble_sources'], detection['ensemble_weights'])),
            'ensemble_count': detection['ensemble_count'],
            'final_confidence': detection['confidence'],
            'is_consensus': detection['ensemble_count'] >= 2
        }
    
    return final_detections

def detect_objects_ensemble(models, image_path, confidence=0.5, ensemble_weights=None):
    """3가지 앙상블 모델을 사용한 객체 탐지 (팀원 버전 유지)"""
    if not models:
        raise ValueError("로드된 모델이 없습니다")
    
    print(f"🔍 3가지 모델 앙상블 탐지 시작 - 모델 수: {len(models)}")
    
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
    
    # 3가지 모델에 최적화된 앙상블 가중치 설정 (팀원 버전)
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

# 🆕 향상된 분석기 인스턴스 생성
enhanced_analyzer = EnhancedAnalyzer(ensemble_models)

# 이미지 전처리 함수 추가
def preprocess_image(image_path, max_size=640):
    """이미지 전처리"""
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지 파일을 읽을 수 없습니다: {image_path}")
        
        h, w = image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return image
    except Exception as e:
        print(f"❌ 이미지 전처리 실패: {e}")
        return None

# 환경 변수 확인 (팀원 버전 유지)
print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"MONGODB_URI 설정: {bool(MONGODB_URI)}")

@app.get("/")
async def root():
    return {
        "message": "통합 Food Detection API with 3-Model Ensemble + Enhanced Analysis",
        "version": "4.0.0",
        "status": "running",
        "features": {
            "team_original_features": {
                "ensemble_models": True,
                "mongodb_integration": True,
                "v3_migration": True,
                "simple_save": True
            },
            "enhanced_features": {
                "color_analysis": True,
                "shape_analysis": True,
                "vegetable_specialized": True,
                "brand_ocr_mapping": True,
                "smart_pattern_analysis": True,
                "comprehensive_analysis": True
            }
        },
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

# ===== 🆕 통합된 API 엔드포인트들 =====

@app.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.5, use_ensemble: bool = True):
    """기존 3가지 YOLO 앙상블 식품 탐지 (팀원 버전 완전 유지)"""
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

@app.post("/api/detect/enhanced")
async def enhanced_detect_food(
    file: UploadFile = File(...), 
    confidence: float = 0.5, 
    use_ensemble: bool = True, 
    use_enhanced_analysis: bool = True
):
    """🆕 향상된 YOLO 앙상블 + 색상/모양 분석 식품 탐지"""
    if not ensemble_models:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"📁 향상된 분석 시작: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 이미지 전처리
        image = preprocess_image(image_path)
        if image is None:
            raise HTTPException(status_code=400, detail="이미지 처리 실패")
        
        response = {}
        
        # 1단계: YOLO 앙상블 탐지 (팀원 방식)
        if use_ensemble and len(ensemble_models) > 1:
            print(f"🤖 앙상블 탐지 시작 (신뢰도: {confidence})")
            detections, model_results = detect_objects_ensemble(ensemble_models, image_path, confidence)
            
            response["yolo_detections"] = {
                "detections": detections,
                "ensemble_info": {
                    "models_used": list(ensemble_models.keys()),
                    "total_detections": len(detections),
                    "individual_results": {
                        model_name: len(results) for model_name, results in model_results.items()
                    }
                }
            }
        else:
            # 단일 모델 사용
            model_name, model = next(iter(ensemble_models.items()))
            print(f"🔍 단일 모델 탐지: {model_name} (신뢰도: {confidence})")
            detections, _ = detect_objects(model, image_path, confidence)
            
            response["yolo_detections"] = {
                "detections": detections,
                "model_used": model_name,
                "ensemble_enabled": False
            }
        
        # 2단계: 향상된 색상/모양 분석
        enhanced_analysis = None
        if use_enhanced_analysis:
            print("🎨 향상된 색상/모양 분석 시작...")
            enhanced_analysis = enhanced_analyzer.enhanced_vegetable_analysis(image, confidence)
            response["enhanced_analysis"] = enhanced_analysis
            
            # 3단계: 기존 YOLO 결과와 향상된 분석 결과 통합
            if enhanced_analysis.get("success") and detections:
                print("🔄 결과 통합 중...")
                integrated_detections = []
                
                vegetable_predictions = enhanced_analysis["vegetable_analysis"]["predicted_vegetables"]
                color_info = enhanced_analysis["vegetable_analysis"]["color_analysis"]["primary_color"]
                shape_info = enhanced_analysis["vegetable_analysis"]["shape_analysis"]["primary_shape"]
                enhanced_confidence = enhanced_analysis["vegetable_analysis"]["confidence"]
                
                for detection in detections:
                    # 낮은 신뢰도 또는 불분명한 클래스를 향상된 분석 결과로 교체
                    if (detection.get("confidence", 0) < 0.6 or 
                        detection.get("class") in ["item", "unknown", "object"]):
                        
                        if vegetable_predictions:
                            detection["class"] = vegetable_predictions[0]
                            detection["originalClass"] = detection.get("class", "unknown")
                            detection["confidence"] = enhanced_confidence
                            detection["source"] = "enhanced_analysis"
                            detection["color_info"] = color_info
                            detection["shape_info"] = shape_info
                            detection["alternative_predictions"] = vegetable_predictions[1:3]
                    
                    integrated_detections.append(detection)
                
                response["integrated_detections"] = integrated_detections
                response["integration_applied"] = True
                
                print(f"✅ 통합 완료: {len(integrated_detections)}개 객체")
            else:
                response["integration_applied"] = False
        
        # 최종 통계
        final_detections = response.get("integrated_detections", response["yolo_detections"]["detections"])
        response["final_summary"] = {
            "total_detections": len(final_detections),
            "detected_items": list(set(det.get("class", "unknown") for det in final_detections)),
            "analysis_methods_used": []
        }
        
        if use_ensemble:
            response["final_summary"]["analysis_methods_used"].append("ensemble_yolo")
        else:
            response["final_summary"]["analysis_methods_used"].append("single_yolo")
            
        if use_enhanced_analysis:
            response["final_summary"]["analysis_methods_used"].append("enhanced_color_shape")
        
        print(f"✅ 향상된 탐지 완료: {len(final_detections)}개 객체")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return response
        
    except Exception as e:
        print(f"❌ 향상된 탐지 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"향상된 탐지 오류: {str(e)}")

@app.post("/api/detect/single/{model_name}")
async def detect_food_single_model(model_name: str, file: UploadFile = File(...), confidence: float = 0.5):
    """특정 단일 모델로 식품 탐지 (팀원 버전 유지)"""
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

@app.post("/api/detect/ensemble/custom")
async def detect_food_custom_ensemble(
    file: UploadFile = File(...), 
    confidence: float = 0.5,
    yolo11s_weight: float = 1.0,
    best_weight: float = 1.2,
    best_friged_weight: float = 1.1,
    iou_threshold: float = 0.5
):
    """커스텀 가중치로 3가지 모델 앙상블 탐지 (팀원 버전 유지)"""
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

# ===== 🆕 향상된 분석 API 엔드포인트들 =====

@app.post("/api/analyze/vegetable-specialized")
async def vegetable_specialized_analysis(file: UploadFile = File(...), confidence: float = 0.5):
    """🆕 채소 전용 특화 분석"""
    try:
        print(f"🥗 채소 전용 분석 시작: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 이미지 전처리
        image = preprocess_image(image_path)
        if image is None:
            raise HTTPException(status_code=400, detail="이미지 처리 실패")
        
        # 채소 전용 분석 실행
        result = enhanced_analyzer.enhanced_vegetable_analysis(image, confidence)
        
        if result.get("success"):
            # 결과를 Ingredient 형식으로 변환
            predictions = result["vegetable_analysis"]["predicted_vegetables"]
            confidence_score = result["vegetable_analysis"]["confidence"]
            color_info = result["vegetable_analysis"]["color_analysis"]["primary_color"]
            shape_info = result["vegetable_analysis"]["shape_analysis"]["primary_shape"]
            
            ingredients = []
            for i, vegetable in enumerate(predictions):
                ingredient = {
                    "id": i + 1,
                    "name": vegetable,
                    "quantity": 1,
                    "confidence": confidence_score,
                    "source": "vegetable_specialized",
                    "color_info": color_info,
                    "shape_info": shape_info,
                    "bbox": None
                }
                ingredients.append(ingredient)
            
            result["formatted_ingredients"] = ingredients
            result["ingredient_count"] = len(ingredients)
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        print(f"❌ 채소 전용 분석 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"채소 전용 분석 오류: {str(e)}")

@app.post("/api/analyze/color-shape")
async def color_shape_analysis(file: UploadFile = File(...)):
    """🆕 색상 및 모양 분석 전용 API"""
    try:
        print(f"🎨 색상/모양 분석: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 이미지 전처리
        image = preprocess_image(image_path)
        if image is None:
            raise HTTPException(status_code=400, detail="이미지 처리 실패")
        
        # 색상 분석
        color_analysis = enhanced_analyzer.analyze_colors(image)
        
        # 모양 분석
        shape_analysis = enhanced_analyzer.analyze_shapes(image)
        
        # 예측 생성
        primary_color = color_analysis.get("primary_color", "")
        primary_shape = shape_analysis.get("primary_shape", "")
        predictions = enhanced_analyzer.predict_vegetable_by_properties(primary_color, primary_shape)
        
        result = {
            "success": True,
            "color_analysis": color_analysis,
            "shape_analysis": shape_analysis,
            "predictions": {
                "vegetables": predictions,
                "primary_color": primary_color,
                "primary_shape": primary_shape,
                "confidence": "높음" if primary_color != "알수없음" and primary_shape != "알수없음" else "보통"
            }
        }
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        print(f"❌ 색상/모양 분석 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"색상/모양 분석 오류: {str(e)}")

@app.post("/api/analyze/comprehensive")
async def comprehensive_food_analysis(
    file: UploadFile = File(...), 
    confidence: float = 0.5,
    use_ensemble: bool = True,
    use_enhanced_analysis: bool = True,
    include_color_shape: bool = True
):
    """🆕 종합적인 식품 분석 - 모든 기능 통합"""
    try:
        print(f"🔬 종합 분석 시작: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 이미지 전처리
        image = preprocess_image(image_path)
        if image is None:
            raise HTTPException(status_code=400, detail="이미지 처리 실패")
        
        analysis_results = {
            "success": True,
            "analysis_methods": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. YOLO 앙상블 탐지 (팀원 방식)
        if use_ensemble and len(ensemble_models) > 1:
            print("🤖 앙상블 YOLO 분석...")
            detections, model_results = detect_objects_ensemble(ensemble_models, image_path, confidence)
            analysis_results["yolo_ensemble"] = {
                "detections": detections,
                "model_results": model_results,
                "models_used": list(ensemble_models.keys())
            }
            analysis_results["analysis_methods"].append("yolo_ensemble")
        else:
            print("🔍 단일 YOLO 분석...")
            model_name, model = next(iter(ensemble_models.items()))
            detections, _ = detect_objects(model, image_path, confidence)
            analysis_results["yolo_single"] = {
                "detections": detections,
                "model_used": model_name
            }
            analysis_results["analysis_methods"].append("yolo_single")
        
        # 2. 색상/모양 분석
        if include_color_shape:
            print("🎨 색상/모양 분석...")
            color_analysis = enhanced_analyzer.analyze_colors(image)
            shape_analysis = enhanced_analyzer.analyze_shapes(image)
            
            analysis_results["color_shape_analysis"] = {
                "color_analysis": color_analysis,
                "shape_analysis": shape_analysis
            }
            analysis_results["analysis_methods"].append("color_shape")
        
        # 3. 채소 전용 분석
        if use_enhanced_analysis:
            print("🥗 채소 전용 분석...")
            vegetable_analysis = enhanced_analyzer.enhanced_vegetable_analysis(image, confidence)
            analysis_results["vegetable_specialized"] = vegetable_analysis
            analysis_results["analysis_methods"].append("vegetable_specialized")
        
        # 4. 결과 통합 및 최종 추천
        print("🔄 결과 통합...")
        
        # 모든 탐지 결과 수집
        all_detections = []
        
        # YOLO 결과
        yolo_detections = (
            analysis_results.get("yolo_ensemble", {}).get("detections", []) or
            analysis_results.get("yolo_single", {}).get("detections", [])
        )
        all_detections.extend(yolo_detections)
        
        # 채소 전용 분석 결과
        if use_enhanced_analysis and analysis_results.get("vegetable_specialized", {}).get("success"):
            vegetable_predictions = analysis_results["vegetable_specialized"]["vegetable_analysis"]["predicted_vegetables"]
            vegetable_confidence = analysis_results["vegetable_specialized"]["vegetable_analysis"]["confidence"]
            
            # 낮은 신뢰도의 YOLO 결과를 채소 예측으로 교체
            for i, detection in enumerate(all_detections):
                if detection.get("confidence", 0) < 0.6:
                    if vegetable_predictions:
                        all_detections[i]["enhanced_prediction"] = vegetable_predictions[0]
                        all_detections[i]["enhanced_confidence"] = vegetable_confidence
                        all_detections[i]["enhanced_alternatives"] = vegetable_predictions[1:3]
                        all_detections[i]["enhanced_applied"] = True
        
        # 최종 요약
        detected_items = list(set(
            det.get("enhanced_prediction", det.get("class", "unknown")) 
            for det in all_detections
        ))
        
        analysis_results["final_summary"] = {
            "total_detections": len(all_detections),
            "unique_items": detected_items,
            "item_count": len(detected_items),
            "analysis_methods_used": analysis_results["analysis_methods"],
            "confidence_distribution": {
                "high": sum(1 for det in all_detections if det.get("confidence", 0) > 0.7),
                "medium": sum(1 for det in all_detections if 0.4 <= det.get("confidence", 0) <= 0.7),
                "low": sum(1 for det in all_detections if det.get("confidence", 0) < 0.4)
            },
            "enhanced_predictions_applied": sum(1 for det in all_detections if det.get("enhanced_applied", False))
        }
        
        analysis_results["integrated_detections"] = all_detections
        
        print(f"✅ 종합 분석 완료: {len(detected_items)}개 고유 아이템")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ 종합 분석 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"종합 분석 오류: {str(e)}")

# ===== OCR 관련 API (팀원 기존 + 고도화 기능) =====

@app.post("/api/ocr")
async def extract_ocr_text(file: UploadFile = File(...)):
    """OCR 텍스트 추출 (팀원 버전 유지)"""
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

@app.post("/api/ocr/enhanced")
async def enhanced_ocr_analysis(file: UploadFile = File(...)):
    """🆕 향상된 OCR 분석 - 브랜드 매핑 포함"""
    try:
        print(f"📁 향상된 OCR 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"🧠 향상된 OCR 분석 시작")
        
        # 1. 기본 OCR 텍스트 추출
        ocr_text = extract_text_with_ocr(image_path)
        
        if not ocr_text:
            return {
                "success": False,
                "error": "OCR 추출 실패",
                "ocr_text": "",
                "brand_analysis": [],
                "total_products": 0
            }
        
        # 2. 브랜드 기반 제품 분석
        brand_products = analyze_brands_in_text(ocr_text)
        
        # 3. 스마트 OCR 분석 (패턴 분석)
        smart_analysis = smart_ocr_analysis(ocr_text)
        
        # 4. 결과 통합
        all_products = brand_products + smart_analysis.get("products", [])
        
        result = {
            "success": True,
            "ocr_text": ocr_text,
            "brand_analysis": brand_products,
            "smart_analysis": smart_analysis,
            "all_products": all_products,
            "total_products": len(all_products),
            "enhancement_applied": len(all_products) > 0
        }
        
        print(f"✅ 향상된 OCR 완료: {len(all_products)}개 제품")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        print(f"❌ 향상된 OCR 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"향상된 OCR 오류: {str(e)}")

@app.post("/api/analyze/brand-detection")
async def brand_detection_only(request_data: dict):
    """🆕 브랜드 탐지만 수행 (텍스트 입력)"""
    try:
        text = request_data.get("text", "")
        
        if not text:
            return {"success": False, "error": "분석할 텍스트가 없습니다"}
        
        # 브랜드 매핑 분석
        brand_results = analyze_brands_in_text(text)
        
        # 스마트 패턴 분석
        smart_results = smart_ocr_analysis(text)
        
        # 결과 통합
        all_results = brand_results + smart_results.get("products", [])
        
        return {
            "success": True,
            "brand_products": brand_results,
            "smart_products": smart_results.get("products", []),
            "all_products": all_results,
            "total_found": len(all_results),
            "analysis_method": "enhanced_brand_mapping",
            "original_text": text
        }
        
    except Exception as e:
        print(f"❌ 브랜드 탐지 오류: {e}")
        raise HTTPException(status_code=500, detail=f"브랜드 탐지 오류: {str(e)}")

# ===== Gemini 분석 API (팀원 버전 유지) =====

@app.post("/api/analyze")
async def analyze_with_gemini(request_data: dict):
    """Gemini AI 분석 (팀원 버전 유지)"""
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

# ===== 모델 정보 API =====

@app.get("/api/models/info")
async def get_models_info():
    """로드된 3가지 모델 정보 조회 (팀원 버전 확장)"""
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
        "missing_models": [name for name in target_models if name not in ensemble_models],
        "enhanced_features": {
            "color_analysis": True,
            "shape_analysis": True,
            "vegetable_specialized": True,
            "brand_ocr_mapping": True,
            "smart_pattern_analysis": True
        }
    }

# ===== MongoDB 냉장고 식재료 관리 API (팀원 버전 완전 유지 + 향상된 필드 지원) =====

@app.post("/api/fridge/save")
async def save_fridge_data(fridge_data: FridgeData):
    """냉장고 식재료 데이터를 MongoDB에 저장 (팀원 버전 + 향상된 필드 지원)"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"💾 냉장고 데이터 저장 시작 - 사용자: {fridge_data.userId}")
        print(f"🗄️ 저장 위치: {DB_NAME}.{COLLECTION_NAME}")
        
        # Pydantic V2 호환: model_dump() 사용 (팀원 방식)
        ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]
        
        # MongoDB 연결 상태 확인 (팀원 방식)
        try:
            await client.admin.command('ping')
            print("✅ MongoDB 연결 상태 정상")
        except Exception as conn_err:
            print(f"❌ MongoDB 연결 확인 실패: {conn_err}")
            raise HTTPException(status_code=503, detail="MongoDB 연결이 불안정합니다")
        
        # 데이터 저장 (팀원 방식 유지)
        current_time = datetime.now().isoformat()
        
        # $set에는 업데이트할 필드들만 포함 (createdAt 제외)
        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "timestamp": fridge_data.timestamp,
            "totalCount": fridge_data.totalCount,
            "totalTypes": fridge_data.totalTypes,
            "analysisMethod": fridge_data.analysisMethod or "enhanced_ensemble",  # 🆕 확장
            "deviceInfo": fridge_data.deviceInfo or "web_app",
            "updatedAt": current_time,
            "enhanced_features": True  # 🆕 향상된 기능 사용 표시
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
        
        # 🆕 색상/모양 정보가 포함된 재료들 카운트
        enhanced_ingredients = [
            ing for ing in ingredients_dict 
            if ing.get("color_info") or ing.get("shape_info")
        ]
        
        print(f"✅ MongoDB 저장 완료")
        print(f"   - 사용자: {fridge_data.userId}")
        print(f"   - 식재료: {fridge_data.totalTypes}종류 {fridge_data.totalCount}개")
        print(f"   - 향상된 분석 적용: {len(enhanced_ingredients)}개")
        print(f"   - 신규 생성: {result.upserted_id is not None}")
        
        return {
            "success": True,
            "message": f"냉장고 데이터가 {DB_NAME}.{COLLECTION_NAME}에 성공적으로 저장되었습니다",
            "userId": fridge_data.userId,
            "totalTypes": fridge_data.totalTypes,
            "totalCount": fridge_data.totalCount,
            "enhanced_analysis_count": len(enhanced_ingredients),  # 🆕 추가
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

# ===== 간소화된 저장 API 엔드포인트 (팀원 버전 완전 유지) =====

@app.post("/api/fridge/save-simple")
async def save_simple_fridge_data(fridge_data: SimpleFridgeData):
    """간소화된 형식으로 냉장고 식재료 데이터를 MongoDB에 저장 (팀원 버전 유지)"""
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
        
        # 간소화된 데이터 저장 (팀원 방식)
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
    """MongoDB에서 사용자별 냉장고 데이터 불러오기 (팀원 버전 + 향상된 통계)"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"📥 냉장고 데이터 로드 시작 - 사용자: {user_id}")
        print(f"🗄️ 검색 위치: {DB_NAME}.{COLLECTION_NAME}")
        
        # MongoDB에서 사용자 데이터 검색 (팀원 방식)
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
        
        # 🆕 향상된 분석 결과 통계
        enhanced_count = 0
        if "ingredients" in fridge_data:
            enhanced_count = sum(
                1 for ing in fridge_data["ingredients"] 
                if ing.get("color_info") or ing.get("shape_info")
            )
        
        print(f"✅ MongoDB 로드 완료")
        print(f"   - 사용자: {user_id}")
        print(f"   - 식재료: {fridge_data.get('totalTypes', 0)}종류")
        print(f"   - 향상된 분석: {enhanced_count}개")
        
        return {
            "success": True,
            "message": f"{DB_NAME}.{COLLECTION_NAME}에서 데이터를 성공적으로 불러왔습니다",
            "enhanced_analysis_count": enhanced_count,  # 🆕 추가
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

# 간소화된 불러오기 API (팀원 버전 완전 유지)
@app.get("/api/fridge/load-simple/{user_id}")
async def load_simple_fridge_data(user_id: str):
    """간소화된 형식으로 사용자별 냉장고 데이터 불러오기 (팀원 버전 유지)"""
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

# ===== 버전3 데이터 마이그레이션 API (팀원 버전 완전 유지) =====

@app.get("/api/fridge/load-v3/{user_id}")
async def load_v3_fridge_data(user_id: str):
    """버전3에서 저장된 냉장고 데이터를 현재 형식으로 변환하여 불러오기 (팀원 버전 유지)"""
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB가 연결되지 않았습니다")
    
    try:
        print(f"📥 버전3 데이터 로드 시작 - 사용자: {user_id}")
        
        # 여러 가능한 버전3 컬렉션/필드에서 데이터 검색 (팀원 방식)
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
        
        # 버전3 데이터 변환 (팀원 함수 사용)
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
        
        # 현재 형식으로 변환 (팀원 함수 사용)
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
    """버전3 데이터를 찾아서 현재 형식으로 마이그레이션 (팀원 버전 유지)"""
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
        
        # 현재 형식으로 저장 (팀원 방식)
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
    """전체 시스템 상태 확인 (팀원 버전 + 고도화 기능 통합)"""
    mongodb_status = "connected" if fridge_collection is not None else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0 - 팀원 최신 + 고도화 기능 완전 통합",
        "integration_info": {
            "team_features_preserved": [
                "3-Model Ensemble YOLO",
                "MongoDB 냉장고 관리",
                "V3 데이터 마이그레이션",
                "간소화된 저장 형식",
                "기존 API 100% 호환성"
            ],
            "enhanced_features_added": [
                "향상된 색상 분석 (채소 최적화)",
                "모양 분석 및 분류",
                "채소 전용 특화 분석",
                "브랜드 매핑 OCR",
                "스마트 패턴 분석",
                "종합 분석 API"
            ]
        },
        "services": {
            "ensemble_models": {
                "target_models": ["yolo11s", "best", "best_friged"],
                "loaded_models": list(ensemble_models.keys()),
                "loaded_count": len(ensemble_models),
                "target_count": 3,
                "ensemble_ready": len(ensemble_models) > 1,
                "full_ensemble": len(ensemble_models) == 3
            },
            "enhanced_analysis": {
                "color_analysis": True,
                "shape_analysis": True,
                "vegetable_specialized": True,
                "pattern_recognition": True
            },
            "ocr_services": {
                "basic_clova_ocr": "configured" if os.environ.get('CLOVA_OCR_API_URL') else "not_configured",
                "brand_mapping": True,
                "smart_pattern_analysis": True
            },
            "mongodb": mongodb_status,
            "gemini": "configured" if os.environ.get('GEMINI_API_KEY') else "not_configured",
            "v3_migration": "available",
            "simple_save": "available"
        },
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None
        },
        "api_endpoints": {
            "team_original": [
                "/api/detect (3-Model Ensemble)",
                "/api/detect/single/{model_name}",
                "/api/detect/ensemble/custom",
                "/api/ocr",
                "/api/analyze (Gemini)",
                "/api/fridge/save",
                "/api/fridge/save-simple",
                "/api/fridge/load/{user_id}",
                "/api/fridge/load-simple/{user_id}",
                "/api/fridge/load-v3/{user_id}",
                "/api/fridge/migrate-v3/{user_id}"
            ],
            "enhanced_new": [
                "/api/detect/enhanced",
                "/api/analyze/vegetable-specialized",
                "/api/analyze/color-shape",
                "/api/analyze/comprehensive",
                "/api/ocr/enhanced",
                "/api/analyze/brand-detection"
            ]
        },
        "temp_dir_exists": os.path.exists("temp"),
        "missing_models": [name for name in ["yolo11s", "best", "best_friged"] if name not in ensemble_models],
        "compatibility": {
            "react_frontend": "100% 호환",
            "existing_apis": "100% 유지",
            "mongodb_structure": "완전 호환",
            "v3_migration": "완전 지원"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 통합 Food Detection API 서버 시작 중...")
    print("=" * 60)
    print("📋 통합 정보:")
    print("  🔵 팀원 최신 버전 (완전 유지):")
    print("    - 3가지 YOLO 앙상블 모델")
    print("    - MongoDB 냉장고 식재료 관리")
    print("    - V3 데이터 마이그레이션")
    print("    - 간소화된 저장/로드 API")
    print("    - 기존 API 엔드포인트 100% 호환")
    print("  🟠 고도화 기능 (추가):")
    print("    - 향상된 색상 분석 (채소 최적화)")
    print("    - 모양 분석 및 분류")
    print("    - 채소 전용 특화 분석")
    print("    - 브랜드 매핑 OCR")
    print("    - 스마트 패턴 분석")
    print("    - 종합 분석 API")
    print("=" * 60)
    print(f"📍 서버 주소: http://0.0.0.0:8000")
    print(f"📋 API 문서: http://0.0.0.0:8000/docs")
    print(f"🤖 타겟 앙상블 모델: yolo11s.pt, best.pt, best_friged.pt")
    print(f"🤖 로드된 모델: {list(ensemble_models.keys())} ({len(ensemble_models)}/3)")
    print(f"🔗 MongoDB 연결: {'✅ 성공' if fridge_collection is not None else '❌ 실패'}")
    print(f"🗄️ 저장 위치: {DB_NAME}.{COLLECTION_NAME}")
    print(f"🔄 V3 마이그레이션: ✅ 지원됨")
    print(f"💾 간소화된 저장: ✅ /api/fridge/save-simple")
    print(f"🎨 향상된 분석: ✅ 색상/모양/채소 특화")
    if len(ensemble_models) < 3:
        print(f"⚠️ 경고: 3개 모델 중 {len(ensemble_models)}개만 로드됨")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)