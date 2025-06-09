# modules/yolo_detector.py - 기존 API 유지하면서 개선

import cv2
import numpy as np
from ultralytics import YOLO
import os
import shutil
from collections import Counter
from io import BytesIO
from PIL import Image as PILImage
import re
import json

# ===== 🔧 JSON 설정 로더 (기존 유지) =====
def load_json_config(config_file, default_data):
    """JSON 설정 파일 로드 또는 기본값 생성"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            print(f"📝 기본 설정 파일 생성: {config_file}")
            return default_data
    except Exception as e:
        print(f"❌ 설정 파일 로드 실패 ({config_file}): {e}")
        return default_data

# ===== 🔧 설정 파일들 로드 (기존 유지) =====
brand_config = load_json_config("config/brand_mapping.json", {"brand_mappings": {}})
BRAND_MAPPINGS = brand_config.get('brand_mappings', {})

korean_config = load_json_config("config/korean_class_mapping.json", {"korean_class_mapping": {}})
KOREAN_CLASS_MAPPING = korean_config.get('korean_class_mapping', {})

color_config = load_json_config("config/color_food_mapping.json", {"color_ranges": {}, "correction_rules": []})
COLOR_RANGES = color_config.get('color_ranges', {})

# 🆕 일반화된 보정 규칙 로드
correction_config = load_json_config("config/correction_rules.json", {
    "correction_rules": [
        {
            "name": "orange_correction",
            "conditions": {
                "detected_class": ["potato"],
                "color_match": ["진한주황색", "연한주황색", "주황빨간색"],
                "confidence_threshold": 0.85
            },
            "actions": {
                "new_class": "orange",
                "new_korean_name": "오렌지",
                "confidence_boost": 0.1,
                "max_confidence": 0.92
            }
        }
    ]
})
CORRECTION_RULES = correction_config.get('correction_rules', [])

print(f"✅ 설정 로드 완료: 브랜드 {len(BRAND_MAPPINGS)}개, 한국어 {len(KOREAN_CLASS_MAPPING)}개, 보정규칙 {len(CORRECTION_RULES)}개")

# ===== 모델 캐시 시스템 (기존 유지) =====
_model_cache = {}

def get_cached_model(model_path):
    """캐시된 모델 반환 (메모리 효율성)"""
    if model_path not in _model_cache:
        _model_cache[model_path] = load_yolo_model(model_path)
    return _model_cache[model_path]

def clear_model_cache():
    """모델 캐시 초기화"""
    global _model_cache
    _model_cache.clear()
    print("🗑️ 모델 캐시가 초기화되었습니다")

# ===== 기존 함수들 유지 =====
def load_yolo_model(model_path=None):
    """YOLO 모델 로드 - 기존 그대로"""
    if model_path is None:
        model_path = "models/yolo11s.pt"
    
    try:
        if not os.path.exists(model_path):
            print(f"❌ 모델 파일이 존재하지 않습니다: {model_path}")
            os.makedirs("models", exist_ok=True)
            
            if "yolo11s.pt" in model_path:
                print("📥 YOLO11s 모델 다운로드 중...")
                model = YOLO('yolo11s.pt')
                if os.path.exists('yolo11s.pt'):
                    shutil.move('yolo11s.pt', model_path)
                    print(f"✅ 모델을 {model_path}로 이동완료")
                return model
            else:
                print(f"⚠️ {model_path} 파일을 수동으로 models/ 폴더에 배치해주세요")
                return None
        
        print(f"📦 YOLO 모델 로딩 중: {model_path}")
        model = YOLO(model_path)
        print(f"✅ 모델 로드 성공: {model_path}")
        
        return model
        
    except Exception as e:
        print(f"❌ YOLO 모델 로드 실패: {e}")
        return None

def detect_objects(model, image_path, confidence_threshold=0.5, save_result=False):
    """기본 YOLO 객체 탐지 - 기존 그대로"""
    if model is None:
        raise ValueError("모델이 로드되지 않았습니다")
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    
    try:
        print(f"🔍 객체 탐지 시작: {image_path}")
        print(f"   신뢰도 임계값: {confidence_threshold}")
        
        results = model(image_path, conf=confidence_threshold, verbose=False)
        
        detections = []
        result_image_path = None
        
        for i, result in enumerate(results):
            boxes = result.boxes
            
            if boxes is not None and len(boxes) > 0:
                print(f"   탐지된 객체 수: {len(boxes)}")
                
                for j, box in enumerate(boxes):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = model.names[class_id]
                    korean_name = KOREAN_CLASS_MAPPING.get(class_name, class_name)
                    
                    detection = {
                        'id': j,
                        'class': class_name,
                        'korean_name': korean_name,
                        'confidence': round(confidence, 3),
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'center': [float((x1 + x2) / 2), float((y1 + y2) / 2)],
                        'width': float(x2 - x1),
                        'height': float(y2 - y1),
                        'area': float((x2 - x1) * (y2 - y1))
                    }
                    
                    detections.append(detection)
                    
                    print(f"      {j+1}. {korean_name}({class_name}) - 신뢰도: {confidence:.3f}")
                
                if save_result:
                    try:
                        result_dir = "results"
                        os.makedirs(result_dir, exist_ok=True)
                        
                        base_name = os.path.splitext(os.path.basename(image_path))[0]
                        result_image_path = os.path.join(result_dir, f"{base_name}_detected.jpg")
                        
                        annotated_img = result.plot()
                        cv2.imwrite(result_image_path, annotated_img)
                        print(f"📸 결과 이미지 저장: {result_image_path}")
                        
                    except Exception as save_error:
                        print(f"⚠️ 결과 이미지 저장 실패: {save_error}")
                        result_image_path = None
            else:
                print("   탐지된 객체가 없습니다")
        
        print(f"✅ 탐지 완료: 총 {len(detections)}개 객체")
        
        return detections, result_image_path
        
    except Exception as e:
        print(f"❌ 객체 탐지 오류: {e}")
        raise

def filter_food_detections(detections, food_keywords=None):
    """음식 관련 탐지 결과만 필터링 - 기존 그대로"""
    if food_keywords is None:
        food_keywords = [
            'apple', 'banana', 'orange', 'strawberry', 'grape', 'watermelon',
            'pineapple', 'peach', 'pear', 'kiwi', 'lemon', 'lime', 'mango',
            'cherry', 'plum', 'carrot', 'broccoli', 'cabbage', 'lettuce', 'spinach',
            'onion', 'garlic', 'potato', 'tomato', 'cucumber', 'pepper', 'corn',
            'mushroom', 'eggplant', 'radish', 'bean', 'pumpkin',
            'beef', 'pork', 'chicken', 'fish', 'salmon', 'tuna', 'shrimp',
            'crab', 'lobster', 'squid', 'octopus', 'egg',
            'milk', 'cheese', 'butter', 'yogurt', 'cream',
            'rice', 'bread', 'noodle', 'pasta', 'cereal',
            'water', 'juice', 'coffee', 'tea', 'soda', 'beer', 'wine',
            'salt', 'sugar', 'oil', 'honey', 'jam', 'nut'
        ]
    
    food_detections = []
    
    for detection in detections:
        class_name = detection['class'].lower()
        
        if any(keyword in class_name for keyword in food_keywords) or \
           detection['class'] in KOREAN_CLASS_MAPPING:
            food_detections.append(detection)
    
    print(f"🍎 음식 관련 객체 필터링: {len(detections)} → {len(food_detections)}개")
    
    return food_detections

def merge_similar_detections(detections, iou_threshold=0.5):
    """유사한 위치의 탐지 결과들을 병합 - 기존 그대로"""
    if len(detections) <= 1:
        return detections
    """IoU 계산 함수"""
    def calculate_iou(box1, box2):
        """IoU 계산"""
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
    
    sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    merged_detections = []
    
    for current in sorted_detections:
        merged = False
        
        for i, existing in enumerate(merged_detections):
            iou = calculate_iou(current['bbox'], existing['bbox'])
            # 클래스 같고 IoU 기준 충족시 병합
            if current['class'] == existing['class'] and  iou > iou_threshold:
                if current['confidence'] > existing['confidence']:
                    merged_detections[i] = current
                merged = True
                break
            elif iou > 0.75:
                print(f"⚠️ 클래스 다르지만 IoU {iou:.2f} → 병합 시도: {existing['class']} → {current['class']}")
                if current['confidence'] > existing['confidence']:
                    merged_detections[i] = current
                merged = True
                break
        # 25.06.08 겹치는 영역이 있으면 클래스 달라도 덮어쓰기 병합 시도 
        if not merged:
            merged_detections.append(current)
    
    print(f"🔄 중복 제거: {len(detections)} → {len(merged_detections)}개")
    
    return merged_detections

def analyze_detection_results(detections):
    """탐지 결과 분석 및 통계 생성 - 기존 그대로"""
    if not detections:
        return {
            'total_objects': 0,
            'unique_classes': 0,
            'class_counts': {},
            'confidence_stats': {},
            'size_distribution': {}
        }
    
    class_counts = {}
    confidences = []
    sizes = []
    
    for detection in detections:
        class_name = detection['korean_name']
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        confidences.append(detection['confidence'])
        sizes.append(detection['area'])
    
    confidence_stats = {
        'average': round(np.mean(confidences), 3),
        'min': round(np.min(confidences), 3),
        'max': round(np.max(confidences), 3),
        'std': round(np.std(confidences), 3)
    }
    
    size_stats = {
        'average': round(np.mean(sizes), 2),
        'min': round(np.min(sizes), 2),
        'max': round(np.max(sizes), 2),
        'std': round(np.std(sizes), 2)
    }
    
    analysis = {
        'total_objects': len(detections),
        'unique_classes': len(class_counts),
        'class_counts': class_counts,
        'confidence_stats': confidence_stats,
        'size_distribution': size_stats,
        'most_common_class': max(class_counts.items(), key=lambda x: x[1]) if class_counts else None,
        'highest_confidence': max(detections, key=lambda x: x['confidence']) if detections else None
    }
    
    return analysis

# ===== 🚀 Enhanced YOLO Detector - 개선된 버전 =====

class EnhancedYOLODetector:
    """향상된 YOLO 탐지기 - 일반화된 보정 규칙 적용"""
    
    def __init__(self, models_dict=None):
        self.models = models_dict or {}
        self.brand_mappings = BRAND_MAPPINGS
        self.correction_rules = CORRECTION_RULES  # 🆕 일반화된 보정 규칙
        print(f"🚀 Enhanced YOLO 초기화: {len(self.models)}개 모델, {len(self.brand_mappings)}개 브랜드, {len(self.correction_rules)}개 보정 규칙")
    
    def analyze_ocr_first(self, ocr_text):
        """OCR 우선 브랜드 인식 - 기존 그대로"""
        if not ocr_text or not ocr_text.strip():
            return None
        
        print(f"🔍 브랜드 인식 시작: '{ocr_text}'")
        
        normalized_text = ocr_text.lower().strip()
        
        for category, data in self.brand_mappings.items():
            for brand in data["brands"]:
                if brand.lower() in normalized_text:
                    print(f"✅ 브랜드 매칭: {brand} → {data['default_product']}")
                    
                    detected_product = data['default_product']
                    for product in data["common_products"]:
                        if product.lower() in normalized_text:
                            detected_product = product
                            break
                    
                    return {
                        "ingredient": detected_product,
                        "brand": brand,
                        "category": category,
                        "confidence": 0.95,
                        "source": "brand_mapping",
                        "ocr_text": ocr_text
                    }
        
        for category, data in self.brand_mappings.items():
            for product in data["common_products"]:
                if product.lower() in normalized_text:
                    print(f"✅ 제품 매칭: {product}")
                    return {
                        "ingredient": product,
                        "brand": "unknown",
                        "category": category,
                        "confidence": 0.85,
                        "source": "product_mapping",
                        "ocr_text": ocr_text
                    }
        
        print(f"❌ 브랜드/제품 매칭 실패")
        return None
    def preprocess_image(self, image_input):
        """이미지 경로 또는 BytesIO 객체 처리"""
        if isinstance(image_input, str) and os.path.exists(image_input):
            return cv2.imread(image_input)
        elif isinstance(image_input, BytesIO):
            image = PILImage.open(image_input).convert("RGB")
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            print("❌ 유효하지 않은 이미지 입력")
            return None
    # ===== 색상 및 모양 분석 기능 =====
    
    def analyze_colors(self, image):
        """향상된 색상 분석 - 모든 채소 최적화"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            # ===== 🆕 배경 마스킹 추가 =====
            # 너무 밝거나 어두운 영역 제외 (배경 제거)
            _, mask = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 30, 255, cv2.THRESH_BINARY)
            mask2 = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 240, 255, cv2.THRESH_BINARY_INV)[1]
            final_mask = cv2.bitwise_and(mask, mask2)
            
            # 마스크 적용된 영역만 색상 분석
            masked_hsv = cv2.bitwise_and(hsv, hsv, mask=final_mask)
            # ===== 🥗 채소별 최적화된 색상 범위 =====
            color_ranges = {
                "양배추초록": [(25, 20, 40), (85, 150, 220)],    # 매우 넓은 초록 범위
                "양배추노랑": [(20, 30, 60), (45, 120, 200)],    # 양배추 심 부분
                
                # 빨간색 계열
                "진한빨간색": [(0, 150, 100), (10, 255, 255)],      # 토마토, 빨간파프리카
                "연한빨간색": [(0, 80, 80), (10, 150, 200)],        # 분홍 무, 적상추
                
                # 주황색 계열  
                "진한주황색": [(11, 120, 100), (20, 255, 255)],     # 당근, 단호박
                "연한주황색": [(11, 60, 80), (25, 150, 200)],       # 연한 당근, 오렌지 파프리카
                
                # 노란색 계열
                "진한노란색": [(20, 120, 100), (30, 255, 255)],     # 노란 파프리카, 옥수수
                "연한노란색": [(25, 40, 80), (35, 120, 200)],       # 연한 양배추, 백색 양파
                
                # 초록색 계열 (가장 세분화)
                "진한초록색": [(40, 120, 80), (70, 255, 200)],      # 브로콜리, 시금치, 케일
                "중간초록색": [(35, 80, 60), (75, 180, 180)],       # 오이, 피망, 청경채
                "연한초록색": [(30, 30, 40), (85, 120, 160)],       # 양배추, 상추, 배추
                "황록색": [(25, 40, 60), (40, 120, 180)],           # 연한 양배추, 셀러리
                
                # 보라색 계열
                "진한보라색": [(120, 120, 80), (140, 255, 200)],    # 가지, 자색양파
                "연한보라색": [(110, 60, 60), (130, 150, 150)],     # 연한 가지, 보라양배추
                
                # 갈색/베이지 계열
                "진한갈색": [(8, 50, 30), (20, 180, 120)],          # 감자, 생강, 마늘껍질
                "연한갈색": [(10, 20, 40), (25, 80, 140)],          # 양파, 마늘, 연근
                "베이지색": [(15, 15, 60), (30, 60, 160)],          # 무, 연근, 죽순
                
                # 흰색 계열
                "흰색": [(0, 0, 200), (180, 30, 255)],              # 무, 양파, 마늘, 배추
                "회색": [(0, 0, 80), (180, 20, 180)]                # 더러운 감자, 땅이 묻은 채소
            }
            # 마스크된 영역에서만 색상 계산
            color_percentages = {}
            total_pixels = np.sum(final_mask > 0)  # 마스크된 픽셀만 카운트
            
            for color_name, (lower, upper) in color_ranges.items():
                lower = np.array(lower)
                upper = np.array(upper)
                
                color_mask = cv2.inRange(masked_hsv, lower, upper)
                color_pixels = np.sum(color_mask > 0)
                
                if total_pixels > 0:
                    percentage = (color_pixels / total_pixels) * 100
                    if percentage > 3:
                        color_percentages[color_name] = round(percentage, 1)
            color_percentages = {}
            total_pixels = image.shape[0] * image.shape[1]
            
            for color_name, (lower, upper) in color_ranges.items():
                lower = np.array(lower)
                upper = np.array(upper)
                
                mask = cv2.inRange(hsv, lower, upper)
                color_pixels = np.sum(mask > 0)
                percentage = (color_pixels / total_pixels) * 100
                
                if percentage > 3:  # 3% 이상인 색상만 기록 (더 민감하게)
                    color_percentages[color_name] = round(percentage, 1)
            
            # 색상 그룹별 통합 분석
            grouped_colors = self._group_similar_colors(color_percentages)
            
            # 주요 색상 순서대로 정렬
            dominant_colors = sorted(color_percentages.items(), key=lambda x: x[1], reverse=True)
            
            # 최적 색상 선택 (채소 인식 우선)
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
        # 초록계열이 있으면 우선 선택
        if "초록계열" in grouped_colors:
            return grouped_colors["초록계열"]["dominant_color"]
        
        # 그 외에는 가장 dominant한 색상 사용
        return dominant_colors[0][0] if dominant_colors else "알수없음"
    def analyze_shapes(self, image):
        """모양 분석"""
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 가우시안 블러 적용
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 엣지 검출
            edges = cv2.Canny(blurred, 50, 150)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes_found = []
            
            for contour in contours:
                # 면적이 너무 작은 윤곽선 제외
                area = cv2.contourArea(contour)
                if area < 1000:
                    continue
                
                # 윤곽선 근사화
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 경계 상자
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                
                # 모양 분류
                shape_info = self._classify_shape(approx, aspect_ratio, area)
                shape_info.update({
                    "area": int(area),
                    "aspect_ratio": round(aspect_ratio, 2),
                    "bounding_box": [x, y, w, h]
                })
                
                shapes_found.append(shape_info)
            
            # 면적 기준으로 정렬 (큰 것부터)
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
            # 원형성 계산
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

    def analyze_sizes(self, image):
        """크기 분석"""
        try:
            h, w = image.shape[:2]
            total_area = h * w
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 임계값 처리로 객체 분리
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            object_sizes = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # 최소 크기 필터
                    relative_size = (area / total_area) * 100
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    size_category = "소형"
                    if relative_size > 20:
                        size_category = "대형"
                    elif relative_size > 10:
                        size_category = "중형"
                    
                    object_sizes.append({
                        "absolute_area": int(area),
                        "relative_size": round(relative_size, 1),
                        "category": size_category,
                        "dimensions": [w, h]
                    })
            
            # 크기 순으로 정렬
            object_sizes.sort(key=lambda x: x["absolute_area"], reverse=True)
            
            return {
                "objects": object_sizes[:3],
                "size_distribution": self._categorize_sizes(object_sizes)
            }
            
        except Exception as e:
            print(f"❌ 크기 분석 실패: {e}")
            return {"objects": [], "size_distribution": {}}

    def analyze_shapes(self, image):
        """모양 분석"""
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 가우시안 블러 적용
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 엣지 검출
            edges = cv2.Canny(blurred, 50, 150)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes_found = []
            
            for contour in contours:
                # 면적이 너무 작은 윤곽선 제외
                area = cv2.contourArea(contour)
                if area < 1000:
                    continue
                
                # 윤곽선 근사화
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 경계 상자
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                
                # 모양 분류
                shape_info = self._classify_shape(approx, aspect_ratio, area)
                shape_info.update({
                    "area": int(area),
                    "aspect_ratio": round(aspect_ratio, 2),
                    "bounding_box": [x, y, w, h]
                })
                
                shapes_found.append(shape_info)
            
            # 면적 기준으로 정렬 (큰 것부터)
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
            # 원형성 계산
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
        
    def predict_food_by_color(self, primary_color):
        """색상 기반 식품 예측 - 기존 그대로"""
        color_food_map = {
            "진한주황색": ["오렌지", "당근", "단호박"],
            "연한주황색": ["오렌지", "감", "복숭아"],
            "주황빨간색": ["오렌지", "토마토", "빨간파프리카"],
            "진한초록색": ["브로콜리", "시금치", "케일"],
            "중간초록색": ["오이", "피망", "상추"],
            "연한초록색": ["양배추", "상추", "배추"],
            "진한빨간색": ["토마토", "빨간파프리카", "딸기"],
            "진한노란색": ["바나나", "노란파프리카", "옥수수"],
            "연한노란색": ["바나나", "양파", "레몬"],
            "진한보라색": ["가지", "자색양파", "포도"],
            "진한갈색": ["감자", "생강", "양파"],
            "흰색": ["양배추", "무", "마늘"]
        }
        
        return color_food_map.get(primary_color, ["사과", "바나나", "당근"])
    
    def apply_general_corrections(self, detections, color_analysis):
        """🆕 일반화된 보정 로직 적용"""
        primary_color = color_analysis.get("primary_color", "")
        
        for detection in detections:
            for rule in self.correction_rules:
                # 조건 확인
                conditions = rule.get("conditions", {})
                
                # 클래스 확인
                if "detected_class" in conditions:
                    if detection['class'] not in conditions["detected_class"]:
                        continue
                
                # 색상 확인
                if "color_match" in conditions:
                    if primary_color not in conditions["color_match"]:
                        continue
                
                # 신뢰도 확인
                if "confidence_threshold" in conditions:
                    if detection['confidence'] >= conditions["confidence_threshold"]:
                        continue
                
                # 형태 비율 확인 (선택적)
                if "shape_ratio" in conditions:
                    shape_ratio = conditions["shape_ratio"]
                    if "min_length_width_ratio" in shape_ratio:
                        ratio = detection['height'] / detection['width'] if detection['width'] > 0 else 0
                        if ratio < shape_ratio["min_length_width_ratio"]:
                            continue
                
                # 보정 적용
                actions = rule.get("actions", {})
                print(f"🔧 보정 적용: {rule.get('name', 'unknown')} - {detection['class']} → {actions.get('new_class', detection['class'])}")
                
                detection['original_class'] = detection['class']
                detection['original_korean_name'] = detection['korean_name']
                detection['class'] = actions.get('new_class', detection['class'])
                detection['korean_name'] = actions.get('new_korean_name', detection['korean_name'])
                
                # 신뢰도 조정
                if 'confidence_boost' in actions:
                    new_confidence = detection['confidence'] + actions['confidence_boost']
                    max_confidence = actions.get('max_confidence', 1.0)
                    detection['confidence'] = min(new_confidence, max_confidence)
                
                detection['correction_applied'] = True
                detection['correction_reason'] = f"{rule.get('name', 'unknown')}: {rule.get('description', '')}"
                
                break  # 첫 번째 매칭 규칙만 적용
        
        return detections
    def analyze_shapes(self, image):
        """모양 분석"""
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 가우시안 블러 적용
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 엣지 검출
            edges = cv2.Canny(blurred, 50, 150)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes_found = []
            
            for contour in contours:
                # 면적이 너무 작은 윤곽선 제외
                area = cv2.contourArea(contour)
                if area < 1000:
                    continue
                
                # 윤곽선 근사화
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 경계 상자
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                
                # 모양 분류
                shape_info = self._classify_shape(approx, aspect_ratio, area)
                shape_info.update({
                    "area": int(area),
                    "aspect_ratio": round(aspect_ratio, 2),
                    "bounding_box": [x, y, w, h]
                })
                
                shapes_found.append(shape_info)
            
            # 면적 기준으로 정렬 (큰 것부터)
            shapes_found.sort(key=lambda x: x["area"], reverse=True)
            
            return {
                "total_objects": len(shapes_found),
                "shapes": shapes_found[:5],
                "primary_shape": shapes_found[0]["shape"] if shapes_found else "알수없음"
            }
            
        except Exception as e:
            print(f"❌ 모양 분석 실패: {e}")
            return {"total_objects": 0, "shapes": [], "primary_shape": "알수없음"}
    def _predict_food_by_properties(self, color, shape, size_info):
        """색상과 모양으로 채소 예측 - 전체 채소 최적화"""
        predictions = []
        
        # ===== 🥗 채소별 상세 예측 규칙 =====
        
        # 1. 색상 + 모양 조합 우선 규칙
        if color == "흰색":
            # 흰색으로 잘못 인식된 경우 양배추 우선
            predictions = ["양배추", "배추", "상추", "무", "양파"]
            print(f"🥬 흰색 감지 → 양배추 우선 예측: {predictions}")
            return predictions
        
        detailed_rules = {
            # 빨간색 계열
            ("진한빨간색", "원형"): ["토마토", "빨간파프리카"],
            ("진한빨간색", "불규칙형"): ["빨간파프리카", "토마토"],
            ("연한빨간색", "직사각형"): ["적상추", "적양배추"],
            
            # 주황색 계열
            ("진한주황색", "원형"): ["단호박", "당근"],
            ("진한주황색", "직사각형"): ["당근"],
            ("진한주황색", "타원형"): ["당근", "고구마"],
            ("연한주황색", "불규칙형"): ["호박", "당근"],
            
            # 노란색 계열
            ("진한노란색", "불규칙형"): ["노란파프리카", "옥수수"],
            ("연한노란색", "불규칙형"): ["양배추", "흰양파"],
            ("연한노란색", "원형"): ["양파", "감자"],
            
            # 초록색 계열 (가장 중요)
            ("진한초록색", "불규칙형"): ["브로콜리", "시금치", "케일"],
            ("진한초록색", "원형"): ["브로콜리", "양배추심"],
            ("중간초록색", "직사각형"): ["오이", "피망"],
            ("중간초록색", "불규칙형"): ["피망", "청경채", "상추"],
            ("연한초록색", "불규칙형"): ["양배추", "상추", "배추", "청경채"],
            ("연한초록색", "원형"): ["양배추", "상추"],
            ("황록색", "불규칙형"): ["연한양배추", "셀러리", "배추"],
            
            # 보라색 계열
            ("진한보라색", "타원형"): ["가지"],
            ("진한보라색", "원형"): ["자색양파", "가지"],
            ("연한보라색", "불규칙형"): ["보라양배추", "적양파"],
            
            # 갈색 계열
            ("진한갈색", "불규칙형"): ["감자", "생강", "더덕"],
            ("진한갈색", "원형"): ["감자", "양파"],
            ("연한갈색", "원형"): ["양파", "마늘", "감자"],
            ("베이지색", "직사각형"): ["무", "연근"],
            ("베이지색", "불규칙형"): ["무", "도라지", "더덕"],
            
            # 흰색 계열
            ("흰색", "직사각형"): ["무", "대파"],
            ("흰색", "불규칙형"): ["무", "양파", "마늘", "배추"],
            ("흰색", "원형"): ["양파", "마늘", "무"]
        }
        
        # 정확한 매칭 시도
        key = (color, shape)
        if key in detailed_rules:
            predictions.extend(detailed_rules[key])
            print(f"🎯 정확 매칭: {color} + {shape} → {detailed_rules[key]}")
            return predictions
        
        # 2. 색상만으로 예측 (모양이 불분명한 경우)
        if not predictions and shape in ["알수없음", "불규칙형"]:
            color_priority_rules = {
                # 초록색 계열 (세분화)
                "진한초록색": ["브로콜리", "시금치", "케일", "피망"],
                "중간초록색": ["오이", "피망", "상추", "청경채"],
                "연한초록색": ["양배추", "상추", "배추", "청경채"],
                "황록색": ["양배추", "셀러리", "배추", "파"],
                
                # 빨간색 계열
                "진한빨간색": ["토마토", "빨간파프리카", "고추"],
                "연한빨간색": ["적상추", "적양배추", "양파"],
                
                # 주황색 계열
                "진한주황색": ["당근", "단호박", "고구마"],
                "연한주황색": ["당근", "호박", "단호박"],
                
                # 노란색 계열
                "진한노란색": ["노란파프리카", "옥수수", "단호박"],
                "연한노란색": ["양배추", "양파", "감자"],
                
                # 보라색 계열
                "진한보라색": ["가지", "자색양파", "보라양배추"],
                "연한보라색": ["보라양배추", "적양파"],
                
                # 갈색 계열
                "진한갈색": ["감자", "생강", "우엉", "더덕"],
                "연한갈색": ["양파", "마늘", "감자", "연근"],
                "베이지색": ["무", "연근", "도라지", "죽순"],
                
                # 흰색 계열
                "흰색": ["양배추", "무", "양파", "마늘", "배추", "대파"],
                "회색": ["감자", "더덕", "우엉"]
            }
            
            if color in color_priority_rules:
                predictions.extend(color_priority_rules[color])
                print(f"🎨 색상 우선 예측: {color} → {color_priority_rules[color]}")
        
        # 3. 크기 정보 보정 (있는 경우)
        if predictions and size_info:
            predictions = self._adjust_predictions_by_size(predictions, size_info)
        
        # 4. 최종 예측이 없으면 일반적인 채소들
        if not predictions:
            predictions = ["양배추", "상추", "무", "당근", "감자"]
            print(f"❓ 기본 채소 예측: {predictions}")
        
        return predictions[:3]  # 상위 3개만 반환
    def _adjust_predictions_by_size(self, predictions, size_info):
        """크기 정보로 예측 보정"""
        try:
            if not size_info or not isinstance(size_info, dict):
                return predictions
            
            # 크기별 채소 분류
            large_vegetables = ["양배추", "배추", "무", "브로콜리", "단호박"]
            medium_vegetables = ["토마토", "가지", "피망", "파프리카", "오이"]
            small_vegetables = ["마늘", "생강", "고추", "체리토마토"]
            
            size_category = size_info.get("category", "")
            
            if size_category == "대형":
                # 큰 채소 우선
                reordered = [v for v in predictions if v in large_vegetables]
                reordered.extend([v for v in predictions if v not in large_vegetables])
                return reordered
            elif size_category == "소형":
                # 작은 채소 우선
                reordered = [v for v in predictions if v in small_vegetables]
                reordered.extend([v for v in predictions if v not in small_vegetables])
                return reordered
            
            return predictions
            
        except Exception as e:
            print(f"⚠️ 크기 보정 실패: {e}")
            return predictions    
    def _categorize_sizes(self, object_sizes):
        """크기 분포 분석"""
        categories = {"대형": 0, "중형": 0, "소형": 0}
        
        for obj in object_sizes:
            category = obj["category"]
            categories[category] += 1
        
        return categories

    def analyze_image_properties(self, image):
        """이미지의 색상, 모양, 크기 종합 분석"""
        try:
            # 색상 분석
            color_analysis = self.analyze_colors(image)
            
            # 모양 분석
            shape_analysis = self.analyze_shapes(image)
            
            # 크기 분석
            size_analysis = self.analyze_sizes(image)
            
            # 전체적인 평가 생성
            overall_assessment = self._create_overall_assessment(
                color_analysis, shape_analysis, size_analysis
            )
            
            return {
                "colors": color_analysis,
                "shapes": shape_analysis,
                "sizes": size_analysis,
                "overall_assessment": overall_assessment
            }
            
        except Exception as e:
            print(f"❌ 이미지 속성 분석 실패: {e}")
            return None

    def _create_overall_assessment(self, color_analysis, shape_analysis, size_analysis):
        """전체적인 평가 생성"""
        assessment = {
            "likely_food_type": "알수없음",
            "confidence_indicators": [],
            "analysis_summary": ""
        }
        
        try:
            # 색상 + 모양 조합으로 음식 추정
            primary_color = color_analysis.get("primary_color", "")
            primary_shape = shape_analysis.get("primary_shape", "")
            
            # 음식 추정 로직
            food_predictions = self._predict_food_by_properties(primary_color, primary_shape, size_analysis)
            
            if food_predictions:
                assessment["likely_food_type"] = food_predictions[0]
                assessment["confidence_indicators"] = [
                    f"주요 색상: {primary_color}",
                    f"주요 형태: {primary_shape}",
                    f"객체 수: {shape_analysis.get('total_objects', 0)}"
                ]
            
            # 요약 생성
            summary_parts = []
            if color_analysis.get("dominant_colors"):
                colors = [color for color, _ in color_analysis["dominant_colors"]]
                summary_parts.append(f"주요 색상: {', '.join(colors)}")
            
            if primary_shape != "알수없음":
                summary_parts.append(f"형태: {primary_shape}")
            
            assessment["analysis_summary"] = " | ".join(summary_parts)
            
        except Exception as e:
            print(f"⚠️ 전체 평가 생성 실패: {e}")
        
        return assessment
    
    def analyze_sizes(self, image):
        """크기 분석"""
        try:
            h, w = image.shape[:2]
            total_area = h * w
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 임계값 처리로 객체 분리
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            object_sizes = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # 최소 크기 필터
                    relative_size = (area / total_area) * 100
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    size_category = "소형"
                    if relative_size > 20:
                        size_category = "대형"
                    elif relative_size > 10:
                        size_category = "중형"
                    
                    object_sizes.append({
                        "absolute_area": int(area),
                        "relative_size": round(relative_size, 1),
                        "category": size_category,
                        "dimensions": [w, h]
                    })
            
            # 크기 순으로 정렬
            object_sizes.sort(key=lambda x: x["absolute_area"], reverse=True)
            
            return {
                "objects": object_sizes[:3],
                "size_distribution": self._categorize_sizes(object_sizes)
            }
            
        except Exception as e:
            print(f"❌ 크기 분석 실패: {e}")
            return {"objects": [], "size_distribution": {}}
    def enhanced_vegetable_analysis(self, image_input, confidence=0.5):
        """채소 전용 향상 분석"""
        try:
            image = self.preprocess_image(image_input)
            if image is None:
                return {"success": False, "error": "이미지 처리 실패"}
            
            print("🥗 채소 전용 분석 시작...")
            
            # 1. 기본 YOLO 탐지
            yolo_detections, _ = self.detect_objects(image, confidence)
            
            # 2. 향상된 색상 분석
            color_analysis = self.analyze_colors(image)
            
            # 3. 모양 분석
            shape_analysis = self.analyze_shapes(image)
            
            # 4. 채소 특화 예측
            primary_color = color_analysis.get("primary_color", "")
            primary_shape = shape_analysis.get("primary_shape", "")
            
            vegetable_predictions = self._predict_food_by_properties(
                primary_color, primary_shape, shape_analysis.get("sizes", {})
            )
            print(f"✅ 채소 분석 완료: {vegetable_predictions}")

            # 5. 신뢰도 계산
            confidence_score = self._create_vegetable_confidence_score(
                vegetable_predictions, color_analysis, shape_analysis
            )
            
            # 6. 결과 통합
            enhanced_detections = []
            
            for detection in yolo_detections:
                if detection.get("class") in ["item", "unknown", "object"]:
                    # 채소 예측으로 교체
                    if vegetable_predictions:
                        detection["class"] = vegetable_predictions[0]
                        detection["originalClass"] = "item"
                        detection["confidence"] = confidence_score
                        detection["source"] = "vegetable_enhanced"
                        detection["predictions"] = vegetable_predictions[:3]
                        detection["color_info"] = primary_color
                        detection["shape_info"] = primary_shape
                
                enhanced_detections.append(detection)
            
            result = {
                "success": True,
                "detections": enhanced_detections,
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
        # ===== GPT 통합 분석 기능 =====
    def ensemble_detection(self, image_path, confidence=0.5):
        """앙상블 탐지 + 색상 분석 + 일반화된 보정"""
        try:
            print(f"🔍 앙상블 탐지 시작...")
            
            all_detections = []
            
            # 1. 각 모델로 탐지
            for model_name, model in self.models.items():
                try:
                    detections, _ = detect_objects(model, image_path, confidence)
                    
                    for det in detections:
                        det['model_source'] = model_name
                        det['enhanced'] = False
                        det['correction_applied'] = False
                    
                    all_detections.extend(detections)
                    print(f"   ✅ {model_name}: {len(detections)}개 탐지")
                    
                except Exception as e:
                    print(f"   ❌ {model_name} 탐지 실패: {e}")
            
            # 2. 중복 제거
            merged_detections = merge_similar_detections(all_detections)
            
            # 3. 색상 분석
            image = cv2.imread(image_path)
            color_analysis = None
            # 25.06.08 추가 
            shape_analysis = None
            size_analysis = None
            if image is not None:
                color_analysis = self.analyze_colors(image)
                shape_analysis = self.analyze_shapes(image)
                size_analysis = self.analyze_sizes(image)
                primary_color = color_analysis["primary_color"]
                
                # 🆕 일반화된 보정 적용
                merged_detections = self.apply_general_corrections(merged_detections, color_analysis)
                
                # 낮은 신뢰도 결과를 색상 기반으로 보완
                food_predictions = self.predict_food_by_color(primary_color)
                  # 🧩 모든 탐지 결과에 분석 결과 병합
                for detection in merged_detections:
                    if detection['confidence'] < 0.6 and not detection.get('correction_applied', False):
                        if food_predictions:
                            detection["color_info"] = color_analysis.get("primary_color", "알수없음")
                            detection["shape_info"] = shape_analysis.get("primary_shape", "알수없음")
                            detection["size_info"] = size_analysis.get("objects", [])
                            # 색상 기반 예측도 보완
                            if detection['confidence'] < 0.6 and not detection.get('correction_applied', False):
                                food_predictions = self.predict_food_by_color(primary_color)
                            if food_predictions:
                                detection['enhanced_prediction'] = food_predictions[0]
                                detection['enhanced_alternatives'] = food_predictions[1:3]
                                detection['enhanced'] = True
                            print(f"   🎨 색상 기반 보완: {detection['class']} → {food_predictions[0]}")
            
            return {
                "detections": merged_detections,
                "color_analysis": color_analysis,
                "total_enhanced": sum(1 for det in merged_detections if det.get('enhanced', False)),
                "total_corrected": sum(1 for det in merged_detections if det.get('correction_applied', False))
            }
            
        except Exception as e:
            print(f"❌ 앙상블 탐지 실패: {e}")
            return {"detections": [], "color_analysis": None, "total_enhanced": 0, "total_corrected": 0}
    
    def comprehensive_analysis(self, image_path, confidence=0.5, ocr_text=None):
        """3단계 완전 통합 분석 - 기존 API 유지"""
        try:
            print(f"🔬 완전 통합 분석 시작: {image_path}")
            
            # 1단계: OCR 우선 브랜드 인식
            if ocr_text:
                print(f"📄 1단계: OCR 브랜드 인식 시도")
                ocr_result = self.analyze_ocr_first(ocr_text)
                if ocr_result and ocr_result['confidence'] >= 0.85:
                    print(f"✅ OCR 브랜드 인식 성공: {ocr_result['ingredient']}")
                    return {
                        "success": True,
                        "detections": [{
                            'id': 0,
                            'class': ocr_result['ingredient'],
                            'korean_name': ocr_result['ingredient'],
                            'confidence': ocr_result['confidence'],
                            'source': ocr_result['source'],
                            'brand': ocr_result.get('brand', 'unknown'),
                            'category': ocr_result.get('category', 'unknown'),
                            'bbox': [0, 0, 100, 100],
                            'method': 'ocr_brand_mapping'
                        }],
                        "method": "ocr_priority",
                        "analysis_stage": "1_ocr_brand_recognition",
                        "confidence": ocr_result["confidence"],
                        "brand_info": {
                            "brand": ocr_result.get('brand'),
                            "category": ocr_result.get('category')
                        }
                    }
            
            # 2단계: 앙상블 탐지 + 색상 분석 + 보정
            print(f"🎯 2단계: 앙상블 + 색상 분석 + 보정")
            ensemble_result = self.ensemble_detection(image_path, confidence)
             
            all_detections = ensemble_result["detections"]
            food_detections = filter_food_detections(all_detections)
            # 25.06.08 추가 
            image = cv2.imread(image_path)

            # 3단계: 채소 특화 분석 (보완용)
            vegetable_result = None
            if len(food_detections) == 0 and image is not None:
                print("🥦 탐지 결과 부족 → 채소 전용 분석 시도")
                vegetable_result = self.enhanced_vegetable_analysis(image)

                if vegetable_result.get("success") and vegetable_result["vegetable_analysis"]["predicted_vegetables"]:
                    predicted = vegetable_result["vegetable_analysis"]["predicted_vegetables"]
                    primary_color = vegetable_result["vegetable_analysis"]["color_analysis"]["primary_color"]
                    primary_shape = vegetable_result["vegetable_analysis"]["shape_analysis"]["primary_shape"]

                    # 기존 탐지 결과 보정 시도
                    for det in all_detections:
                        if det["class"] in ["item", "apple", "object", "unknown"]:
                            print(f"🔁 '{det['class']}' → '{predicted[0]}' 보정")
                            det["original_class"] = det["class"]
                            det["class"] = predicted[0]
                            det["confidence"] = vegetable_result["vegetable_analysis"]["confidence"]
                            det["color_info"] = primary_color
                            det["shape_info"] = primary_shape
                            det["source"] = "vegetable_inference"
                            det["method"] = "vegetable_repair"
                            det["enhanced"] = True
   
                    food_detections = filter_food_detections(all_detections)
         
            print(f"🍎 3단계: 음식 필터링")    
            # 4단계: 결과 분석
            analysis = analyze_detection_results(food_detections)
            
            # 5단계: 최종 결과 구성
            result = {
                "success": True,
                "detections": food_detections,
                "color_analysis": ensemble_result["color_analysis"],
                "statistics": analysis,
                "method": "comprehensive_enhanced",
                "analysis_stage": "2_ensemble_color_correction",
                "enhancement_info": {
                    "total_detections": len(all_detections),
                    "food_filtered": len(food_detections),
                    "enhanced_predictions": ensemble_result["total_enhanced"],
                    "corrections_applied": ensemble_result["total_corrected"],
                    "models_used": list(self.models.keys()),
                    "vegetable_inference_used": vegetable_result is not None
                }
            }
            if vegetable_result:
                result["vegetable_analysis"] = vegetable_result["vegetable_analysis"]
            
            print(f"✅ 완전 통합 분석 완료:")
            print(f"   📊 총 {len(food_detections)}개 음식 객체")
            print(f"   🎨 {ensemble_result['total_enhanced']}개 색상 보완")
            print(f"   🔧 {ensemble_result['total_corrected']}개 보정 적용")
            
            return result
            
        except Exception as e:
            print(f"❌ 완전 통합 분석 실패: {e}")
            return {"success": False, "error": str(e), "method": "error"}

# ===== 편의 함수들 (기존 API 유지) =====

def create_enhanced_detector(model_paths=None):
    """향상된 탐지기 생성 - 기존 API 유지"""
    if model_paths is None:
        model_paths = {
            'yolo11s': 'models/yolo11s.pt',
            'best': 'models/best.pt',
            'best_friged': 'models/best_friged.pt'
        }
    
    models = {}
    for name, path in model_paths.items():
        model = get_cached_model(path)
        if model:
            models[name] = model
            print(f"✅ {name} 모델 로드 완료")
        else:
            print(f"❌ {name} 모델 로드 실패")
    
    detector = EnhancedYOLODetector(models)
    print(f"🚀 Enhanced YOLO 탐지기 생성 완료:")
    print(f"   📦 모델: {len(models)}개")
    print(f"   🏷️ 브랜드 카테고리: {len(BRAND_MAPPINGS)}개")
    print(f"   🔧 보정 규칙: {len(CORRECTION_RULES)}개")
    
    return detector

def quick_food_detection(image_path, confidence=0.5, use_enhanced=True, ocr_text=None):
    """빠른 음식 탐지 (올인원 함수) - 기존 API 유지"""
    try:
        if use_enhanced:
            # 향상된 탐지기 사용
            detector = create_enhanced_detector()
            result = detector.comprehensive_analysis(image_path, confidence, ocr_text)
            return result
        else:
            # 기본 단일 모델 사용
            model = get_cached_model()
            if not model:
                return {"success": False, "error": "모델 로드 실패"}
            
            detections, _ = detect_objects(model, image_path, confidence)
            food_detections = filter_food_detections(detections)
            analysis = analyze_detection_results(food_detections)
            
            return {
                "success": True,
                "detections": food_detections,
                "statistics": analysis,
                "method": "basic_yolo"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===== 테스트 및 유틸리티 (기존 유지) =====

def test_enhanced_detector(test_image_path=None, test_ocr_text=None):
    """Enhanced YOLO 탐지기 테스트"""
    print("🧪 Enhanced YOLO 탐지기 종합 테스트")
    print("=" * 60)
    
    # Enhanced 탐지기 생성
    detector = create_enhanced_detector()
    
    if not detector.models:
        print("❌ 모델 로드 실패 - 테스트 중단")
        return None
    
    # 브랜드 인식 테스트
    print("\n📋 1. 브랜드 인식 테스트")
    test_brands = [
        "메가커피 아메리카노",
        "스타벅스 카페라떼", 
        "롯데 초코파이",
        "매일유업 우유"
    ]
    
    for brand_text in test_brands:
        result = detector.analyze_ocr_first(brand_text)
        if result:
            print(f"   ✅ '{brand_text}' → {result['ingredient']} ({result['confidence']:.2f})")
        else:
            print(f"   ❌ '{brand_text}' → 인식 실패")
    
    # 이미지 분석 테스트
    if test_image_path and os.path.exists(test_image_path):
        print(f"\n🖼️ 2. 이미지 분석 테스트: {test_image_path}")
        
        # 기본 탐지
        basic_result = quick_food_detection(test_image_path, use_enhanced=False)
        print(f"📊 기본 탐지: {basic_result.get('statistics', {}).get('total_objects', 0)}개")
        
        # Enhanced 탐지 (OCR 없이)
        enhanced_result = quick_food_detection(test_image_path, use_enhanced=True)
        print(f"🚀 Enhanced 탐지: {enhanced_result.get('statistics', {}).get('total_objects', 0)}개")
        
        # Enhanced 탐지 (OCR 포함)
        if test_ocr_text:
            enhanced_ocr_result = quick_food_detection(test_image_path, use_enhanced=True, ocr_text=test_ocr_text)
            print(f"📄 Enhanced + OCR: {enhanced_ocr_result.get('method', 'unknown')}")
        
        return {
            "basic": basic_result,
            "enhanced": enhanced_result,
            "enhanced_ocr": enhanced_ocr_result if test_ocr_text else None
        }
    else:
        print("\n⚠️ 테스트 이미지가 없어 이미지 분석 테스트 건너뜀")
        return {"brand_test": "completed"}

def print_enhanced_summary(result):
    """Enhanced 탐지 결과 상세 요약 - 기존 유지"""
    if not result.get("success"):
        print(f"❌ 탐지 실패: {result.get('error', '알수없는 오류')}")
        return
    
    detections = result.get("detections", [])
    stats = result.get("statistics", {})
    enhancement_info = result.get("enhancement_info", {})
    method = result.get("method", "unknown")
    
    print("=" * 60)
    print("📋 Enhanced YOLO 탐지 결과 상세 요약")
    print("=" * 60)
    print(f"🔬 분석 방법: {method}")
    print(f"📊 탐지 단계: {result.get('analysis_stage', 'unknown')}")
    print(f"🔍 총 탐지 객체: {stats.get('total_objects', 0)}개")
    print(f"🍎 고유 음식 종류: {stats.get('unique_classes', 0)}개")
    
    if enhancement_info:
        print(f"\n🚀 Enhancement 통계:")
        print(f"   🎨 색상 기반 보완: {enhancement_info.get('enhanced_predictions', 0)}개")
        print(f"   🔧 보정 규칙 적용: {enhancement_info.get('corrections_applied', 0)}개")
        print(f"   📦 사용된 모델: {', '.join(enhancement_info.get('models_used', []))}")
    
    # 브랜드 정보
    brand_info = result.get('brand_info')
    if brand_info:
        print(f"\n🏷️ 브랜드 정보:")
        print(f"   브랜드: {brand_info.get('brand', 'unknown')}")
        print(f"   카테고리: {brand_info.get('category', 'unknown')}")
    
    # 클래스별 개수
    class_counts = stats.get('class_counts', {})
    if class_counts:
        print("\n📊 탐지된 음식별 개수:")
        for food, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {food}: {count}개")
    
    # 보정 적용된 항목들
    corrected_items = [d for d in detections if d.get('correction_applied')]
    if corrected_items:
        print(f"\n🔧 보정 적용 항목:")
        for item in corrected_items:
            original = item.get('original_class', 'unknown')
            corrected = item.get('class', 'unknown')
            reason = item.get('correction_reason', 'unknown')
            print(f"   {original} → {corrected} ({reason})")
    
    # 신뢰도 통계
    conf_stats = stats.get('confidence_stats', {})
    if conf_stats:
        print(f"\n📈 신뢰도 통계:")
        print(f"   평균: {conf_stats.get('average', 0):.3f}")
        print(f"   최고: {conf_stats.get('max', 0):.3f}")
        print(f"   최저: {conf_stats.get('min', 0):.3f}")
    
    print("=" * 60)

def get_supported_features():
    """지원 기능 목록 반환 - 기존 유지"""
    return {
        "detection_features": [
            "3-Model Ensemble Detection",
            "Smart Color Analysis", 
            "Generalized Correction Rules",  # 🆕 일반화된 보정
            "Food-Only Filtering",
            "IoU-based Deduplication"
        ],
        "brand_recognition": {
            "categories": list(BRAND_MAPPINGS.keys()),
            "total_brands": sum(len(data["brands"]) for data in BRAND_MAPPINGS.values()),
            "ocr_priority": True
        },
        "correction_rules": {  # 🆕 보정 규칙 정보
            "total_rules": len(CORRECTION_RULES),
            "rule_names": [rule.get("name", "unnamed") for rule in CORRECTION_RULES]
        },
        "analysis_stages": [
            "1. OCR Brand Recognition (Priority)",
            "2. Ensemble Detection + Color Analysis", 
            "3. Generalized Corrections",  # 🆕 일반화된 보정
            "4. Food Filtering",
            "5. Statistical Analysis"
        ],
        "supported_models": ["yolo11s.pt", "best.pt", "best_friged.pt"],
        "color_ranges": len(COLOR_RANGES),
        "korean_mappings": len(KOREAN_CLASS_MAPPING)
    }

if __name__ == "__main__":
    print("🚀 Enhanced YOLO Detector - 개선된 버전 테스트")
    print("=" * 60)
    
    # 기능 정보 출력
    features = get_supported_features()
    print("📋 지원 기능:")
    for feature in features["detection_features"]:
        print(f"   ✅ {feature}")
    
    print(f"\n🏷️ 브랜드 인식: {features['brand_recognition']['total_brands']}개 브랜드")
    print(f"🔧 보정 규칙: {features['correction_rules']['total_rules']}개")
    print(f"🎨 색상 범위: {features['color_ranges']}개")
    print(f"🇰🇷 한국어 매핑: {features['korean_mappings']}개")
    
    # 테스트 실행
    test_results = test_enhanced_detector(
        test_image_path="orange.jpeg", 
        test_ocr_text="스타벅스 아메리카노"
    )
    
    if test_results and "enhanced" in test_results:
        print("\n🚀 Enhanced 탐지 결과:")
        print_enhanced_summary(test_results["enhanced"])
    
    print("\n✅ Enhanced YOLO Detector 테스트 완료")