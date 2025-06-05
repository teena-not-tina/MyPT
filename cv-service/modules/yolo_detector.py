import cv2
import numpy as np
from ultralytics import YOLO
import os

# 한국어 클래스 매핑 (음식 관련)
KOREAN_CLASS_MAPPING = {
    # 과일류
    'apple': '사과', 'banana': '바나나', 'orange': '오렌지', 'strawberry': '딸기',
    'grape': '포도', 'watermelon': '수박', 'pineapple': '파인애플', 'peach': '복숭아',
    'pear': '배', 'kiwi': '키위', 'lemon': '레몬', 'lime': '라임', 'mango': '망고',
    'cherry': '체리', 'plum': '자두',

    # 채소류
    'carrot': '당근', 'broccoli': '브로콜리', 'cabbage': '양배추', 'lettuce': '상추',
    'spinach': '시금치', 'onion': '양파', 'garlic': '마늘', 'potato': '감자', 'tomato': '토마토',
    'cucumber': '오이', 'pepper': '고추', 'corn': '옥수수', 'mushroom': '버섯', 'eggplant': '가지',
    'radish': '무', 'bean': '콩', 'pumpkin': '호박', 'celery': '셀러리', 'asparagus': '아스파라거스',
    'green onion': '대파', 'scallion': '파', 'leek': '리크', 'zuchini': '주키니호박',

    # 육류/어류
    'beef': '소고기', 'pork': '돼지고기', 'chicken': '닭고기', 'fish': '생선', 'salmon': '연어',
    'tuna': '참치', 'shrimp': '새우', 'crab': '게', 'lobster': '랍스터', 'squid': '오징어',
    'octopus': '문어', 'clam': '조개', 'oyster': '굴', 'scallop': '가리비',

    # 유제품
    'milk': '우유', 'cheese': '치즈', 'butter': '버터', 'yogurt': '요거트', 'cream': '크림', 'egg': '계란',

    # 곡물류
    'rice': '쌀', 'bread': '빵', 'noodle': '면', 'pasta': '파스타', 'cereal': '시리얼',
    'oat': '오트', 'wheat': '밀', 'barley': '보리',

    # 음료
    'water': '물', 'juice': '주스', 'coffee': '커피', 'tea': '차', 'soda': '탄산음료',
    'beer': '맥주', 'wine': '와인',

    # 기타
    'salt': '소금', 'sugar': '설탕', 'oil': '기름', 'vinegar': '식초', 'sauce': '소스',
    'honey': '꿀', 'jam': '잼', 'nut': '견과류', 'almond': '아몬드', 'walnut': '호두', 'peanut': '땅콩',

    # 일반 클래스
    'person': '사람', 'bottle': '병', 'wine glass': '와인잔', 'cup': '컵',
    'fork': '포크', 'knife': '칼', 'spoon': '숟가락', 'bowl': '그릇', 'dining table': '식탁',
    'refrigerator': '냉장고',
}

def load_yolo_model(model_path=None):
    if model_path is None:
        model_path = "models/yolo11s.pt"
    try:
        if not os.path.exists(model_path):
            print(f"❌ 모델 파일 없음: {model_path}")
            os.makedirs("models", exist_ok=True)
            if "yolo11s.pt" in model_path:
                print("🔄 YOLO11s 모델 다운로드 중...")
                model = YOLO('yolo11s.pt')
                import shutil
                if os.path.exists('yolo11s.pt'):
                    shutil.move('yolo11s.pt', model_path)
                return model
            else:
                return None
        print(f"🔄 YOLO 로딩: {model_path}")
        model = YOLO(model_path)
        return model
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return None

def detect_objects(model, image_path, confidence_threshold=0.5, save_result=False):
    if model is None:
        raise ValueError("모델이 로드되지 않았습니다")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일 없음: {image_path}")
    try:
        results = model(image_path, conf=confidence_threshold, verbose=False)
        detections = []
        result_image_path = None

        for i, result in enumerate(results):
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
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
            else:
                print("   탐지된 객체 없음")
        return detections, result_image_path
    except Exception as e:
        print(f"❌ 탐지 오류: {e}")
        import traceback
        traceback.print_exc()
        raise

def filter_food_detections(detections, food_keywords=None):
    if food_keywords is None:
        food_keywords = [
            'apple', 'banana', 'orange', 'strawberry', 'grape', 'watermelon',
            'pineapple', 'peach', 'pear', 'kiwi', 'lemon', 'lime', 'mango',
            'cherry', 'plum', 'carrot', 'broccoli', 'cabbage', 'lettuce', 'spinach',
            'onion', 'garlic', 'potato', 'tomato', 'cucumber', 'pepper', 'corn',
            'mushroom', 'eggplant', 'radish', 'bean', 'pumpkin','zuchini',
            'celery', 'asparagus', 'green onion', 'scallion', 'leek', 'beef',
            'pork', 'chicken', 'fish', 'salmon', 'tuna', 'shrimp', 'crab',
            'lobster', 'squid', 'octopus', 'egg', 'milk', 'cheese', 'butter',
            'yogurt', 'cream', 'rice', 'bread', 'noodle', 'pasta', 'cereal',
            'water', 'juice', 'coffee', 'tea', 'soda', 'beer', 'wine', 'salt',
            'sugar', 'oil', 'honey', 'jam', 'nut'
        ]
    return [
        d for d in detections
        if any(k in d['class'].lower() for k in food_keywords)
        or d['class'] in KOREAN_CLASS_MAPPING
    ]

def analyze_detection_results(detections):
    if not detections:
        return {
            'total_objects': 0, 'unique_classes': 0,
            'class_counts': {}, 'confidence_stats': {}, 'size_distribution': {}
        }
    class_counts = {}
    confidences, sizes = [], []
    for d in detections:
        name = d['korean_name']
        class_counts[name] = class_counts.get(name, 0) + 1
        confidences.append(d['confidence'])
        sizes.append(d['area'])
    return {
        'total_objects': len(detections),
        'unique_classes': len(class_counts),
        'class_counts': class_counts,
        'confidence_stats': {
            'average': round(np.mean(confidences), 3),
            'min': round(np.min(confidences), 3),
            'max': round(np.max(confidences), 3),
            'std': round(np.std(confidences), 3)
        },
        'size_distribution': {
            'average': round(np.mean(sizes), 2),
            'min': round(np.min(sizes), 2),
            'max': round(np.max(sizes), 2),
            'std': round(np.std(sizes), 2)
        },
        'most_common_class': max(class_counts.items(), key=lambda x: x[1]),
        'highest_confidence': max(detections, key=lambda x: x['confidence'])
    }

# 모델 캐싱
_model_cache = {}
def get_cached_model(model_path):
    if model_path not in _model_cache:
        _model_cache[model_path] = load_yolo_model(model_path)
    return _model_cache[model_path]

def clear_model_cache():
    global _model_cache
    _model_cache.clear()
    print("🗑️ 모델 캐시 초기화 완료")

if __name__ == "__main__":
    print("🧪 YOLO 탐지기 모듈 테스트")
    model = load_yolo_model("models/yolo11s.pt")
    if model:
        test_image = "test_image.jpg"
        if os.path.exists(test_image):
            det, _ = detect_objects(model, test_image)
            food_only = filter_food_detections(det)
            analysis = analyze_detection_results(food_only)
            print(analysis)
        else:
            print("❌ 테스트 이미지 없음")