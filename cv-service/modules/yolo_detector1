# 📁 cv-service/modules/yolo_detector.py
import os
import torch
import cv2
import numpy as np
import tempfile
import base64
import json
# 25.06.01 추가
from io import BytesIO                    # ← 🆕 추가
from PIL import Image as PILImage   
from io import BytesIO
from PIL import Image as PILImage
from ultralytics import YOLO
from collections import Counter
from datetime import datetime
import openai
from dotenv import load_dotenv

load_dotenv()

class YOLODetector:
    """통합 YOLO 탐지기 - 객체 탐지, 색상/모양 분석, GPT 통합"""
    
    def __init__(self, openai_api_key=None):
        self.yolo11s_model = None
        self.custom_model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.openai_api_key = openai_api_key
        
        if openai_api_key:
            openai.api_key = openai_api_key
            
        print(f"YOLO 디바이스: {self.device}")
        
    def load_models(self):
        """두 개의 모델을 순서대로 로드 (싱글톤 패턴)"""
        # YOLO11s 모델 로드
        if self.yolo11s_model is None:
            try:
                print("YOLO11s 모델 로드 중...")
                self.yolo11s_model = YOLO('yolo11s.pt')
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
            if os.path.exists(model_path):
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
            else:
                print(f"커스텀 모델 파일 없음: {model_path}")
                
        return True

    def preprocess_image(self, image_input, max_size=640):
        """이미지 전처리 - 파일 경로, 바이트, numpy 배열 모두 지원"""
        try:
            # 입력 타입별 처리
            if isinstance(image_input, str):
                # 파일 경로인 경우
                image = cv2.imread(image_input)
                if image is None:
                    raise ValueError(f"이미지 파일을 읽을 수 없습니다: {image_input}")
                    
            elif isinstance(image_input, bytes):
                # 바이트 데이터인 경우
                nparr = np.frombuffer(image_input, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError("바이트 데이터에서 이미지를 디코딩할 수 없습니다")
                    
            elif isinstance(image_input, np.ndarray):
                # numpy 배열인 경우
                image = image_input.copy()
                
            else:
                raise ValueError(f"지원하지 않는 이미지 입력 타입: {type(image_input)}")
            
            # 이미지 크기 최적화
            h, w = image.shape[:2]
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                
            return image
            
        except Exception as e:
            print(f"❌ 이미지 전처리 실패: {e}")
            return None

    def run_detection_with_model(self, model, model_name, image, confidence=0.5):
        """단일 모델로 객체 탐지 실행"""
        try:
            print(f"{model_name} 탐지 실행 중...")
            results = model(
                image,
                conf=confidence,
                iou=0.45,
                max_det=100,
                verbose=False,
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
                            'model': model_name
                        })
            
            print(f"{model_name} 탐지 완료: {len(detections)}개 객체 발견")
            return detections
            
        except Exception as e:
            print(f"{model_name} 탐지 오류: {e}")
            return []

    def detect_objects(self, image_input, confidence=0.5):
        """통합 객체 탐지 - 파일/바이트/배열 모두 지원"""
        if not self.load_models():
            return [], None
            
        # 이미지 전처리
        image = self.preprocess_image(image_input)
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
        
        # 2단계: 커스텀 모델로 탐지 (모델이 있는 경우만)
        if self.custom_model is not None:
            print("=" * 50)
            print("2단계: 커스텀 모델(best_v.pt) 실행")
            custom_detections = self.run_detection_with_model(
                self.custom_model, "Custom(best_v.pt)", image, confidence
            )
            all_detections.extend(custom_detections)
        
        print("=" * 50)
        print(f"전체 탐지 완료: {len(all_detections)}개 객체")
        
        return all_detections, image

    def detect_objects_separate(self, image_input, confidence=0.5):
        """두 모델의 결과를 분리해서 반환하는 메서드"""
        if not self.load_models():
            return {}, None
            
        # 이미지 전처리
        image = self.preprocess_image(image_input)
        if image is None:
            return {}, None
        
        results = {}
        
        # YOLO11s 결과
        yolo11s_detections = self.run_detection_with_model(
            self.yolo11s_model, "YOLO11s", image, confidence
        )
        results['yolo11s'] = yolo11s_detections
        
        # 커스텀 모델 결과 (모델이 있는 경우만)
        if self.custom_model is not None:
            custom_detections = self.run_detection_with_model(
                self.custom_model, "Custom", image, confidence
            )
            results['custom'] = custom_detections
        else:
            results['custom'] = []
        
        return results, image

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
    def _create_vegetable_confidence_score(self, predictions, color_analysis, shape_analysis):
        """채소 예측 신뢰도 점수 계산"""
        try:
            base_score = 0.6
            
            # 색상 신뢰도
            primary_color = color_analysis.get("primary_color", "")
            if primary_color != "알수없음":
                base_score += 0.2
            
            # 모양 신뢰도
            primary_shape = shape_analysis.get("primary_shape", "")
            if primary_shape != "알수없음":
                base_score += 0.15
            
            # 색상 일관성
            grouped_colors = color_analysis.get("grouped_colors", {})
            if len(grouped_colors) == 1:  # 한 가지 색상 계열만 있으면 높은 신뢰도
                base_score += 0.1
            
            return min(0.95, base_score)
            
        except Exception as e:
            return 0.6

# ===== 🆕 채소 전용 특별 분석 함수 =====

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

    def encode_image_to_base64(self, image):
        """이미지를 base64로 인코딩"""
        try:
            # BGR을 RGB로 변환
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(image_rgb)
            
            buffer = BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"❌ 이미지 인코딩 실패: {e}")
            return None

    def enhanced_gpt_analysis_with_properties(self, image, properties=None):
        """속성 정보를 포함한 향상된 GPT 분석"""
        
        print(f"🔑 GPT 분석 시 API 키 확인: {bool(self.openai_api_key)}")
        if not self.openai_api_key:
            return "OpenAI API 키가 설정되지 않았습니다."
        
        try:
            import openai
            openai.api_key = self.openai_api_key  # 기존 방식
            # 또는 새로운 방식
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            image_base64 = self.encode_image_to_base64(image)
            if not image_base64:
                return "이미지 인코딩 실패"
            
            # 기본 프롬프트
            base_prompt = """
            이미지의 식재료를 정확히 식별해주세요.

            🔍 **분석 지침**:
            1. 모든 식재료를 정확히 식별하고 개수를 세어주세요
            2. 바나나는 노란색 + 타원형/길쭉한 형태
            3. 토마토는 빨간색 + 원형
            4. 키위는 갈색 껍질 + 원형 (또는 초록색 과육)
            5. 불분명한 경우 가능성이 높은 것을 언급해주세요

            JSON 형식으로 답변해주세요:
            {
                "identified_items": [
                    {
                        "name": "정확한 식재료명",
                        "count": 개수,
                        "confidence": "높음/보통/낮음",
                        "description": "간단한 설명"
                    }
                ],
                "total_items": 전체개수,
                "analysis_notes": "분석 과정에서의 특이사항"
            }
            """
            
            # 속성 정보가 있으면 추가
            if properties:
                color_info = properties.get("colors", {})
                shape_info = properties.get("shapes", {})
                
                enhanced_prompt = f"""
                {base_prompt}

                🎨 **색상 분석 결과**:
                - 주요 색상: {color_info.get('primary_color', '분석불가')}
                - 색상 분포: {color_info.get('dominant_colors', [])}

                📐 **형태 분석 결과**:
                - 주요 형태: {shape_info.get('primary_shape', '분석불가')}
                - 객체 수: {shape_info.get('total_objects', 0)}개

                위 분석 정보를 참고하여 더 정확한 식별을 해주세요.
                """
                prompt = enhanced_prompt
            else:
                prompt = base_prompt

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ GPT 분석 실패: {e}")
            return f"분석 실패: {str(e)}"

    # ===== 이미지 특성 분석 =====

    def analyze_image_characteristics(self, image):
        """이미지 특성 분석 (스마트 전략용)"""
        try:
            h, w = image.shape[:2]
            
            # 이미지 복잡도 측정 (엣지 기반)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)
            
            # 색상 다양성 측정
            unique_colors = len(np.unique(image.reshape(-1, image.shape[2]), axis=0))
            color_diversity = unique_colors / (h * w) * 100
            
            # 밝기 분산 측정
            brightness_var = np.var(gray)
            
            return {
                "is_simple_scene": edge_density < 0.1 and color_diversity < 5,
                "has_text_overlay": brightness_var > 2000,  # 높은 명암 대비
                "complexity_score": edge_density * 10 + color_diversity / 100,
                "dimensions": (w, h),
                "edge_density": edge_density,
                "color_diversity": color_diversity,
                "brightness_variance": brightness_var
            }
            
        except Exception as e:
            print(f"⚠️ 이미지 특성 분석 실패: {e}")
            return {
                "is_simple_scene": False,
                "has_text_overlay": False,
                "complexity_score": 5.0,
                "dimensions": (0, 0)
            }

    # ===== 통합 분석 기능 =====

    def comprehensive_analysis(self, image_input, use_gpt=True, confidence=0.5):
        """종합적인 식재료 분석 (YOLO + 색상/모양 + GPT)"""
        try:
            # 이미지 전처리
            image = self.preprocess_image(image_input)
            if image is None:
                return {"success": False, "error": "이미지 처리 실패"}
            
            print("🔍 종합 분석 시작...")
            
            # 1단계: YOLO 객체 탐지
            yolo_detections, _ = self.detect_objects(image, confidence)
            
            # 2단계: 색상/모양 분석
            properties = self.analyze_image_properties(image)
            
            # 3단계: GPT 분석 (옵션)
            gpt_analysis = None
            if use_gpt and self.openai_api_key:
                gpt_analysis = self.enhanced_gpt_analysis_with_properties(image, properties)
            
            # 결과 종합
            result = {
                "success": True,
                "yolo_detections": {
                    "count": len(yolo_detections),
                    "items": yolo_detections
                },
                "color_shape_analysis": properties,
                "gpt_analysis": gpt_analysis,
                "recommendation": self._generate_recommendation(yolo_detections, properties, gpt_analysis)
            }
            
            print("✅ 종합 분석 완료")
            return result
            
        except Exception as e:
            print(f"❌ 종합 분석 실패: {e}")
            return {"success": False, "error": f"분석 실패: {str(e)}"}

    def smart_detection_strategy(self, image_input, confidence=0.5):
        """스마트 탐지 전략 - 이미지 특성에 따라 최적 방법 선택"""
        try:
            # 이미지 전처리
            image = self.preprocess_image(image_input)
            if image is None:
                return {"success": False, "error": "이미지 처리 실패"}
            
            # 이미지 특성 분석
            characteristics = self.analyze_image_characteristics(image)
            
            print(f"🤖 스마트 전략 - 이미지 특성:")
            print(f"   - 단순 장면: {characteristics['is_simple_scene']}")
            print(f"   - 텍스트 오버레이: {characteristics['has_text_overlay']}")
            print(f"   - 복잡도 점수: {characteristics['complexity_score']:.2f}")
            
            # 전략 선택
            strategy_used = ""
            
            if characteristics["is_simple_scene"]:
                # 단순한 장면 → YOLO 우선 (빠른 처리)
                print("📷 단순 장면 감지 → YOLO 우선 전략")
                strategy_used = "yolo_priority"
                
                # YOLO 탐지
                yolo_detections, _ = self.detect_objects(image, confidence)
                
                # 고신뢰도 결과가 있으면 GPT 생략
                high_conf_detections = [
                    det for det in yolo_detections
                    if det.get("confidence", 0) > 0.7
                ]
                
                if high_conf_detections:
                    print(f"✅ YOLO 고신뢰도 결과 사용: {len(high_conf_detections)}개")
                    return {
                        "success": True,
                        "strategy": strategy_used,
                        "detections": high_conf_detections,
                        "characteristics": characteristics,
                        "gpt_used": False
                    }
            
            elif characteristics["has_text_overlay"]:
                # 텍스트가 많은 이미지 → GPT 우선
                print("📝 텍스트 감지 → GPT 우선 전략")
                strategy_used = "gpt_priority"
                
            else:
                # 복잡한 장면 → 병렬 처리
                print("🔍 복잡 장면 감지 → 종합 분석")
                strategy_used = "comprehensive"
            
            # 종합 분석 실행
            result = self.comprehensive_analysis(image, use_gpt=True, confidence=confidence)
            result["strategy"] = strategy_used
            result["characteristics"] = characteristics
            
            return result
            
        except Exception as e:
            print(f"❌ 스마트 전략 실패: {e}")
            return {"success": False, "error": f"스마트 전략 오류: {str(e)}"}

    def batch_detection(self, image_inputs, confidence=0.5, use_gpt=False):
        """배치 탐지 - 여러 이미지 한번에 처리"""
        results = []
        
        print(f"📦 배치 탐지 시작 - {len(image_inputs)}개 이미지")
        
        for i, image_input in enumerate(image_inputs):
            print(f"🔍 이미지 {i+1}/{len(image_inputs)} 처리 중...")
            
            try:
                if use_gpt:
                    result = self.comprehensive_analysis(image_input, use_gpt=True, confidence=confidence)
                else:
                    # YOLO만 사용하여 빠른 처리
                    detections, image = self.detect_objects(image_input, confidence)
                    result = {
                        "success": True,
                        "index": i,
                        "detections": detections,
                        "count": len(detections)
                    }
                
                result["index"] = i
                results.append(result)
                
            except Exception as e:
                print(f"❌ 이미지 {i+1} 처리 실패: {e}")
                results.append({
                    "success": False,
                    "index": i,
                    "error": str(e)
                })
        
        print(f"✅ 배치 탐지 완료")
        
        # 통계 생성
        successful = [r for r in results if r.get("success")]
        total_detections = sum(r.get("count", 0) for r in successful)
        
        return {
            "results": results,
            "summary": {
                "total_images": len(image_inputs),
                "successful": len(successful),
                "failed": len(image_inputs) - len(successful),
                "total_detections": total_detections,
                "average_detections": total_detections / len(successful) if successful else 0
            }
        }

    def _generate_recommendation(self, yolo_detections, properties, gpt_analysis):
        """분석 결과를 바탕으로 추천 생성"""
        recommendations = []
        
        # YOLO 결과 기반 추천
        if yolo_detections:
            detected_items = [det.get('class', '') for det in yolo_detections]
            recommendations.append(f"YOLO 탐지: {', '.join(detected_items)}")
        
        # 색상/모양 분석 기반 추천
        if properties and properties.get("overall_assessment"):
            likely_food = properties["overall_assessment"].get("likely_food_type", "")
            if likely_food != "알수없음":
                recommendations.append(f"색상/모양 분석: {likely_food}")
        
        # 최종 추천
        if not recommendations:
            return "식재료를 명확히 식별하지 못했습니다. 다른 각도에서 촬영해보세요."
        
        return " | ".join(recommendations)

    # ===== 품질 검증 및 통계 =====

    def validate_detection_quality(self, detections, image):
        """탐지 품질 검증"""
        try:
            if not detections:
                return {"quality_score": 0, "issues": ["탐지된 객체 없음"]}
            
            issues = []
            quality_factors = []
            
            # 신뢰도 분석
            confidences = [det.get("confidence", 0) for det in detections]
            avg_confidence = sum(confidences) / len(confidences)
            quality_factors.append(avg_confidence)
            
            if avg_confidence < 0.5:
                issues.append("평균 신뢰도 낮음")
            
            # 중복 탐지 체크
            positions = []
            for det in detections:
                bbox = det.get("bbox", [])
                if len(bbox) == 4:
                    center_x = (bbox[0] + bbox[2]) / 2
                    center_y = (bbox[1] + bbox[3]) / 2
                    positions.append((center_x, center_y))
            
            # 너무 가까운 탐지들 찾기
            duplicate_count = 0
            for i, pos1 in enumerate(positions):
                for j, pos2 in enumerate(positions[i+1:], i+1):
                    distance = ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
                    if distance < 50:  # 임계값
                        duplicate_count += 1
            
            if duplicate_count > 0:
                issues.append(f"중복 탐지 {duplicate_count}개")
                quality_factors.append(max(0, 1 - duplicate_count * 0.2))
            else:
                quality_factors.append(1.0)
            
            # 전체 품질 점수 계산
            quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0
            
            return {
                "quality_score": round(quality_score, 3),
                "average_confidence": round(avg_confidence, 3),
                "duplicate_detections": duplicate_count,
                "issues": issues if issues else ["품질 양호"]
            }
            
        except Exception as e:
            return {"quality_score": 0, "issues": [f"품질 검증 오류: {str(e)}"]}

    def get_detection_statistics(self, detections):
        """탐지 통계 생성"""
        try:
            if not detections:
                return {"total": 0, "by_class": {}, "by_model": {}, "confidence_stats": {}}
            
            # 클래스별 통계
            class_counts = Counter(det.get("class", "unknown") for det in detections)
            
            # 모델별 통계
            model_counts = Counter(det.get("model", "unknown") for det in detections)
            
            # 신뢰도 통계
            confidences = [det.get("confidence", 0) for det in detections if "confidence" in det]
            confidence_stats = {}
            
            if confidences:
                confidence_stats = {
                    "min": round(min(confidences), 3),
                    "max": round(max(confidences), 3),
                    "mean": round(sum(confidences) / len(confidences), 3),
                    "high_confidence_count": sum(1 for c in confidences if c > 0.7),
                    "medium_confidence_count": sum(1 for c in confidences if 0.3 <= c <= 0.7),
                    "low_confidence_count": sum(1 for c in confidences if c < 0.3)
                }
            
            return {
                "total": len(detections),
                "by_class": dict(class_counts),
                "by_model": dict(model_counts),
                "confidence_stats": confidence_stats,
                "unique_classes": len(class_counts),
                "models_used": len(model_counts)
            }
            
        except Exception as e:
            print(f"❌ 통계 생성 실패: {e}")
            return {"error": f"통계 생성 오류: {str(e)}"}

    def create_detection_summary(self, detections, properties=None, gpt_analysis=None):
        """탐지 결과 요약 생성"""
        try:
            summary = {
                "detection_count": len(detections),
                "detected_items": [],
                "confidence_level": "낮음",
                "analysis_methods": [],
                "recommendations": []
            }
            
            # 탐지된 아이템 정리
            if detections:
                item_counts = Counter(det.get("class", "unknown") for det in detections)
                summary["detected_items"] = [
                    {"name": item, "count": count} 
                    for item, count in item_counts.most_common()
                ]
                
                # 전체 신뢰도 계산
                confidences = [det.get("confidence", 0) for det in detections if "confidence" in det]
                if confidences:
                    avg_conf = sum(confidences) / len(confidences)
                    if avg_conf > 0.7:
                        summary["confidence_level"] = "높음"
                    elif avg_conf > 0.4:
                        summary["confidence_level"] = "보통"
                
                summary["analysis_methods"].append("YOLO 객체 탐지")
            
            # 색상/모양 분석 정보 추가
            if properties:
                summary["analysis_methods"].append("색상/모양 분석")
                
                overall = properties.get("overall_assessment", {})
                likely_food = overall.get("likely_food_type", "")
                if likely_food and likely_food != "알수없음":
                    summary["recommendations"].append(f"형태 분석 결과: {likely_food}")
            
            # GPT 분석 정보 추가
            if gpt_analysis:
                summary["analysis_methods"].append("GPT-4o Vision 분석")
                
                try:
                    # JSON 파싱 시도
                    gpt_data = json.loads(gpt_analysis)
                    if "identified_items" in gpt_data:
                        gpt_items = gpt_data["identified_items"]
                        summary["recommendations"].append(
                            f"GPT 식별: {', '.join([item.get('name', '') for item in gpt_items])}"
                        )
                except:
                    # JSON 파싱 실패시 텍스트로 처리
                    if len(gpt_analysis) > 100:
                        summary["recommendations"].append("GPT 상세 분석 완료")
                    else:
                        summary["recommendations"].append(f"GPT: {gpt_analysis[:100]}...")
            
            # 종합 추천사항
            if not summary["recommendations"]:
                summary["recommendations"].append("추가 분석이 필요합니다")
            
            return summary
            
        except Exception as e:
            print(f"❌ 요약 생성 실패: {e}")
            return {"error": f"요약 생성 오류: {str(e)}"}

    # ===== 바이트 처리 전용 메서드 =====

    def detect_from_bytes(self, image_bytes, confidence=0.5, use_gpt=True):
        """바이트 데이터에서 직접 식재료 탐지"""
        try:
            print("📱 바이트 데이터 처리 시작...")
            
            # 바이트에서 이미지 로드
            image = self.preprocess_image(image_bytes)
            if image is None:
                return {"success": False, "error": "바이트 데이터 처리 실패"}
            
            # 종합 분석 실행
            result = self.comprehensive_analysis(image, use_gpt, confidence)
            
            print("✅ 바이트 데이터 처리 완료")
            return result
            
        except Exception as e:
            print(f"❌ 바이트 처리 실패: {e}")
            return {"success": False, "error": f"바이트 처리 오류: {str(e)}"}

    def detect_from_file(self, file_path, confidence=0.5, use_gpt=True):
        """파일에서 식재료 탐지"""
        try:
            print(f"📁 파일 처리 시작: {file_path}")
            
            # 종합 분석 실행
            result = self.comprehensive_analysis(file_path, use_gpt, confidence)
            
            print("✅ 파일 처리 완료")
            return result
            
        except Exception as e:
            print(f"❌ 파일 처리 실패: {e}")
            return {"success": False, "error": f"파일 처리 오류: {str(e)}"}


# ===== 고급 분석 기능 =====

class AdvancedAnalyzer:
    """고급 분석 기능들"""
    
    def __init__(self, detector_instance):
        self.detector = detector_instance
    
    def compare_detection_methods(self, image_input, confidence=0.5):
        """여러 탐지 방법 비교 분석"""
        try:
            image = self.detector.preprocess_image(image_input)
            if image is None:
                return {"success": False, "error": "이미지 처리 실패"}
            
            print("🔬 탐지 방법 비교 분석 시작...")
            
            results = {}
            
            # 1. YOLO만 사용
            yolo_detections, _ = self.detector.detect_objects(image, confidence)
            results["yolo_only"] = {
                "detections": yolo_detections,
                "count": len(yolo_detections),
                "method": "YOLO 객체 탐지"
            }
            
            # 2. 색상/모양 분석
            properties = self.detector.analyze_image_properties(image)
            results["color_shape"] = {
                "analysis": properties,
                "prediction": properties.get("overall_assessment", {}).get("likely_food_type", "없음") if properties else "없음",
                "method": "색상/모양 분석"
            }
            
            # 3. GPT 분석 (API 키가 있는 경우)
            if self.detector.openai_api_key:
                gpt_result = self.detector.enhanced_gpt_analysis_with_properties(image, properties)
                results["gpt_vision"] = {
                    "analysis": gpt_result,
                    "method": "GPT-4o Vision"
                }
            
            # 4. 스마트 전략
            smart_result = self.detector.smart_detection_strategy(image, confidence)
            results["smart_strategy"] = {
                "result": smart_result,
                "method": "스마트 전략"
            }
            
            # 비교 분석
            comparison = self._analyze_method_differences(results)
            
            return {
                "success": True,
                "individual_results": results,
                "comparison_analysis": comparison,
                "recommendation": self._recommend_best_method(results, comparison)
            }
            
        except Exception as e:
            print(f"❌ 비교 분석 실패: {e}")
            return {"success": False, "error": f"비교 분석 오류: {str(e)}"}
    
    def _analyze_method_differences(self, results):
        """방법별 차이점 분석"""
        try:
            analysis = {
                "consistency": {},
                "coverage": {},
                "confidence": {},
                "speed_estimate": {}
            }
            
            # YOLO 결과 추출
            yolo_items = set()
            if "yolo_only" in results:
                yolo_items = set(det.get("class", "") for det in results["yolo_only"]["detections"])
            
            # 색상/모양 예측 추출
            color_shape_pred = results.get("color_shape", {}).get("prediction", "")
            
            # 일관성 분석
            analysis["consistency"]["yolo_vs_color_shape"] = color_shape_pred in yolo_items
            
            # 커버리지 분석
            analysis["coverage"] = {
                "yolo_unique_items": len(yolo_items),
                "color_shape_prediction": 1 if color_shape_pred and color_shape_pred != "없음" else 0
            }
            
            # 신뢰도 분석
            if "yolo_only" in results:
                confidences = [det.get("confidence", 0) for det in results["yolo_only"]["detections"]]
                if confidences:
                    analysis["confidence"]["yolo_avg"] = sum(confidences) / len(confidences)
                    analysis["confidence"]["yolo_high_count"] = sum(1 for c in confidences if c > 0.7)
            
            # 속도 추정 (상대적)
            analysis["speed_estimate"] = {
                "yolo_only": "빠름",
                "color_shape": "매우 빠름",
                "gpt_vision": "느림" if "gpt_vision" in results else "사용 안함",
                "smart_strategy": "보통"
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"차이점 분석 오류: {str(e)}"}
    
    def _recommend_best_method(self, results, comparison):
        """최적 방법 추천"""
        try:
            recommendations = []
            
            # YOLO 결과 기준
            yolo_count = results.get("yolo_only", {}).get("count", 0)
            
            if yolo_count > 0:
                avg_conf = comparison.get("confidence", {}).get("yolo_avg", 0)
                if avg_conf > 0.7:
                    recommendations.append("YOLO 단독 사용 권장 (높은 신뢰도)")
                elif avg_conf > 0.4:
                    recommendations.append("YOLO + 색상/모양 분석 조합 권장")
                else:
                    recommendations.append("전체 방법 조합 사용 권장 (낮은 신뢰도)")
            else:
                recommendations.append("GPT Vision 분석 권장 (YOLO 탐지 실패)")
            
            # 색상/모양 분석 기준
            color_pred = results.get("color_shape", {}).get("prediction", "")
            if color_pred and color_pred != "없음":
                recommendations.append(f"색상/모양 분석이 '{color_pred}' 예측")
            
            return {
                "primary_recommendation": recommendations[0] if recommendations else "추가 분석 필요",
                "all_recommendations": recommendations,
                "suggested_confidence_threshold": self._suggest_confidence_threshold(comparison)
            }
            
        except Exception as e:
            return {"error": f"추천 생성 오류: {str(e)}"}
    
    def _suggest_confidence_threshold(self, comparison):
        """신뢰도 임계값 제안"""
        avg_conf = comparison.get("confidence", {}).get("yolo_avg", 0.5)
        
        if avg_conf > 0.8:
            return 0.7  # 높은 품질이면 임계값 상승
        elif avg_conf > 0.6:
            return 0.5  # 보통 품질이면 기본값
        else:
            return 0.3  # 낮은 품질이면 임계값 하락


# ===== 성능 모니터링 =====

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self.detection_times = []
        self.success_count = 0
        self.failure_count = 0
        
    def record_detection(self, start_time, end_time, success=True):
        """탐지 성능 기록"""
        duration = (end_time - start_time).total_seconds()
        self.detection_times.append(duration)
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
    
    def get_performance_stats(self):
        """성능 통계 반환"""
        if not self.detection_times:
            return {"no_data": True}
        
        times = self.detection_times
        total_attempts = self.success_count + self.failure_count
        
        return {
            "total_detections": len(times),
            "success_rate": self.success_count / total_attempts if total_attempts > 0 else 0,
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "recent_average": sum(times[-10:]) / min(len(times), 10)
        }


# ===== 전역 인스턴스 및 호환성 함수들 =====

# 전역 인스턴스 (싱글톤)
detector_instance = YOLODetector()

# 전역 성능 모니터
performance_monitor = PerformanceMonitor()

def load_yolo_model():
    """호환성을 위한 래퍼 함수"""
    return detector_instance if detector_instance.load_models() else None

def detect_objects(model, image_path, confidence=0.5):
    """호환성을 위한 래퍼 함수 - 기존 API 유지"""
    return detector_instance.detect_objects(image_path, confidence)

def detect_objects_separate(model, image_path, confidence=0.5):
    """두 모델의 결과를 분리해서 반환하는 래퍼 함수"""
    return detector_instance.detect_objects_separate(image_path, confidence)

def analyze_food_with_properties(image_input, openai_api_key=None):
    """색상/모양 분석 + GPT 조합 (호환성 함수)"""
    try:
        # 기존 detector_instance 사용하되 API 키 설정
        if openai_api_key:
            detector_instance.openai_api_key = openai_api_key
            
        # 이미지 전처리
        image = detector_instance.preprocess_image(image_input)
        if image is None:
            return {"success": False, "error": "이미지 처리 실패"}
        
        # 1단계: 물리적 속성 분석
        properties = detector_instance.analyze_image_properties(image)
        
        if not properties:
            return {"success": False, "error": "속성 분석 실패"}
        
        # 2단계: GPT와 함께 정밀 분석
        gpt_analysis = detector_instance.enhanced_gpt_analysis_with_properties(image, properties)
        
        return {
            "success": True,
            "properties": properties,
            "gpt_analysis": gpt_analysis,
            "recommendation": properties["overall_assessment"]["likely_food_type"]
        }
        
    except Exception as e:
        return {"success": False, "error": f"통합 분석 실패: {str(e)}"}

def detect_with_integrated_system(image_bytes, strategy="smart", confidence_threshold=0.5, openai_api_key=None):
    """통합 시스템으로 재료 탐지 (FastAPI용)"""
    try:
        # 탐지기 인스턴스 생성/설정
        if openai_api_key:
            detector_instance.openai_api_key = openai_api_key
        
        # 전략별 처리
        if strategy == "smart":
            result = detector_instance.smart_detection_strategy(image_bytes, confidence_threshold)
        elif strategy == "yolo_only":
            detections, image = detector_instance.detect_objects(image_bytes, confidence_threshold)
            result = {
                "success": True,
                "strategy": "yolo_only",
                "detections": detections,
                "count": len(detections)
            }
        elif strategy == "comprehensive":
            result = detector_instance.comprehensive_analysis(image_bytes, use_gpt=True, confidence=confidence_threshold)
        else:
            # 기본값: 종합 분석
            result = detector_instance.comprehensive_analysis(image_bytes, use_gpt=bool(openai_api_key), confidence=confidence_threshold)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"통합 탐지 오류: {str(e)}"}

def enhanced_identify_item_from_image(image, use_gpt=True, openai_api_key=None):
    """개선된 재료 인식 함수 (호환성 유지)"""
    try:
        if openai_api_key:
            detector_instance.openai_api_key = openai_api_key
        
        if not use_gpt:
            # YOLO만 사용
            detections, _ = detector_instance.detect_objects(image, 0.5)
            
            if detections:
                ingredient_names = [det.get('class', 'unknown') for det in detections]
                return f"탐지된 재료: {', '.join(ingredient_names)}"
            else:
                return "재료를 탐지할 수 없습니다."
        else:
            # GPT 사용
            gpt_result = detector_instance.enhanced_gpt_analysis_with_properties(image)
            return gpt_result if gpt_result else "GPT 분석을 사용할 수 없습니다."
            
    except Exception as e:
        return f"재료 인식 오류: {str(e)}"


# ===== 유틸리티 함수들 =====

def create_temp_file_from_bytes(image_bytes, suffix='.jpg'):
    """바이트 데이터로부터 임시 파일 생성"""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(image_bytes)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print(f"❌ 임시 파일 생성 실패: {e}")
        return None

def cleanup_temp_file(file_path):
    """임시 파일 정리"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            return True
    except Exception as e:
        print(f"⚠️ 임시 파일 정리 실패: {e}")
    return False

def convert_detection_format(detections, target_format="standard"):
    """탐지 결과 형식 변환"""
    try:
        if target_format == "standard":
            # 표준 형식으로 변환
            return [
                {
                    "name": det.get("class", "unknown"),
                    "confidence": det.get("confidence", 0),
                    "bbox": det.get("bbox", []),
                    "source": det.get("model", "yolo")
                }
                for det in detections
            ]
        
        elif target_format == "simple":
            # 간단한 형식으로 변환
            return [det.get("class", "unknown") for det in detections]
        
        elif target_format == "detailed":
            # 상세 형식으로 변환
            detailed = []
            for i, det in enumerate(detections):
                bbox = det.get("bbox", [])
                detailed.append({
                    "id": i,
                    "name": det.get("class", "unknown"),
                    "confidence": round(det.get("confidence", 0), 3),
                    "bbox": {
                        "x1": bbox[0] if len(bbox) > 0 else 0,
                        "y1": bbox[1] if len(bbox) > 1 else 0,
                        "x2": bbox[2] if len(bbox) > 2 else 0,
                        "y2": bbox[3] if len(bbox) > 3 else 0,
                        "width": bbox[2] - bbox[0] if len(bbox) > 2 else 0,
                        "height": bbox[3] - bbox[1] if len(bbox) > 3 else 0
                    },
                    "area": (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) if len(bbox) == 4 else 0,
                    "model": det.get("model", "yolo")
                })
            return detailed
        
        else:
            return detections
            
    except Exception as e:
        print(f"❌ 형식 변환 실패: {e}")
        return detections 
