# 📁 cv-service/modules/ocr_processor.py - 병합 버전
import requests
import json
import traceback
import os
from typing import Optional, Dict, Any

# 🔸 팀원 방식: 환경변수 우선
CLOVA_OCR_API_URL = os.environ.get("CLOVA_OCR_API_URL")
CLOVA_SECRET_KEY = os.environ.get("CLOVA_SECRET_KEY")

# 🔸 내 방식: 환경변수 없으면 fallback 키 사용
DEFAULT_CLOVA_API_KEY = "d0d3aURrbHdoUHpJbFpCRWRMRkhJdkJ3U1dkRXZvalA="
DEFAULT_GEMINI_API_KEY = "AIzaSyBMLUwN-GEaC3yby5ItX9BHjfpybqMKGFg"

# 🔗 병합: 환경변수가 없으면 fallback 사용
if not CLOVA_SECRET_KEY:
    CLOVA_SECRET_KEY = DEFAULT_CLOVA_API_KEY
    print("⚠️ 환경변수에서 CLOVA_SECRET_KEY를 찾지 못해 기본 키를 사용합니다.")

if not CLOVA_OCR_API_URL:
    CLOVA_OCR_API_URL = "https://n0dcck6cu9.apigw.ntruss.com/custom/v1/42376/6cc36c80e643ae7f7a318f824e0d44e28ac43699286f2ab8c95dfd4d011a4e4f/general"
    print("⚠️ 환경변수에서 CLOVA_OCR_API_URL을 찾지 못해 기본 URL을 사용합니다.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", DEFAULT_GEMINI_API_KEY)

class GeminiQuestionPrompts:
    """
    🆕 내 고급 기능: 10가지 식품 분석 프롬프트
    """
    
    @staticmethod
    def get_food_name_prompt(text: str) -> str:
        return f"""당신은 한국의 식품 전문가입니다. OCR로 추출된 텍스트를 분석하여 정확한 식품명을 추론해주세요.

🎯 **분석 단계**:
1. 텍스트에서 브랜드명과 제품명 구분
2. 핵심 식품 카테고리 파악
3. 구체적인 제품 특성 확인

📋 **출력 형식**: [식품명]

💡 **예시**:
- "델몬트 100% 오렌지주스" → 오렌지주스
- "풀무원 유기농 두부" → 유기농 두부
- "스미후루 바나나" → 바나나

⚠️ **주의사항**: 브랜드명은 제외하고 실제 식품명만 추출하세요.

🔍 **분석할 텍스트**: {text}
"""

    @staticmethod  
    def get_nutrition_info_prompt(text: str) -> str:
        return f"""당신은 영양학 전문가입니다. OCR 텍스트에서 영양성분표를 정확히 분석해주세요.

📋 **출력 형식**:
- 칼로리: 000kcal
- 탄수화물: 00g
- 단백질: 00g
- 지방: 00g
- 나트륨: 000mg

⚠️ **정보 부족시**: "영양정보 불충분"

🔍 **분석할 텍스트**: {text}
"""

    @staticmethod
    def get_main_ingredients_prompt(text: str) -> str:
        return f"""당신은 식품 성분 분석 전문가입니다. OCR 텍스트에서 주요 원재료를 정확히 추출해주세요.

📋 **출력 형식**: [주재료1, 주재료2, 주재료3]

💡 **추출 기준**:
- 주원료: 제품의 핵심이 되는 재료
- 부재료나 첨가물은 제외
- 한국어 식품 용어 사용

🔍 **분석할 텍스트**: {text}
"""

    @staticmethod
    def get_cooking_method_prompt(text: str) -> str:
        return f"""당신은 한식/양식/중식을 아우르는 요리 전문가입니다. 텍스트의 식재료에 가장 적합한 조리법을 추천해주세요.

📋 **출력 형식**:
🔥 추천 조리법 TOP 3:
1. [조리법1] - 난이도: ⭐⭐ | 시간: 00분
2. [조리법2] - 난이도: ⭐⭐⭐ | 시간: 00분  
3. [조리법3] - 난이도: ⭐ | 시간: 00분

🔍 **분석할 텍스트**: {text}
"""

    @staticmethod
    def get_recipe_suggestions_prompt(text: str) -> str:
        return f"""당신은 한국의 유명 요리연구가입니다. OCR 텍스트의 식재료로 만들 수 있는 실용적인 레시피를 제안해주세요.

📋 **출력 형식**:
🍽️ 추천 레시피 3선:
1️⃣ [레시피명] - 조리시간: 00분 | 난이도: ⭐⭐
2️⃣ [레시피명] - 조리시간: 00분 | 난이도: ⭐⭐⭐
3️⃣ [레시피명] - 조리시간: 00분 | 난이도: ⭐

🔍 **분석할 텍스트**: {text}
"""

# 🔸 팀원 기본 함수 (원본 유지 + 약간의 개선)
def extract_text_with_ocr(image_path):
    """팀원 원본 OCR 함수 (안정성 검증됨)"""
    try:
        print(f"OCR 시작: {image_path}")
        print(f"API URL: {CLOVA_OCR_API_URL}")
        print(f"Secret Key 존재: {bool(CLOVA_SECRET_KEY)}")
        
        # 🔧 개선: 파일 형식 자동 감지
        file_format = _get_file_format(image_path)
        
        request_json = {
            'images': [
                {
                    'format': file_format,  # 🔧 동적 형식 설정
                    'name': 'food'
                }
            ],
            'requestId': 'food-ocr-request',
            'version': 'V2',
            'timestamp': 0
        }

        # JSON을 UTF-8로 인코딩
        payload = {'message': json.dumps(request_json, ensure_ascii=False).encode('UTF-8')}
        
        # 이미지 파일 열기
        with open(image_path, 'rb') as f:
            file_data = f.read()
            print(f"이미지 파일 크기: {len(file_data)} bytes")
            
        # API 요청 헤더
        headers = {'X-OCR-SECRET': CLOVA_SECRET_KEY}
        
        # 멀티파트 폼 형식으로 데이터 생성
        files = [
            ('file', ('food.jpg', file_data, f'image/{file_format}'))  # 🔧 동적 MIME 타입
        ]
        
        print("OCR API 요청 전송 중...")
        
        # API 요청 보내기 (타임아웃 추가)
        response = requests.post(
            CLOVA_OCR_API_URL, 
            headers=headers, 
            data=payload, 
            files=files,
            timeout=60  # 60초 타임아웃
        )
        
        print(f"OCR API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("OCR API 응답 성공")
            
            # OCR 결과에서 텍스트 추출
            extracted_text = []
            if 'images' in result and len(result['images']) > 0:
                if 'fields' in result['images'][0]:
                    for field in result['images'][0]['fields']:
                        if 'inferText' in field:
                            extracted_text.append(field['inferText'])
            
            full_text = ' '.join(extracted_text)
            print(f"OCR 추출 텍스트: {full_text}")
            return full_text
        else:
            print(f"OCR API 오류 - 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("OCR API 타임아웃 (60초)")
        return None
    except Exception as e:
        print(f"OCR 텍스트 추출 중 오류 발생: {e}")
        print(f"오류 세부 정보: {type(e).__name__}, {str(e)}")
        traceback.print_exc()
        return None

# 🆕 내 고급 기능: 통합 분석 클래스
class EnhancedOCRProcessor:
    """향상된 OCR 프로세서 (기본 OCR + Gemini 분석)"""
    
    def __init__(self):
        """초기화"""
        self.clova_api_url = CLOVA_OCR_API_URL
        self.clova_secret_key = CLOVA_SECRET_KEY
        self.gemini_api_key = GEMINI_API_KEY
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
        self.prompts = GeminiQuestionPrompts()
        
        # API 키 검증
        self._validate_keys()
    
    def _validate_keys(self):
        """API 키 유효성 검사"""
        if not self.clova_secret_key or len(self.clova_secret_key) < 10:
            print("⚠️ CLOVA OCR API 키가 설정되지 않았습니다.")
        
        if not self.gemini_api_key or len(self.gemini_api_key) < 10:
            print("⚠️ Gemini API 키가 설정되지 않았습니다.")
    
    def extract_and_analyze(self, image_path: str, analysis_types: list = None) -> Dict[str, Any]:
        """OCR + Gemini 통합 분석"""
        if analysis_types is None:
            analysis_types = ["food_name", "nutrition_info", "main_ingredients"]
        
        result = {
            'success': False,
            'ocr_text': None,
            'analyses': {},
            'method': 'enhanced_ocr',
            'error': None
        }
        
        try:
            # 1단계: 팀원 OCR 함수 사용
            print("🔍 1단계: OCR 텍스트 추출 (팀원 방식)")
            ocr_text = extract_text_with_ocr(image_path)
            
            if not ocr_text:
                result['error'] = "OCR 텍스트 추출 실패"
                return result
            
            result['ocr_text'] = ocr_text
            
            # 2단계: Gemini 분석 (내 방식)
            print("🤖 2단계: Gemini AI 분석 (고급 기능)")
            
            prompt_methods = {
                "food_name": self.prompts.get_food_name_prompt,
                "nutrition_info": self.prompts.get_nutrition_info_prompt,
                "main_ingredients": self.prompts.get_main_ingredients_prompt,
                "cooking_method": self.prompts.get_cooking_method_prompt,
                "recipe_suggestions": self.prompts.get_recipe_suggestions_prompt,
            }
            
            for analysis_type in analysis_types:
                if analysis_type in prompt_methods:
                    try:
                        print(f"  📋 {analysis_type} 분석 중...")
                        prompt = prompt_methods[analysis_type](ocr_text)
                        response = self._call_gemini_api(prompt)
                        result['analyses'][analysis_type] = response
                        print(f"  ✅ {analysis_type} 완료")
                    except Exception as e:
                        result['analyses'][analysis_type] = f"분석 실패: {str(e)}"
                        print(f"  ❌ {analysis_type} 실패: {e}")
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['error'] = f"통합 분석 중 오류: {str(e)}"
            print(f"❌ {result['error']}")
            traceback.print_exc()
            return result
    
    def _call_gemini_api(self, prompt: str, temperature: float = 0.2, max_tokens: int = 300) -> Optional[str]:
        """Gemini API 호출"""
        try:
            request_data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.gemini_api_key
            }
            
            json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
            
            response = requests.post(
                self.gemini_api_url, 
                headers=headers, 
                data=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_gemini_result(result)
            else:
                print(f"❌ Gemini API 오류 - 상태 코드: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Gemini API 호출 중 오류: {e}")
            return None
    
    def _parse_gemini_result(self, result: dict) -> Optional[str]:
        """Gemini 결과 파싱"""
        try:
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        return content['parts'][0]['text'].strip()
            return None
            
        except Exception as e:
            print(f"❌ Gemini 결과 파싱 중 오류: {e}")
            return None

# 🔧 보조 함수들
def _get_file_format(image_path: str) -> str:
    """파일 확장자에서 형식 추출"""
    extension = os.path.splitext(image_path)[1].lower()
    format_map = {
        '.jpg': 'jpg', 
        '.jpeg': 'jpg', 
        '.jfif': 'jpg',
        '.png': 'png',
        '.bmp': 'bmp', 
        '.gif': 'gif'
    }
    return format_map.get(extension, 'jpg')

# 🆕 통합 함수들 (FastAPI 호환)
def extract_text_enhanced(image_path: str, use_gemini: bool = False, analysis_types: list = None) -> Dict[str, Any]:
    """향상된 텍스트 추출 (선택적 Gemini 분석 포함)"""
    
    if not use_gemini:
        # 기본 OCR만 사용
        ocr_text = extract_text_with_ocr(image_path)
        return {
            "success": bool(ocr_text),
            "text": ocr_text,
            "method": "basic_ocr",
            "analyses": {}
        }
    else:
        # OCR + Gemini 분석
        processor = EnhancedOCRProcessor()
        return processor.extract_and_analyze(image_path, analysis_types)

def get_nutrition_analysis(image_path: str) -> Dict[str, Any]:
    """영양 분석 특화 함수"""
    return extract_text_enhanced(
        image_path, 
        use_gemini=True, 
        analysis_types=["food_name", "nutrition_info", "main_ingredients"]
    )

def get_cooking_analysis(image_path: str) -> Dict[str, Any]:
    """요리 분석 특화 함수"""
    return extract_text_enhanced(
        image_path, 
        use_gemini=True, 
        analysis_types=["food_name", "cooking_method", "recipe_suggestions"]
    )

def get_complete_analysis(image_path: str) -> Dict[str, Any]:
    """완전 분석 (모든 기능)"""
    return extract_text_enhanced(
        image_path, 
        use_gemini=True, 
        analysis_types=["food_name", "nutrition_info", "main_ingredients", "cooking_method", "recipe_suggestions"]
    )

# 🔍 상태 확인 함수
def get_ocr_status() -> Dict[str, Any]:
    """OCR 시스템 상태 확인"""
    return {
        "basic_ocr": {
            "clova_api_url": bool(CLOVA_OCR_API_URL),
            "clova_secret_key": bool(CLOVA_SECRET_KEY),
            "available": bool(CLOVA_OCR_API_URL and CLOVA_SECRET_KEY)
        },
        "enhanced_ocr": {
            "gemini_api_key": bool(GEMINI_API_KEY),
            "available": bool(GEMINI_API_KEY)
        },
        "features": {
            "basic_text_extraction": True,
            "nutrition_analysis": bool(GEMINI_API_KEY),
            "cooking_suggestions": bool(GEMINI_API_KEY),
            "complete_analysis": bool(GEMINI_API_KEY)
        }
    }

# 🧪 테스트 함수
def test_ocr_system(image_path: str = None):
    """OCR 시스템 테스트"""
    print("=== OCR 시스템 테스트 ===")
    
    # 상태 확인
    status = get_ocr_status()
    print(f"📊 시스템 상태: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if image_path and os.path.exists(image_path):
        print(f"\n🖼️ 테스트 이미지: {image_path}")
        
        # 기본 OCR 테스트
        print("\n1️⃣ 기본 OCR 테스트:")
        basic_result = extract_text_enhanced(image_path, use_gemini=False)
        print(f"결과: {basic_result}")
        
        # 향상된 OCR 테스트 (Gemini 있는 경우)
        if status["enhanced_ocr"]["available"]:
            print("\n2️⃣ 향상된 OCR 테스트:")
            enhanced_result = get_complete_analysis(image_path)
            print(f"결과: {enhanced_result}")
        else:
            print("\n⚠️ Gemini API 키가 없어 향상된 기능을 테스트할 수 없습니다.")
    else:
        print("⚠️ 테스트할 이미지 파일이 제공되지 않았습니다.")

# 🔥 하위 호환성을 위한 별칭
def enhanced_ocr_analysis(image_path: str) -> Dict[str, Any]:
    """하위 호환성을 위한 함수"""
    return get_complete_analysis(image_path)

if __name__ == "__main__":
    # 테스트 실행
    test_image = "test_image.jpg"  # 실제 테스트 이미지 경로로 변경
    test_ocr_system(test_image)