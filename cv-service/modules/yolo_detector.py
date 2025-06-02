# modules/yolo_detector.py - 앙상블 지원 버전

import cv2
import numpy as np
from ultralytics import YOLO
import os

# 한국어 클래스 매핑 (음식 관련)
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

def load_yolo_model(model_path=None):
    """
    YOLO 모델 로드
    
    Args:
        model_path: 모델 파일 경로 (기본값: models/yolo11s.pt)
    
    Returns:
        YOLO 모델 객체 또는 None (실패 시)
    """
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
                import shutil
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
    """
    YOLO 모델을 사용하여 객체 탐지 수행
    
    Args:
        model: 로드된 YOLO 모델
        image_path: 분석할 이미지 경로
        confidence_threshold: 신뢰도 임계값
        save_result: 결과 이미지 저장 여부
    
    Returns:
        tuple: (detections 리스트, 결과 이미지 경로)
    """
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
    """
    음식 관련 탐지 결과만 필터링
    
    Args:
        detections: 전체 탐지 결과 리스트
        food_keywords: 음식으로 간주할 키워드 리스트
    
    Returns:
        list: 음식 관련 탐지 결과만 포함한 리스트
    """
    if food_keywords is None:
        # 기본 음식 키워드
        food_keywords = [
            # 과일
            'apple', 'banana', 'orange', 'strawberry', 'grape', 'watermelon',
            'pineapple', 'peach', 'pear', 'kiwi', 'lemon', 'lime', 'mango',
            'cherry', 'plum',
            
            # 채소
            'carrot', 'broccoli', 'cabbage', 'lettuce', 'spinach', 'onion',
            'garlic', 'potato', 'tomato', 'cucumber', 'pepper', 'corn',
            'mushroom', 'eggplant', 'radish', 'bean', 'pumpkin',
            
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
    """
    유사한 위치의 탐지 결과들을 병합
    
    Args:
        detections: 탐지 결과 리스트
        iou_threshold: IoU 임계값 (이보다 높으면 같은 객체로 간주)
        confidence_weight: 신뢰도 가중치
    
    Returns:
        list: 병합된 탐지 결과 리스트
    """
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
    """
    탐지 결과 분석 및 통계 생성
    
    Args:
        detections: 탐지 결과 리스트
    
    Returns:
        dict: 분석 결과 딕셔너리
    """
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

# 모델 캐시 (전역 변수)
_model_cache = {}

def get_cached_model(model_path):
    """
    캐시된 모델 반환 (메모리 효율성을 위해)
    
    Args:
        model_path: 모델 파일 경로
    
    Returns:
        YOLO 모델 객체
    """
    if model_path not in _model_cache:
        _model_cache[model_path] = load_yolo_model(model_path)
    
    return _model_cache[model_path]

def clear_model_cache():
    """모델 캐시 초기화"""
    global _model_cache
    _model_cache.clear()
    print("🗑️ 모델 캐시가 초기화되었습니다")

if __name__ == "__main__":
    # 테스트 코드
    print("🧪 YOLO 탐지기 모듈 테스트")
    
    # 모델 로드 테스트
    model = load_yolo_model("models/yolo11s.pt")
    
    if model:
        print("✅ 모델 로드 테스트 성공")
        
        # 테스트 이미지가 있다면 탐지 테스트
        test_image = "test_image.jpg"
        if os.path.exists(test_image):
            print(f"🖼️ 테스트 이미지로 탐지 테스트: {test_image}")
            detections, result_path = detect_objects(model, test_image, save_result=True)
            
            # 음식만 필터링
            food_detections = filter_food_detections(detections)
            
            # 분석 결과 출력
            analysis = analyze_detection_results(food_detections)
            print(f"📊 분석 결과: {analysis}")
        else:
            print("⚠️ 테스트 이미지가 없습니다")
    else:
        print("❌ 모델 로드 테스트 실패")



# # 📁 cv-service/modules/yolo_detector.py
# import os
# import torch
# from ultralytics import YOLO
# import cv2
# import numpy as np

# class YOLODetector:
#     def __init__(self):
#         self.yolo11s_model = None
#         self.custom_model = None
#         self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
#         print(f"YOLO 디바이스: {self.device}")
        
#     def load_models(self):
#         """두 개의 모델을 순서대로 로드 (싱글톤 패턴)"""
#         # YOLO11s 모델 로드
#         if self.yolo11s_model is None:
#             try:
#                 print("YOLO11s 모델 로드 중...")
#                 self.yolo11s_model = YOLO('yolo11s.pt')  # 자동으로 다운로드됨
#                 self.yolo11s_model.to(self.device)
                
#                 # 모델 워밍업
#                 dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
#                 self.yolo11s_model(dummy_img, verbose=False)
#                 print("YOLO11s 모델 로드 완료")
#             except Exception as e:
#                 print(f"YOLO11s 모델 로드 실패: {e}")
#                 return False
        
#         # 커스텀 모델 로드
#         if self.custom_model is None:
#             model_path = os.path.join(os.path.dirname(__file__), "../models/best_v.pt")
#             if not os.path.exists(model_path):
#                 print(f"커스텀 모델 파일 없음: {model_path}")
#                 return False
                
#             try:
#                 print("커스텀 모델(best_v.pt) 로드 중...")
#                 self.custom_model = YOLO(model_path)
#                 self.custom_model.to(self.device)
                
#                 # 모델 워밍업
#                 dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
#                 self.custom_model(dummy_img, verbose=False)
#                 print(f"커스텀 모델 로드 완료: {model_path}")
#             except Exception as e:
#                 print(f"커스텀 모델 로드 실패: {e}")
#                 return False
                
#         return True

#     def preprocess_image(self, image_path, max_size=640):
#         """이미지 전처리 및 크기 최적화"""
#         image = cv2.imread(image_path)
#         if image is None:
#             return None
            
#         # 이미지 크기 최적화 (큰 이미지는 리사이징)
#         h, w = image.shape[:2]
#         if max(h, w) > max_size:
#             scale = max_size / max(h, w)
#             new_w, new_h = int(w * scale), int(h * scale)
#             image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
#         return image

#     def run_detection_with_model(self, model, model_name, image, confidence=0.5):
#         """단일 모델로 객체 탐지 실행"""
#         try:
#             print(f"{model_name} 탐지 실행 중...")
#             results = model(
#                 image,
#                 conf=confidence,
#                 iou=0.45,  # NMS threshold
#                 max_det=100,  # 최대 탐지 수 제한
#                 verbose=False,  # 로그 출력 비활성화
#                 device=self.device
#             )
            
#             detections = []
#             for r in results:
#                 if r.boxes is not None:
#                     for box in r.boxes:
#                         cls_id = int(box.cls[0].item())
#                         cls_name = model.names[cls_id]
#                         conf = box.conf[0].item()
#                         x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
#                         detections.append({
#                             'class': cls_name,
#                             'confidence': conf,
#                             'bbox': [x1, y1, x2, y2],
#                             'model': model_name  # 어떤 모델에서 탐지했는지 표시
#                         })
            
#             print(f"{model_name} 탐지 완료: {len(detections)}개 객체 발견")
#             return detections
            
#         except Exception as e:
#             print(f"{model_name} 탐지 오류: {e}")
#             return []

#     def detect_objects(self, image_path, confidence=0.5):
#         """두 모델을 순서대로 실행하여 객체 탐지"""
#         if not self.load_models():
#             return [], None
            
#         # 이미지 전처리
#         image = self.preprocess_image(image_path)
#         if image is None:
#             return [], None
        
#         all_detections = []
        
#         # 1단계: YOLO11s 모델로 탐지
#         print("=" * 50)
#         print("1단계: YOLO11s 모델 실행")
#         yolo11s_detections = self.run_detection_with_model(
#             self.yolo11s_model, "YOLO11s", image, confidence
#         )
#         all_detections.extend(yolo11s_detections)
        
#         # 2단계: 커스텀 모델로 탐지
#         print("=" * 50)
#         print("2단계: 커스텀 모델(best_v.pt) 실행")
#         custom_detections = self.run_detection_with_model(
#             self.custom_model, "Custom(best_v.pt)", image, confidence
#         )
#         all_detections.extend(custom_detections)
        
#         print("=" * 50)
#         print(f"전체 탐지 완료: {len(all_detections)}개 객체")
#         print(f"  - YOLO11s: {len(yolo11s_detections)}개")
#         print(f"  - Custom: {len(custom_detections)}개")
        
#         return all_detections, image

#     def detect_objects_separate(self, image_path, confidence=0.5):
#         """두 모델의 결과를 분리해서 반환하는 메서드"""
#         if not self.load_models():
#             return {}, None
            
#         # 이미지 전처리
#         image = self.preprocess_image(image_path)
#         if image is None:
#             return {}, None
        
#         results = {}
        
#         # YOLO11s 결과
#         yolo11s_detections = self.run_detection_with_model(
#             self.yolo11s_model, "YOLO11s", image, confidence
#         )
#         results['yolo11s'] = yolo11s_detections
        
#         # 커스텀 모델 결과
#         custom_detections = self.run_detection_with_model(
#             self.custom_model, "Custom", image, confidence
#         )
#         results['custom'] = custom_detections
        
#         return results, image

# # 전역 인스턴스 (싱글톤)
# detector_instance = YOLODetector()

# def load_yolo_model():
#     """호환성을 위한 래퍼 함수"""
#     return detector_instance if detector_instance.load_models() else None

# def detect_objects(model, image_path, confidence=0.5):
#     """호환성을 위한 래퍼 함수 - 두 모델을 순서대로 실행"""
#     return detector_instance.detect_objects(image_path, confidence)

# def detect_objects_separate(model, image_path, confidence=0.5):
#     """두 모델의 결과를 분리해서 반환하는 래퍼 함수"""
#     return detector_instance.detect_objects_separate(image_path, confidence)