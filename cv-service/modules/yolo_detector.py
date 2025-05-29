# 📁 cv-service/modules/yolo_detector.py
import os
import torch
from ultralytics import YOLO
import cv2
import numpy as np

class YOLODetector:
    def __init__(self):
        self.yolo11s_model = None
        self.custom_model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"YOLO 디바이스: {self.device}")
        
    def load_models(self):
        """두 개의 모델을 순서대로 로드 (싱글톤 패턴)"""
        # YOLO11s 모델 로드
        if self.yolo11s_model is None:
            try:
                print("YOLO11s 모델 로드 중...")
                self.yolo11s_model = YOLO('yolo11s.pt')  # 자동으로 다운로드됨
                self.yolo11s_model.to(self.device)
                
                # 모델 워밍업
                dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
                self.yolo11s_model(dummy_img, verbose=False)
                print("YOLO11s 모델 로드 완료")
            except Exception as e:
                print(f"YOLO11s 모델 로드 실패: {e}")
                return False
        
        # 커스텀 모델 로드
        if self.custom_model is None:
            model_path = os.path.join(os.path.dirname(__file__), "../models/best_v.pt")
            if not os.path.exists(model_path):
                print(f"커스텀 모델 파일 없음: {model_path}")
                return False
                
            try:
                print("커스텀 모델(best_v.pt) 로드 중...")
                self.custom_model = YOLO(model_path)
                self.custom_model.to(self.device)
                
                # 모델 워밍업
                dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
                self.custom_model(dummy_img, verbose=False)
                print(f"커스텀 모델 로드 완료: {model_path}")
            except Exception as e:
                print(f"커스텀 모델 로드 실패: {e}")
                return False
                
        return True

    def preprocess_image(self, image_path, max_size=640):
        """이미지 전처리 및 크기 최적화"""
        image = cv2.imread(image_path)
        if image is None:
            return None
            
        # 이미지 크기 최적화 (큰 이미지는 리사이징)
        h, w = image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
        return image

    def run_detection_with_model(self, model, model_name, image, confidence=0.5):
        """단일 모델로 객체 탐지 실행"""
        try:
            print(f"{model_name} 탐지 실행 중...")
            results = model(
                image,
                conf=confidence,
                iou=0.45,  # NMS threshold
                max_det=100,  # 최대 탐지 수 제한
                verbose=False,  # 로그 출력 비활성화
                device=self.device
            )
            
            detections = []
            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = model.names[cls_id]
                        conf = box.conf[0].item()
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        detections.append({
                            'class': cls_name,
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2],
                            'model': model_name  # 어떤 모델에서 탐지했는지 표시
                        })
            
            print(f"{model_name} 탐지 완료: {len(detections)}개 객체 발견")
            return detections
            
        except Exception as e:
            print(f"{model_name} 탐지 오류: {e}")
            return []

    def detect_objects(self, image_path, confidence=0.5):
        """두 모델을 순서대로 실행하여 객체 탐지"""
        if not self.load_models():
            return [], None
            
        # 이미지 전처리
        image = self.preprocess_image(image_path)
        if image is None:
            return [], None
        
        all_detections = []
        
        # 1단계: YOLO11s 모델로 탐지
        print("=" * 50)
        print("1단계: YOLO11s 모델 실행")
        yolo11s_detections = self.run_detection_with_model(
            self.yolo11s_model, "YOLO11s", image, confidence
        )
        all_detections.extend(yolo11s_detections)
        
        # 2단계: 커스텀 모델로 탐지
        print("=" * 50)
        print("2단계: 커스텀 모델(best_v.pt) 실행")
        custom_detections = self.run_detection_with_model(
            self.custom_model, "Custom(best_v.pt)", image, confidence
        )
        all_detections.extend(custom_detections)
        
        print("=" * 50)
        print(f"전체 탐지 완료: {len(all_detections)}개 객체")
        print(f"  - YOLO11s: {len(yolo11s_detections)}개")
        print(f"  - Custom: {len(custom_detections)}개")
        
        return all_detections, image

    def detect_objects_separate(self, image_path, confidence=0.5):
        """두 모델의 결과를 분리해서 반환하는 메서드"""
        if not self.load_models():
            return {}, None
            
        # 이미지 전처리
        image = self.preprocess_image(image_path)
        if image is None:
            return {}, None
        
        results = {}
        
        # YOLO11s 결과
        yolo11s_detections = self.run_detection_with_model(
            self.yolo11s_model, "YOLO11s", image, confidence
        )
        results['yolo11s'] = yolo11s_detections
        
        # 커스텀 모델 결과
        custom_detections = self.run_detection_with_model(
            self.custom_model, "Custom", image, confidence
        )
        results['custom'] = custom_detections
        
        return results, image

# 전역 인스턴스 (싱글톤)
detector_instance = YOLODetector()

def load_yolo_model():
    """호환성을 위한 래퍼 함수"""
    return detector_instance if detector_instance.load_models() else None

def detect_objects(model, image_path, confidence=0.5):
    """호환성을 위한 래퍼 함수 - 두 모델을 순서대로 실행"""
    return detector_instance.detect_objects(image_path, confidence)

def detect_objects_separate(model, image_path, confidence=0.5):
    """두 모델의 결과를 분리해서 반환하는 래퍼 함수"""
    return detector_instance.detect_objects_separate(image_path, confidence)