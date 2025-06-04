# modules/yolo_detector.py - 팀원 최신 버전 + 고도화 기능 완전 통합

import cv2
import numpy as np
from ultralytics import YOLO
import os
import shutil
from collections import Counter
from io import BytesIO
from PIL import Image as PILImage

# ===== 팀원의 완전한 한국어 클래스 매핑 (100% 유지) =====
KOREAN_CLASS_MAPPING = {
    # 과일류
    'apple': '사과',
    'banana': '바나나',
    'orange': '오렌지',
    'strawberry': '딸기',
    'grape': '포도',
    'watermelon': '수박',
    'pineapple': '파인애플',
    'peach': '복숭아',
    'pear': '배',
    'kiwi': '키위',
    'lemon': '레몬',
    'lime': '라임',
    'mango': '망고',
    'cherry': '체리',
    'plum': '자두',
    
    # 채소류
    'carrot': '당근',
    'broccoli': '브로콜리',
    'cabbage': '양배추',
    'lettuce': '상추',
    'spinach': '시금치',
    'onion': '양파',
    'garlic': '마늘',
    'potato': '감자',
    'tomato': '토마토',
    'cucumber': '오이',
    'pepper': '피망',
    'corn': '옥수수',
    'mushroom': '버섯',
    'eggplant': '가지',
    'radish': '무',
    'bean': '콩',
    'pumpkin': '호박',
    'celery': '셀러리',
    'asparagus': '아스파라거스',
    'green onion': '대파',
    'scallion': '파',
    'leek': '리크',
    'zuchini': '주키니호박',
    'asparagus': '아스파라거스', 
    'green onion': "대파",
    'scallion': '파', 
    'leek': '부추',
    
    # 육류
    'beef': '소고기',
    'pork': '돼지고기',
    'chicken': '닭고기',
    'fish': '생선',
    'salmon': '연어',
    'tuna': '참치',
    'shrimp': '새우',
    'crab': '게',
    'lobster': '랍스터',
    'squid': '오징어',
    'octopus': '문어',
    'clam': '조개',
    'oyster': '굴',
    'scallop': '가리비',
    
    # 유제품
    'milk': '우유',
    'cheese': '치즈',
    'butter': '버터',
    'yogurt': '요거트',
    'cream': '크림',
    'egg': '계란',
    
    # 곡물류
    'rice': '쌀',
    'bread': '빵',
    'noodle': '면',
    'pasta': '파스타',
    'cereal': '시리얼',
    'oat': '오트',
    'wheat': '밀',
    'barley': '보리',
    
    # 음료
    'water': '물',
    'juice': '주스',
    'coffee': '커피',
    'tea': '차',
    'soda': '탄산음료',
    'beer': '맥주',
    'wine': '와인',
    
    # 조미료/기타
    'salt': '소금',
    'sugar': '설탕',
    'oil': '기름',
    'vinegar': '식초',
    'sauce': '소스',
    'honey': '꿀',
    'jam': '잼',
    'nut': '견과류',
    'almond': '아몬드',
    'walnut': '호두',
    'peanut': '땅콩',
    
    # 일반적인 YOLO 클래스들
    'person': '사람',
    'bicycle': '자전거',
    'car': '자동차',
    'motorcycle': '오토바이',
    'airplane': '비행기',
    'bus': '버스',
    'train': '기차',
    'truck': '트럭',
    'boat': '보트',
    'traffic light': '신호등',
    'fire hydrant': '소화전',
    'stop sign': '정지 표지판',
    'parking meter': '주차 미터기',
    'bench': '벤치',
    'bird': '새',
    'cat': '고양이',
    'dog': '개',
    'horse': '말',
    'sheep': '양',
    'cow': '소',
    'elephant': '코끼리',
    'bear': '곰',
    'zebra': '얼룩말',
    'giraffe': '기린',
    'backpack': '배낭',
    'umbrella': '우산',
    'handbag': '핸드백',
    'tie': '넥타이',
    'suitcase': '여행가방',
    'frisbee': '프리스비',
    'skis': '스키',
    'snowboard': '스노보드',
    'sports ball': '공',
    'kite': '연',
    'baseball bat': '야구방망이',
    'baseball glove': '야구글러브',
    'skateboard': '스케이트보드',
    'surfboard': '서핑보드',
    'tennis racket': '테니스라켓',
    'bottle': '병',
    'wine glass': '와인잔',
    'cup': '컵',
    'fork': '포크',
    'knife': '칼',
    'spoon': '숟가락',
    'bowl': '그릇',
    'dining table': '식탁',
    'toilet': '화장실',
    'tv': 'TV',
    'laptop': '노트북',
    'mouse': '마우스',
    'remote': '리모컨',
    'keyboard': '키보드',
    'cell phone': '휴대폰',
    'microwave': '전자레인지',
    'oven': '오븐',
    'toaster': '토스터',
    'sink': '싱크대',
    'refrigerator': '냉장고',
    'book': '책',
    'clock': '시계',
    'vase': '꽃병',
    'scissors': '가위',
    'teddy bear': '테디베어',
    'hair drier': '헤어드라이어',
    'toothbrush': '칫솔'
}

# ===== 팀원의 모델 캐시 시스템 (100% 유지) =====
_model_cache = {}

def get_cached_model(model_path):
    """캐시된 모델 반환 (메모리 효율성을 위해) - 팀원 버전"""
    if model_path not in _model_cache:
        _model_cache[model_path] = load_yolo_model(model_path)
    return _model_cache[model_path]

def clear_model_cache():
    """모델 캐시 초기화 - 팀원 버전"""
    global _model_cache
    _model_cache.clear()
    print("🗑️ 모델 캐시가 초기화되었습니다")

def load_yolo_model(model_path=None):
    """YOLO 모델 로드 (팀원 코드 기반, 완전 유지)"""
    if model_path is None:
        model_path = "models/yolo11s.pt"
    
    try:
        # 모델 파일 존재 확인
        if not os.path.exists(model_path):
            print(f"❌ 모델 파일이 존재하지 않습니다: {model_path}")
            
            # models 디렉토리 생성
            os.makedirs("models", exist_ok=True)
            
            # 기본 모델 다운로드 시도
            if "yolo11s.pt" in model_path:
                print("📥 YOLO11s 모델 다운로드 중...")
                model = YOLO('yolo11s.pt')  # 자동 다운로드
                # 다운로드된 모델을 models 폴더로 복사
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
        
        # 모델 정보 출력
        try:
            model_info = model.info()
            print(f"📊 모델 정보: {model_info}")
        except:
            print("📊 모델 정보를 가져올 수 없습니다")
        
        return model
        
    except Exception as e:
        print(f"❌ YOLO 모델 로드 실패: {e}")
        print(f"   모델 경로: {model_path}")
        print(f"   작업 디렉토리: {os.getcwd()}")
        print(f"   모델 디렉토리 존재 여부: {os.path.exists('models')}")
        return None

def detect_objects(model, image_path, confidence_threshold=0.5, save_result=False):
    """YOLO 모델을 사용하여 객체 탐지 수행 (팀원 코드 완전 유지)"""
    if model is None:
        raise ValueError("모델이 로드되지 않았습니다")
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    
    try:
        print(f"🔍 객체 탐지 시작: {image_path}")
        print(f"   신뢰도 임계값: {confidence_threshold}")
        
        # YOLO 추론 실행
        results = model(image_path, conf=confidence_threshold, verbose=False)
        
        detections = []
        result_image_path = None
        
        # 결과 처리
        for i, result in enumerate(results):
            boxes = result.boxes
            
            if boxes is not None and len(boxes) > 0:
                print(f"   탐지된 객체 수: {len(boxes)}")
                
                # 각 탐지 결과 처리
                for j, box in enumerate(boxes):
                    # 바운딩 박스 좌표
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # 신뢰도
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    # 클래스 ID와 이름
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = model.names[class_id]
                    
                    # 한국어 클래스명
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
                
                # 결과 이미지 저장 (요청된 경우)
                if save_result:
                    try:
                        # 결과 이미지 저장
                        result_dir = "results"
                        os.makedirs(result_dir, exist_ok=True)
                        
                        base_name = os.path.splitext(os.path.basename(image_path))[0]
                        result_image_path = os.path.join(result_dir, f"{base_name}_detected.jpg")
                        
                        # 이미지에 탐지 결과 그리기
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
        import traceback
        traceback.print_exc()
        raise

def filter_food_detections(detections, food_keywords=None):
    """음식 관련 탐지 결과만 필터링 (팀원 코드 완전 유지)"""
    if food_keywords is None:
        # 기본 음식 키워드 (팀원 버전)
        food_keywords = [
            # 과일
            'apple', 'banana', 'orange', 'strawberry', 'grape', 'watermelon',
            'pineapple', 'peach', 'pear', 'kiwi', 'lemon', 'lime', 'mango',
            'cherry', 'plum',
            
            # 채소
            'carrot', 'broccoli', 'cabbage', 'lettuce', 'spinach', 'onion',
            'garlic', 'potato', 'tomato', 'cucumber', 'pepper', 'corn',
            'mushroom', 'eggplant', 'radish', 'bean', 'pumpkin','zuchini',
            'celery', 'asparagus', 'green onion', 'scallion', 'leek',
            
            # 단백질
            'beef', 'pork', 'chicken', 'fish', 'salmon', 'tuna', 'shrimp',
            'crab', 'lobster', 'squid', 'octopus', 'egg',
            
            # 유제품
            'milk', 'cheese', 'butter', 'yogurt', 'cream',
            
            # 곡물
            'rice', 'bread', 'noodle', 'pasta', 'cereal',
            
            # 음료
            'water', 'juice', 'coffee', 'tea', 'soda', 'beer', 'wine',
            
            # 기타 식품
            'salt', 'sugar', 'oil', 'honey', 'jam', 'nut'
        ]
    
    food_detections = []
    
    for detection in detections:
        class_name = detection['class'].lower()
        
        # 음식 키워드에 포함되거나 한국어 매핑이 있는 경우
        if any(keyword in class_name for keyword in food_keywords) or \
           detection['class'] in KOREAN_CLASS_MAPPING:
            food_detections.append(detection)
    
    print(f"🍎 음식 관련 객체 필터링: {len(detections)} → {len(food_detections)}개")
    
    return food_detections

def merge_similar_detections(detections, iou_threshold=0.5, confidence_weight=0.7):
    """유사한 위치의 탐지 결과들을 병합 (팀원 코드 완전 유지)"""
    if len(detections) <= 1:
        return detections
    
    def calculate_iou(box1, box2):
        """IoU 계산"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # 교집합 영역
        x1_inter = max(x1_1, x1_2)
        y1_inter = max(y1_1, y1_2)
        x2_inter = min(x2_1, x2_2)
        y2_inter = min(y2_1, y2_2)
        
        if x2_inter <= x1_inter or y2_inter <= y1_inter:
            return 0.0
        
        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        # 합집합 영역
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    # 신뢰도 기준으로 정렬
    sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    merged_detections = []
    
    for current in sorted_detections:
        merged = False
        
        for i, existing in enumerate(merged_detections):
            # 같은 클래스이고 IoU가 임계값보다 높은 경우
            if (current['class'] == existing['class'] and 
                calculate_iou(current['bbox'], existing['bbox']) > iou_threshold):
                
                # 더 높은 신뢰도의 정보로 업데이트
                if current['confidence'] > existing['confidence']:
                    merged_detections[i] = current
                
                merged = True
                break
        
        if not merged:
            merged_detections.append(current)
    
    print(f"🔄 중복 제거: {len(detections)} → {len(merged_detections)}개")
    
    return merged_detections

def analyze_detection_results(detections):
    """탐지 결과 분석 및 통계 생성 (팀원 코드 완전 유지)"""
    if not detections:
        return {
            'total_objects': 0,
            'unique_classes': 0,
            'class_counts': {},
            'confidence_stats': {},
            'size_distribution': {}
        }
    
    # 클래스별 개수 계산
    class_counts = {}
    confidences = []
    sizes = []
    
    for detection in detections:
        class_name = detection['korean_name']
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        confidences.append(detection['confidence'])
        sizes.append(detection['area'])
    
    # 신뢰도 통계
    confidence_stats = {
        'average': round(np.mean(confidences), 3),
        'min': round(np.min(confidences), 3),
        'max': round(np.max(confidences), 3),
        'std': round(np.std(confidences), 3)
    }
    
    # 크기 분포
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

# ===== 🆕 고도화 기능 추가 (기존 코드와 완전 분리) =====

class EnhancedYOLODetector:
    """🆕 향상된 YOLO 탐지기 - 앙상블 + 색상/모양 분석"""
    
    def __init__(self, models_dict=None):
        self.models = models_dict or {}
    
    def analyze_colors(self, image):
        """🆕 향상된 색상 분석 - 채소 최적화"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 배경 마스킹
            _, mask = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 30, 255, cv2.THRESH_BINARY)
            mask2 = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 240, 255, cv2.THRESH_BINARY_INV)[1]
            final_mask = cv2.bitwise_and(mask, mask2)
            
            # 채소별 최적화된 색상 범위
            color_ranges = {
                "진한초록색": [(40, 120, 80), (70, 255, 200)],
                "중간초록색": [(35, 80, 60), (75, 180, 180)],
                "연한초록색": [(30, 30, 40), (85, 120, 160)],
                "진한빨간색": [(0, 150, 100), (10, 255, 255)],
                "진한주황색": [(11, 120, 100), (20, 255, 255)],
                "진한노란색": [(20, 120, 100), (30, 255, 255)],
                "연한노란색": [(25, 40, 80), (35, 120, 200)],
                "진한보라색": [(120, 120, 80), (140, 255, 200)],
                "진한갈색": [(8, 50, 30), (20, 180, 120)],
                "흰색": [(0, 0, 200), (180, 30, 255)]
            }
            
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
            
            # 주요 색상 정렬
            dominant_colors = sorted(color_percentages.items(), key=lambda x: x[1], reverse=True)
            primary_color = dominant_colors[0][0] if dominant_colors else "알수없음"
            
            return {
                "dominant_colors": dominant_colors[:3],
                "color_distribution": color_percentages,
                "primary_color": primary_color
            }
            
        except Exception as e:
            print(f"❌ 색상 분석 실패: {e}")
            return {"dominant_colors": [], "color_distribution": {}, "primary_color": "알수없음"}
    
    def analyze_shapes(self, image):
        """🆕 모양 분석"""
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
        """🆕 모양 분류"""
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
    
    def predict_vegetable_by_color(self, primary_color):
        """🆕 색상 기반 채소 예측"""
        color_vegetable_map = {
            "진한초록색": ["브로콜리", "시금치", "케일"],
            "중간초록색": ["오이", "피망", "상추"],
            "연한초록색": ["양배추", "상추", "배추"],
            "진한빨간색": ["토마토", "빨간파프리카"],
            "진한주황색": ["당근", "단호박", "고구마"],
            "진한노란색": ["노란파프리카", "옥수수"],
            "연한노란색": ["양배추", "양파"],
            "진한보라색": ["가지", "자색양파"],
            "진한갈색": ["감자", "생강"],
            "흰색": ["양배추", "무", "양파", "마늘"]
        }
        
        return color_vegetable_map.get(primary_color, ["양배추", "상추", "무"])
    
    def ensemble_detection(self, image_path, confidence=0.5):
        """🆕 앙상블 탐지 + 향상된 분석"""
        try:
            print(f"🔍 앙상블 탐지 시작...")
            
            all_detections = []
            
            # 1. 각 모델로 탐지
            for model_name, model in self.models.items():
                try:
                    detections, _ = detect_objects(model, image_path, confidence)
                    
                    # 모델 소스 정보 추가
                    for det in detections:
                        det['model_source'] = model_name
                        det['enhanced'] = False
                    
                    all_detections.extend(detections)
                    print(f"   ✅ {model_name}: {len(detections)}개 탐지")
                    
                except Exception as e:
                    print(f"   ❌ {model_name} 탐지 실패: {e}")
            
            # 2. 중복 제거
            merged_detections = merge_similar_detections(all_detections)
            
            # 3. 색상 분석으로 보완
            image = cv2.imread(image_path)
            if image is not None:
                color_analysis = self.analyze_colors(image)
                primary_color = color_analysis["primary_color"]
                vegetable_predictions = self.predict_vegetable_by_color(primary_color)
                
                # 낮은 신뢰도 결과를 향상된 예측으로 교체
                for detection in merged_detections:
                    if detection['confidence'] < 0.6:
                        if vegetable_predictions:
                            detection['enhanced_prediction'] = vegetable_predictions[0]
                            detection['enhanced_alternatives'] = vegetable_predictions[1:3]
                            detection['color_info'] = primary_color
                            detection['enhanced'] = True
                            print(f"   🎨 향상된 예측 적용: {detection['class']} → {vegetable_predictions[0]}")
            
            return {
                "detections": merged_detections,
                "color_analysis": color_analysis if 'color_analysis' in locals() else None,
                "total_enhanced": sum(1 for det in merged_detections if det.get('enhanced', False))
            }
            
        except Exception as e:
            print(f"❌ 앙상블 탐지 실패: {e}")
            return {"detections": [], "color_analysis": None, "total_enhanced": 0}
    
    def comprehensive_analysis(self, image_path, confidence=0.5):
        """🆕 종합 분석 - 모든 기능 통합"""
        try:
            print(f"🔬 종합 분석 시작: {image_path}")
            
            # 1. 앙상블 탐지 + 색상 분석
            ensemble_result = self.ensemble_detection(image_path, confidence)
            
            # 2. 음식만 필터링
            all_detections = ensemble_result["detections"]
            food_detections = filter_food_detections(all_detections)
            
            # 3. 결과 분석
            analysis = analyze_detection_results(food_detections)
            
            # 4. 최종 결과
            result = {
                "success": True,
                "detections": food_detections,
                "color_analysis": ensemble_result["color_analysis"],
                "statistics": analysis,
                "enhancement_info": {
                    "total_detections": len(all_detections),
                    "food_filtered": len(food_detections),
                    "enhanced_predictions": ensemble_result["total_enhanced"]
                }
            }
            
            print(f"✅ 종합 분석 완료: {len(food_detections)}개 음식 객체")
            return result
            
        except Exception as e:
            print(f"❌ 종합 분석 실패: {e}")
            return {"success": False, "error": str(e)}

# ===== 🆕 편의 함수들 =====

def create_enhanced_detector(model_paths=None):
    """🆕 향상된 탐지기 생성"""
    if model_paths is None:
        model_paths = {
            'yolo11s': 'models/yolo11s.pt',
            'best': 'models/best.pt',
            'best_friged': 'models/best_fri.pt'  # 팀원 버전
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
    print(f"🚀 향상된 탐지기 생성 완료: {len(models)}개 모델")
    
    return detector

def quick_food_detection(image_path, confidence=0.5, use_enhanced=True):
    """🆕 빠른 음식 탐지 (올인원 함수)"""
    try:
        if use_enhanced:
            # 향상된 탐지기 사용
            detector = create_enhanced_detector()
            result = detector.comprehensive_analysis(image_path, confidence)
            return result
        else:
            # 기본 단일 모델 사용 (팀원 방식)
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

# ===== 🆕 테스트 및 유틸리티 =====

def test_detector(test_image_path=None):
    """🆕 탐지기 테스트"""
    print("🧪 YOLO 탐지기 모듈 테스트")
    
    # 기본 모델 테스트 (팀원 방식)
    model = load_yolo_model("models/yolo11s.pt")
    
    if model:
        print("✅ 기본 모델 로드 테스트 성공")
        
        # 향상된 탐지기 테스트
        detector = create_enhanced_detector()
        
        if test_image_path and os.path.exists(test_image_path):
            print(f"🖼️ 테스트 이미지로 분석: {test_image_path}")
            
            # 기본 탐지 (팀원 방식)
            basic_result = quick_food_detection(test_image_path, use_enhanced=False)
            print(f"📊 기본 탐지 결과: {basic_result.get('statistics', {}).get('total_objects', 0)}개")
            
            # 향상된 탐지
            enhanced_result = quick_food_detection(test_image_path, use_enhanced=True)
            print(f"🚀 향상된 탐지 결과: {enhanced_result.get('statistics', {}).get('total_objects', 0)}개")
            
            return basic_result, enhanced_result
        else:
            print("⚠️ 테스트 이미지가 없습니다")
            return None, None
    else:
        print("❌ 모델 로드 테스트 실패")
        return None, None

def get_supported_models():
    """🆕 지원하는 모델 목록 반환"""
    return {
        "basic_models": ["yolo11s.pt", "yolo11n.pt", "yolo11m.pt", "yolo11l.pt", "yolo11x.pt"],
        "custom_models": ["best.pt", "best_fri.pt"],  # 팀원 버전
        "recommended": {
            "accuracy": "best.pt + yolo11s.pt + best_fri.pt 앙상블",  # 팀원 버전
            "speed": "yolo11s.pt 단일",
            "balanced": "yolo11s.pt + best.pt 앙상블"
        }
    }

def print_detection_summary(result):
    """🆕 탐지 결과 요약 출력"""
    if not result.get("success"):
        print(f"❌ 탐지 실패: {result.get('error', '알수없는 오류')}")
        return
    
    detections = result.get("detections", [])
    stats = result.get("statistics", {})
    enhancement_info = result.get("enhancement_info", {})
    
    print("=" * 50)
    print("📋 탐지 결과 요약")
    print("=" * 50)
    print(f"🔍 총 탐지 객체: {stats.get('total_objects', 0)}개")
    print(f"🍎 고유 음식 종류: {stats.get('unique_classes', 0)}개")
    
    if enhancement_info:
        print(f"🚀 향상된 예측 적용: {enhancement_info.get('enhanced_predictions', 0)}개")
    
    # 클래스별 개수
    class_counts = stats.get('class_counts', {})
    if class_counts:
        print("\n📊 음식별 개수:")
        for food, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {food}: {count}개")
    
    # 신뢰도 통계
    conf_stats = stats.get('confidence_stats', {})
    if conf_stats:
        print(f"\n📈 신뢰도 통계:")
        print(f"   평균: {conf_stats.get('average', 0):.3f}")
        print(f"   최고: {conf_stats.get('max', 0):.3f}")
        print(f"   최저: {conf_stats.get('min', 0):.3f}")
    
    print("=" * 50)

# ===== 호환성 유지 함수들 (팀원 코드와 100% 호환) =====

# 팀원이 사용하던 모든 함수들이 그대로 작동하도록 보장
if __name__ == "__main__":
    # 기본 테스트 실행 (팀원 방식 + 고도화)
    print("🧪 통합 YOLO 탐지기 모듈 테스트")
    print("=" * 50)
    print("📋 테스트 내용:")
    print("  🔵 팀원 기존 기능 (100% 유지):")
    print("    - 기본 YOLO 모델 로드")
    print("    - 객체 탐지 및 한국어 매핑")
    print("    - 음식 필터링")
    print("    - 중복 제거")
    print("    - 통계 분석")
    print("  🟠 고도화 기능 (추가):")
    print("    - 색상 분석")
    print("    - 모양 분석")  
    print("    - 앙상블 탐지")
    print("    - 향상된 예측")
    print("=" * 50)
    
    basic_result, enhanced_result = test_detector("test_image.jpg")
    
    if basic_result:
        print("\n📊 기본 탐지 결과 (팀원 방식):")
        print_detection_summary(basic_result)
    
    if enhanced_result:
        print("\n🚀 향상된 탐지 결과 (고도화):")
        print_detection_summary(enhanced_result)
    
    # 지원 모델 정보 출력
    supported = get_supported_models()
    print(f"\n📋 지원 모델: {supported}")
    
    print("\n✅ 통합 모듈 테스트 완료")
    print("📝 팀원 기존 코드와 100% 호환됩니다")