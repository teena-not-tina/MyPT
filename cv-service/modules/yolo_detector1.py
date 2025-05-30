# 📁 cv-service/modules/integrated_detector.py
import cv2
import numpy as np
import tempfile
import os
from .yolo_detector import YOLODetector, detector_instance
from .gpt_vision_detector import GPTVisionDetector, HybridDetector
import openai

class IntegratedFoodDetector:
    def __init__(self, openai_api_key=None):
        """통합 식품 탐지 시스템"""
        self.yolo_detector = detector_instance
        self.gpt_detector = GPTVisionDetector(api_key=openai_api_key)
        self.hybrid_detector = HybridDetector(self.yolo_detector, self.gpt_detector)
        
        # 탐지 전략 설정
        self.detection_strategies = {
            "yolo_first": self._yolo_first_strategy,
            "gpt_first": self._gpt_first_strategy,
            "parallel": self._parallel_strategy,
            "smart": self._smart_strategy
        }
    
    def detect_ingredients(self, image, strategy="smart", confidence_threshold=0.5):
        """통합 재료 탐지"""
        try:
            detection_func = self.detection_strategies.get(strategy, self._smart_strategy)
            return detection_func(image, confidence_threshold)
        except Exception as e:
            print(f"❌ 통합 탐지 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy
            }
    
    def _yolo_first_strategy(self, image, confidence_threshold):
        """YOLO 우선 전략 (빠른 탐지)"""
        print("🎯 전략: YOLO 우선")
        
        # 1차: YOLO 탐지
        yolo_results = self._run_yolo_detection(image, confidence_threshold)
        
        # YOLO 결과가 충분히 신뢰할 만하면 GPT 생략
        if yolo_results.get("success") and len(yolo_results.get("detections", [])) > 0:
            high_conf_detections = [
                det for det in yolo_results["detections"]
                if det.get("confidence", 0) > 0.7  # 높은 신뢰도만
            ]
            
            if high_conf_detections:
                print(f"✅ YOLO 고신뢰도 결과 사용: {len(high_conf_detections)}개")
                return {
                    "success": True,
                    "strategy": "yolo_only",
                    "ingredients": high_conf_detections,
                    "detection_time": "fast",
                    "yolo_results": yolo_results
                }
        
        # 2차: GPT 보완
        print("🔄 GPT-4o-mini 보완 분석...")
        gpt_results = self._run_gpt_detection(image, "detailed")
        
        return self._merge_results(yolo_results, gpt_results, "yolo_first")
    
    def _gpt_first_strategy(self, image, confidence_threshold):
        """GPT 우선 전략 (정확한 탐지)"""
        print("🧠 전략: GPT 우선")
        
        # 1차: GPT 탐지
        gpt_results = self._run_gpt_detection(image, "detailed")
        
        # 2차: YOLO 보완 (위치 정보 추가)
        yolo_results = self._run_yolo_detection(image, confidence_threshold)
        
        return self._merge_results(yolo_results, gpt_results, "gpt_first")
    
    def _parallel_strategy(self, image, confidence_threshold):
        """병렬 전략 (최대 정확도)"""
        print("⚡ 전략: 병렬 처리")
        
        # 동시 실행 (실제로는 순차적이지만 결과 동등 처리)
        yolo_results = self._run_yolo_detection(image, confidence_threshold)
        gpt_results = self._run_gpt_detection(image, "detailed")
        
        return self._merge_results(yolo_results, gpt_results, "parallel")
    
    def _smart_strategy(self, image, confidence_threshold):
        """스마트 전략 (상황별 최적화)"""
        print("🤖 전략: 스마트 선택")
        
        # 이미지 특성 분석
        image_analysis = self._analyze_image_characteristics(image)
        
        if image_analysis["is_simple_scene"]:
            # 단순한 장면 → YOLO 우선
            print("📷 단순 장면 감지 → YOLO 우선")
            return self._yolo_first_strategy(image, confidence_threshold)
        
        elif image_analysis["has_text_overlay"]:
            # 텍스트가 많은 이미지 → GPT 우선
            print("📝 텍스트 감지 → GPT 우선")
            return self._gpt_first_strategy(image, confidence_threshold)
        
        else:
            # 복잡한 장면 → 병렬 처리
            print("🔍 복잡 장면 감지 → 병렬 처리")
            return self._parallel_strategy(image, confidence_threshold)
    
    def _run_yolo_detection(self, image, confidence_threshold):
        """YOLO 탐지 실행"""
        try:
            # 임시 파일로 저장 (YOLO는 파일 경로 필요)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                cv2.imwrite(temp_file.name, image)
                temp_path = temp_file.name
            
            # YOLO 탐지 실행
            detections, _ = self.yolo_detector.detect_objects(temp_path, confidence_threshold)
            
            # 임시 파일 삭제
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return {
                "success": True,
                "detections": detections,
                "method": "yolo",
                "count": len(detections)
            }
            
        except Exception as e:
            print(f"❌ YOLO 탐지 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "yolo"
            }
    
    def _run_gpt_detection(self, image, analysis_type="detailed"):
        """GPT 탐지 실행"""
        try:
            result = self.gpt_detector.identify_ingredients_detailed(image, analysis_type)
            
            if result and result.get("success"):
                return {
                    "success": True,
                    "ingredients": result.get("ingredients", []),
                    "notes": result.get("notes", ""),
                    "method": "gpt",
                    "count": len(result.get("ingredients", []))
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "GPT 분석 실패"),
                    "method": "gpt"
                }
                
        except Exception as e:
            print(f"❌ GPT 탐지 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "gpt"
            }
    
    def _merge_results(self, yolo_results, gpt_results, strategy):
        """결과 병합"""
        merged_ingredients = []
        
        # YOLO 결과 처리
        if yolo_results.get("success"):
            for detection in yolo_results.get("detections", []):
                merged_ingredients.append({
                    "name": detection.get("class", "알수없음"),
                    "confidence": detection.get("confidence", 0),
                    "bbox": detection.get("bbox"),
                    "source": "yolo",
                    "model": detection.get("model", "unknown")
                })
        
        # GPT 결과 처리
        if gpt_results.get("success"):
            for ingredient in gpt_results.get("ingredients", []):
                # 중복 체크
                ingredient_name = ingredient.get("name", "").lower()
                existing = any(
                    item["name"].lower() == ingredient_name 
                    for item in merged_ingredients
                )
                
                if not existing:
                    merged_ingredients.append({
                        "name": ingredient.get("name", "알수없음"),
                        "category": ingredient.get("category", "기타"),
                        "confidence_text": ingredient.get("confidence", "보통"),
                        "description": ingredient.get("description", ""),
                        "source": "gpt"
                    })
        
        # 최종 결과
        return {
            "success": True,
            "strategy": strategy,
            "total_ingredients": len(merged_ingredients),
            "ingredients": merged_ingredients,
            "yolo_results": yolo_results,
            "gpt_results": gpt_results,
            "detection_summary": {
                "yolo_count": yolo_results.get("count", 0),
                "gpt_count": gpt_results.get("count", 0),
                "merged_count": len(merged_ingredients)
            }
        }
    
    def _analyze_image_characteristics(self, image):
        """이미지 특성 분석"""
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
                "dimensions": (w, h)
            }
            
        except Exception as e:
            print(f"⚠️ 이미지 분석 실패: {e}")
            return {
                "is_simple_scene": False,
                "has_text_overlay": False,
                "complexity_score": 5.0,
                "dimensions": (0, 0)
            }

# FastAPI 통합을 위한 래퍼 함수들
def detect_with_integrated_system(image_bytes, strategy="smart", confidence_threshold=0.5, openai_api_key=None):
    """통합 시스템으로 재료 탐지"""
    try:
        # 바이트를 이미지로 변환
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return {"success": False, "error": "이미지 디코딩 실패"}
        
        # 통합 탐지기 초기화
        detector = IntegratedFoodDetector(openai_api_key)
        
        # 탐지 실행
        result = detector.detect_ingredients(image, strategy, confidence_threshold)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"통합 탐지 오류: {str(e)}"}

# 기존 함수와의 호환성을 위한 개선된 래퍼
def enhanced_identify_item_from_image(image, use_gpt=True, openai_api_key=None):
    """개선된 재료 인식 함수"""
    
    if not use_gpt:
        # YOLO만 사용하는 경우
        try:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                cv2.imwrite(temp_file.name, image)
                temp_path = temp_file.name
            
            detections, _ = detector_instance.detect_objects(temp_path, 0.5)
            
            # 임시 파일 삭제
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if detections:
                ingredient_names = [det.get('class', 'unknown') for det in detections]
                return f"탐지된 재료: {', '.join(ingredient_names)}"
            else:
                return "재료를 탐지할 수 없습니다."
                
        except Exception as e:
            return f"YOLO 탐지 오류: {str(e)}"
    
    else:
        # GPT-4o-mini 사용
        try:
            gpt_detector = GPTVisionDetector(api_key=openai_api_key)
            return gpt_detector.identify_item_from_image(image)
        except Exception as e:
            return f"GPT 탐지 오류: {str(e)}"

# 🔥 프롬프트 최적화 전략
class AdvancedPromptStrategy:
    """고급 프롬프트 전략"""
    
    @staticmethod
    def get_korean_food_prompt():
        """한국 음식 특화 프롬프트"""
        return """
당신은 한국 요리 전문가입니다. 한국 가정의 냉장고/식재료 사진을 분석해주세요.

🇰🇷 **한국 식재료 우선 인식**:
- 김치, 된장, 고추장, 간장 등 한국 전통 발효식품
- 배추, 무, 대파, 마늘, 생강 등 한국 채소
- 쌀, 현미, 잡곡 등 한국 주식
- 김, 미역, 다시마 등 해조류
- 고춧가루, 참기름, 들기름 등 한국 양념

📋 **결과 형식**:
```json
{
    "korean_ingredients": ["한국 전통 재료들"],
    "general_ingredients": ["일반 재료들"],
    "recommended_korean_dishes": ["추천 한국 요리 3가지"],
    "missing_for_korean_cooking": ["한국 요리에 필요한 추가 재료"]
}
```

이미지를 분석해주세요!
"""
    
    @staticmethod
    def get_health_focused_prompt():
        """건강 중심 프롬프트"""
        return """
영양학 전문가 관점에서 이미지의 식재료를 분석해주세요.

🍎 **영양학적 분석 기준**:
1. 영양소별 분류 (탄수화물, 단백질, 지방, 비타민, 미네랄)
2. 건강 효능 분석
3. 칼로리 추정
4. 다이어트/건강식 적합성

📊 **결과 형식**:
```json
{
    "nutrition_analysis": {
        "high_protein": ["단백질 풍부 식품"],
        "vitamins_minerals": ["비타민/미네랄 공급원"],
        "healthy_carbs": ["건강한 탄수화물"],
        "healthy_fats": ["좋은 지방"]
    },
    "health_score": "1-10점",
    "diet_compatibility": {
        "keto": "적합/부적합",
        "low_carb": "적합/부적합",
        "mediterranean": "적합/부적합"
    },
    "recommended_combinations": ["영양 균형 조합 3가지"]
}
```
"""
    
    @staticmethod
    def get_cooking_method_prompt():
        """조리법 중심 프롬프트"""
        return """
요리 전문가로서 이 재료들로 가능한 조리법을 분석해주세요.

👨‍🍳 **조리법 분석**:
1. 재료별 최적 조리법
2. 재료 조합 가능성
3. 난이도별 요리 제안
4. 조리 시간 추정

🍳 **결과 형식**:
```json
{
    "quick_recipes": ["15분 이내 요리"],
    "medium_recipes": ["30분 이내 요리"],
    "advanced_recipes": ["1시간 이상 요리"],
    "ingredient_prep": {
        "재료명": "최적 손질법"
    },
    "cooking_tips": ["조리 팁 3가지"]
}
```
"""

# 🎯 특화된 탐지 클래스
class SpecializedDetector(GPTVisionDetector):
    """특화된 탐지 기능"""
    
    def detect_korean_ingredients(self, image):
        """한국 식재료 특화 탐지"""
        prompt = AdvancedPromptStrategy.get_korean_food_prompt()
        
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
                                "url": f"data:image/jpeg;base64,{self.encode_image_to_base64(image)}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    def analyze_for_health(self, image):
        """건강/영양 중심 분석"""
        prompt = AdvancedPromptStrategy.get_health_focused_prompt()
        
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
                                "url": f"data:image/jpeg;base64,{self.encode_image_to_base64(image)}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    def suggest_cooking_methods(self, image):
        """조리법 제안"""
        prompt = AdvancedPromptStrategy.get_cooking_method_prompt()
        
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
                                "url": f"data:image/jpeg;base64,{self.encode_image_to_base64(image)}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.2
        )
        
        return response.choices[0].message.content.strip()

# 📊 성능 비교 및 검증
class DetectionValidator:
    """탐지 결과 검증"""
    
    def __init__(self):
        self.known_ingredients = {
            "과일": ["사과", "바나나", "오렌지", "키위", "딸기", "포도"],
            "채소": ["당근", "양파", "마늘", "생강", "감자", "고구마"],
            "육류": ["소고기", "돼지고기", "닭고기"],
            "유제품": ["우유", "치즈", "요거트", "버터"]
        }
    
    def validate_results(self, yolo_results, gpt_results):
        """결과 검증 및 신뢰도 계산"""
        validation = {
            "yolo_accuracy": self._calculate_accuracy(yolo_results, "yolo"),
            "gpt_accuracy": self._calculate_accuracy(gpt_results, "gpt"),
            "consistency_score": self._calculate_consistency(yolo_results, gpt_results),
            "recommendation": ""
        }
        
        # 추천 로직
        if validation["consistency_score"] > 0.7:
            validation["recommendation"] = "두 모델 결과가 일치함 - 신뢰도 높음"
        elif validation["gpt_accuracy"] > validation["yolo_accuracy"]:
            validation["recommendation"] = "GPT 결과 우선 권장"
        else:
            validation["recommendation"] = "YOLO 결과 우선 권장"
        
        return validation
    
    def _calculate_accuracy(self, results, method):
        """정확도 계산 (알려진 재료와 비교)"""
        if not results:
            return 0.0
        
        known_count = 0
        total_count = 0
        
        if method == "yolo":
            for detection in results.get("detections", []):
                ingredient = detection.get("class", "").lower()
                total_count += 1
                if self._is_known_ingredient(ingredient):
                    known_count += 1
        
        elif method == "gpt":
            for ingredient in results.get("ingredients", []):
                ingredient_name = ingredient.get("name", "").lower()
                total_count += 1
                if self._is_known_ingredient(ingredient_name):
                    known_count += 1
        
        return known_count / total_count if total_count > 0 else 0.0
    
    def _is_known_ingredient(self, ingredient_name):
        """알려진 재료인지 확인"""
        for category_items in self.known_ingredients.values():
            if any(known.lower() in ingredient_name for known in category_items):
                return True
        return False
    
    def _calculate_consistency(self, yolo_results, gpt_results):
        """두 결과 간 일관성 계산"""
        yolo_ingredients = set()
        gpt_ingredients = set()
        
        # YOLO 재료 추출
        for detection in yolo_results.get("detections", []):
            yolo_ingredients.add(detection.get("class", "").lower())
        
        # GPT 재료 추출
        for ingredient in gpt_results.get("ingredients", []):
            gpt_ingredients.add(ingredient.get("name", "").lower())
        
        if not yolo_ingredients and not gpt_ingredients:
            return 1.0
        
        # 교집합 / 합집합
        intersection = len(yolo_ingredients & gpt_ingredients)
        union = len(yolo_ingredients | gpt_ingredients)
        
        return intersection / union if union > 0 else 0.0