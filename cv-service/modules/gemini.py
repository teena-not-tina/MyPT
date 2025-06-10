# modules/gemini.py

import os
import requests
import json
import traceback
import re

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")

BRAND_PATTERNS = {
    '농심': ['신라면', '너구리', '안성탕면', '짜파게티', '육개장', '새우탕', '올리브'],
    '오뚜기': ['진라면', '스낵면', '컵누들', '참치마요', '카레'],
    '롯데': ['초코파이', '가나초콜릿', '빼빼로', '칸쵸', '몽쉘'],
    '해태': ['홈런볼', '맛동산', '오예스', '허니버터칩'],
    '오리온': ['초코파이', '닥터유', '참붕어빵', '치토스'],
    '삼양': ['불닭볶음면', '까르보', '삼양라면'],
    '팔도': ['팔도비빔면', '왕뚜껑'],
    'CJ': ['햇반', '비비고'],
    '동원': ['참치캔', '김치찌개', '양반김'],
    '빙그레': ['바나나우유', '메로나', '투게더'],
    '매일': ['매일우유', '상하목장'],
    '서울우유': ['서울우유', '아이셔'],
    '코카콜라': ['코카콜라', '스프라이트', '환타'],
    '펩시': ['펩시콜라', '마운틴듀'],
    '롯데칠성': ['칠성사이다', '델몬트', '펩시'],
    '동서식품': ['맥심', '포스트'],
    '네슬레': ['네스카페', '킷캣'],
    '크라운': ['산도', '쿠크다스'],
    '동양제과': ['초코하임', '요하임'],
    '남양': ['남양유업', '불가리스', '홍삼정', '초코에몽'],
    '광동': ['비타500', '홍삼정', '옥수수수염차'],
}

def preprocess_text_for_brand_detection(text):
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_brand_and_product(text):
    if not text:
        return None, None
    preprocessed_text = preprocess_text_for_brand_detection(text)
    text_upper = preprocessed_text.upper()
    detected_brand, detected_product, max_confidence = None, None, 0
    for brand, products in BRAND_PATTERNS.items():
        brand_upper = brand.upper()
        if brand in preprocessed_text or brand_upper in text_upper:
            for product in products:
                if product in preprocessed_text or product.upper() in text_upper:
                    confidence = len(brand) + len(product)
                    if confidence > max_confidence:
                        detected_brand, detected_product = brand, product
                        max_confidence = confidence
    if not detected_brand:
        for brand, products in BRAND_PATTERNS.items():
            for product in products:
                if product in preprocessed_text or product.upper() in text_upper:
                    confidence = len(product)
                    if confidence > max_confidence:
                        detected_brand, detected_product = brand, product
                        max_confidence = confidence
    return detected_brand, detected_product

def extract_keywords(text, min_length=2):
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.strip().split()
    return list(set([w for w in words if len(w) >= min_length]))

def google_search_keywords(keywords, max_results=3):
    import urllib.parse
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return [], []
    query = urllib.parse.quote_plus(' '.join(keywords))
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={query}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            titles = [item['title'] for item in data.get("items", [])[:max_results]]
            snippets = [item['snippet'] for item in data.get("items", [])[:max_results]]
            return titles, snippets
    except:
        pass
    return [], []

def analyze_with_google_and_gemini(text, detection_results=None):
    keywords = extract_keywords(text)
    print(f"🔍 키워드: {keywords}")
    titles, _ = google_search_keywords(keywords)
    google_summary = "\n".join([f"- {t}" for t in titles]) if titles else "검색 결과 없음"
    augmented_text = text + f"\n\n[Google 검색 결과]\n{google_summary}"
    
    # analyze_text_with_gemini가 None을 반환할 수 있으므로 확인
    result = analyze_text_with_gemini(augmented_text, detection_results)
    if result is None:
        print("ℹ️ Google 검색 강화 분석에서도 식품이 아닌 것으로 판단됨")
    return result

def check_if_food_product(text):
    """텍스트가 식품 관련인지 확인하는 함수"""
    if not text or text.strip() == "":
        return False
    
    try:
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다")
            return False
        
        # 식품 여부 확인 프롬프트
        prompt = f"""다음 텍스트가 식품(먹을 수 있는 것)의 포장지나 라벨에서 나온 것인지 판단해주세요.

텍스트: {text}

다음 중 하나로만 답해주세요:
- "식품": 먹거나 마실 수 있는 제품 (과자, 음료, 라면, 우유, 빵 등)
- "비식품": 먹을 수 없는 제품 (전자제품, 책, 의류, 문구류 등)

판단 기준:
1. 칼로리, 영양성분, 원재료, 유통기한 등의 정보가 있으면 식품
2. 식품 브랜드나 제품명이 명확하면 식품
3. 먹는 방법, 조리법 등이 있으면 식품
4. 전자제품, 의류, 문구, 도서 등의 키워드가 있으면 비식품

답변 (한 단어로만):"""
        
        request_data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 10,
                "topP": 0.5,
                "topK": 10
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
        
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            data=json_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        answer = content['parts'][0]['text'].strip().lower()
                        print(f"🔍 식품 여부 판단: {answer}")
                        return "식품" in answer
        
        return False
        
    except Exception as e:
        print(f"❌ 식품 여부 확인 중 오류: {e}")
        # 오류 시 브랜드 탐지로 대체 판단
        detected_brand, _ = detect_brand_and_product(text)
        return detected_brand is not None

def is_valid_food_name(food_name):
    """추론된 이름이 실제 식품인지 검증"""
    if not food_name:
        return False
    
    # 비식품 패턴 목록
    non_food_patterns = [
        # 이미지/사진 관련
        r'\d+RF', 'SHUTTERSTOCK', 'GETTY', 'PIXABAY', 'UNSPLASH',
        'ADOBE STOCK', 'ISTOCK', 'DREAMSTIME', 'ALAMY',
        # 기술/전자제품 관련
        'SAMSUNG', 'APPLE', 'LG전자', 'SONY', 'MICROSOFT',
        'GOOGLE', 'AMAZON', 'FACEBOOK', 'INTEL', 'AMD',
        # 의류/패션 브랜드
        'NIKE', 'ADIDAS', 'PUMA', 'ZARA', 'H&M', 'UNIQLO',
        # 문구/사무용품
        'MONAMI', '모나미', 'STAEDTLER', 'PILOT',
        # 기타 비식품
        '전자', '기기', '디바이스', '소프트웨어', '하드웨어',
        '의류', '신발', '가방', '문구', '사무용품', '도서'
    ]
    
    food_name_upper = food_name.upper()
    
    # 비식품 패턴 체크
    for pattern in non_food_patterns:
        if isinstance(pattern, str) and pattern.upper() in food_name_upper:
            print(f"⚠️ 비식품 패턴 감지: {pattern}")
            return False
        elif hasattr(pattern, 'search') and re.search(pattern, food_name, re.IGNORECASE):
            print(f"⚠️ 비식품 패턴 감지: {pattern}")
            return False
    
    # 식품 관련 키워드가 있는지 확인
    food_keywords = [
        '라면', '과자', '음료', '우유', '빵', '김치', '참치',
        '커피', '차', '주스', '콜라', '사이다', '맥주',
        '초콜릿', '사탕', '젤리', '쿠키', '비스킷',
        '스낵', '칩', '포테이토', '새우깡', '양파링'
    ]
    
    # 알려진 식품 브랜드가 있는지 확인
    for brand in BRAND_PATTERNS.keys():
        if brand in food_name:
            return True
    
    # 식품 키워드가 있는지 확인
    for keyword in food_keywords:
        if keyword in food_name:
            return True
    
    # 숫자와 영문자만으로 구성된 짧은 문자열은 제품코드일 가능성
    if re.match(r'^[A-Z0-9]{2,6}$', food_name_upper):
        print(f"⚠️ 제품코드 패턴으로 의심됨: {food_name}")
        return False
    
    return True

def analyze_text_with_gemini(text, detection_results=None):
    """개선된 Gemini 함수 - 식품이 아닌 경우 None 반환"""
    if not text or text.strip() == "":
        print("📝 분석할 텍스트가 없습니다.")
        return None
    
    try:
        print(f"🧠 Gemini 분석 시작 - 텍스트 길이: {len(text)}")
        print(f"🔑 API Key 존재: {bool(GEMINI_API_KEY)}")
        
        # 환경 변수 확인
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다")
            print("   환경 변수를 확인하세요: GEMINI_API_KEY")
            return None
        
        # 먼저 식품인지 확인
        is_food = check_if_food_product(text)
        if not is_food:
            print("ℹ️ 식품이 아닌 것으로 판단되어 분석을 중단합니다.")
            return None
        
        # 1단계: 직접 브랜드/제품명 탐지
        detected_brand, detected_product = detect_brand_and_product(text)
        brand_context = ""
        if detected_brand and detected_product:
            brand_context = f"\n\n중요: 텍스트에서 '{detected_brand} {detected_product}' 브랜드/제품이 직접 탐지되었습니다. 이를 최우선으로 고려하세요."
            print(f"🔍 직접 탐지된 브랜드/제품: {detected_brand} {detected_product}")
        elif detected_brand:
            brand_context = f"\n\n중요: 텍스트에서 '{detected_brand}' 브랜드가 탐지되었습니다."
            print(f"🔍 직접 탐지된 브랜드: {detected_brand}")
        
        # 탐지 결과가 있으면 컨텍스트에 포함
        detection_context = ""
        if detection_results and len(detection_results) > 0:
            detected_classes = [det['class'] for det in detection_results if det['class'] != 'other']
            if detected_classes:
                detection_context = f"\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: {', '.join(detected_classes)}"
            else:
                detection_context = "\n\n참고: 이미지에서 알려진 식품이 탐지되지 않았습니다."
        
        # 개선된 프롬프트 - 브랜드/제품명 우선 추론 강화
        prompt = f"""식품의 포장지를 OCR로 추출한 텍스트를 분석해서 어떤 식품인지 추론해주세요.

추출된 텍스트: {text}{brand_context}{detection_context}

분석 지침 (중요도 순):
1. **실제 유통 중인 브랜드+제품명 조합을 최우선으로 추론하세요**
   - 예시: "농심 신라면", "오뚜기 진라면", "롯데 초코파이", "삼양 불닭볶음면", "광동 비타500"
   - 브랜드와 제품명이 모두 확인되면 반드시 그 조합을 사용하세요
   
2. **주요 브랜드별 대표 제품들:**
   - 농심: 신라면, 너구리, 안성탕면, 짜파게티, 육개장
   - 오뚜기: 진라면, 컵누들, 참치마요, 카레
   - 롯데: 초코파이, 가나초콜릿, 빼빼로, 칸쵸
   - 해태: 홈런볼, 맛동산, 허니버터칩
   - 삼양: 불닭볶음면, 까르보
   - 빙그레: 바나나우유, 메로나
   - 광동: 비타500, 홍삼정
   
3. **제품명 추론 우선순위:**
   - 1순위: 완전한 "브랜드명 + 제품명" (예: 농심 신라면)
   - 2순위: 명확한 제품명 (브랜드 유추 가능)
   - 3순위: 일반적인 식품 카테고리명
   
4. **응답 형식:**
   - 첫 번째 줄에만 추론된 식품명을 명확하게 작성
   - 가능한 한 "브랜드명 + 제품명" 형태로 답변

텍스트에서 브랜드명과 제품명을 찾을 수 있다면 반드시 그 조합으로 답변하세요."""
        
        request_data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.05,
                "maxOutputTokens": 200,
                "topP": 0.7,
                "topK": 20
            }
        }
        
        # API 요청 헤더
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        # API 요청 데이터를 JSON으로 직접 직렬화하여 인코딩 문제 방지
        json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
        
        print("📤 Gemini API 요청 전송 중...")
        
        # API 요청 보내기 (data 파라미터 사용)
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            data=json_data,
            timeout=30
        )
        
        print(f"📥 Gemini API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        inference_result = content['parts'][0]['text']
                        print(f"🎯 Gemini API 추론 결과: {inference_result}")
                        
                        # 결과 후처리 - 첫 번째 줄만 추출하여 식품명만 반환
                        food_name = extract_food_name_from_result(inference_result, detected_brand, detected_product)
                        
                        # 추출된 식품명이 None이면 (비식품으로 판단된 경우)
                        if food_name is None:
                            print("ℹ️ 추론 결과가 식품이 아닌 것으로 판단되어 None 반환")
                            return None
                            
                        print(f"✅ 추출된 식품명: {food_name}")
                        
                        return food_name
        
        print(f"❌ Gemini API 오류 - 상태 코드: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"📋 오류 상세: {error_detail}")
        except:
            print(f"📋 응답 내용: {response.text}")
        
        # API 실패 시 직접 탐지된 결과 반환
        if detected_brand and detected_product:
            fallback_result = f"{detected_brand} {detected_product}"
            print(f"🔄 API 실패로 직접 탐지 결과 반환: {fallback_result}")
            return fallback_result
        
        return None
        
    except requests.exceptions.Timeout:
        print("⏰ Gemini API 타임아웃 (30초)")
        # 타임아웃 시에도 직접 탐지 결과 반환
        detected_brand, detected_product = detect_brand_and_product(text)
        if detected_brand and detected_product:
            return f"{detected_brand} {detected_product}"
        return None
    except requests.exceptions.ConnectionError:
        print("🌐 Gemini API 연결 오류")
        return None
    except requests.exceptions.RequestException as e:
        print(f"📡 Gemini API 요청 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ Gemini API 분석 중 예상치 못한 오류: {e}")
        print(f"🔍 오류 세부 정보: {type(e).__name__}, {str(e)}")
        traceback.print_exc()
        # 오류 시에도 직접 탐지 결과 반환
        detected_brand, detected_product = detect_brand_and_product(text)
        if detected_brand and detected_product:
            return f"{detected_brand} {detected_product}"
        return None

def extract_food_name_from_result(result_text, detected_brand=None, detected_product=None):
    """Gemini 결과에서 식품명만 추출하는 함수 - 브랜드/제품명 우선"""
    if not result_text:
        # Gemini 결과가 없으면 직접 탐지된 결과 사용
        if detected_brand and detected_product:
            return f"{detected_brand} {detected_product}"
        return None
    
    try:
        # 줄 단위로 분리
        lines = result_text.strip().split('\n')
        
        # 첫 번째 줄에서 식품명 추출
        first_line = lines[0].strip()
        
        # 불필요한 접두사 제거
        prefixes_to_remove = [
            "추론된 식품:", "식품명:", "제품명:", "상품명:",
            "분석 결과:", "결과:", "답변:", "식품:",
            "추론 결과:", "판단 결과:", "**", "*"
        ]
        
        for prefix in prefixes_to_remove:
            if first_line.startswith(prefix):
                first_line = first_line[len(prefix):].strip()
        
        # 마크다운 굵은 글씨 제거
        first_line = first_line.replace("**", "").replace("*", "")
        
        # 괄호 안의 부가 설명 제거 (예: "신라면 (매운맛)" -> "신라면")
        if "(" in first_line and ")" in first_line:
            first_line = first_line.split("(")[0].strip()
        
        # 추론된 결과가 실제 식품인지 검증
        if not is_valid_food_name(first_line):
            print(f"❌ 추론 결과가 식품이 아님: {first_line}")
            # 직접 탐지된 브랜드/제품이 있으면 사용
            if detected_brand and detected_product:
                fallback = f"{detected_brand} {detected_product}"
                if is_valid_food_name(fallback):
                    return fallback
            return None
        
        # 직접 탐지된 브랜드/제품과 일치하는지 확인
        if detected_brand and detected_product:
            expected_name = f"{detected_brand} {detected_product}"
            # Gemini 결과에 브랜드+제품명이 포함되어 있으면 우선 사용
            if detected_brand in first_line and detected_product in first_line:
                if len(first_line) <= len(expected_name) + 10:  # 너무 길지 않으면
                    return first_line
            # 그렇지 않으면 직접 탐지된 결과 사용
            else:
                return expected_name
        
        return first_line if first_line else None
        
    except Exception as e:
        print(f"❌ 식품명 추출 중 오류: {e}")
        # 오류 시 직접 탐지된 결과 사용
        if detected_brand and detected_product:
            fallback = f"{detected_brand} {detected_product}"
            if is_valid_food_name(fallback):
                return fallback
        return None

def analyze_text_with_gemini_detailed(text, detection_results=None):
    """상세한 분석이 필요한 경우를 위한 함수 - 식품 확인 후 분석"""
    if not text or text.strip() == "":
        print("📝 분석할 텍스트가 없습니다.")
        return None
    
    try:
        print(f"🧠 Gemini 상세 분석 시작 - 텍스트 길이: {len(text)}")
        
        # 환경 변수 확인
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다")
            return None
        
        # 먼저 식품인지 확인
        is_food = check_if_food_product(text)
        if not is_food:
            print("ℹ️ 식품이 아닌 것으로 판단되어 상세 분석을 중단합니다.")
            return json.dumps({
                "product_name": None,
                "brand": None,
                "category": "비식품",
                "is_food": False,
                "message": "식품이 아닌 것으로 판단됨"
            }, ensure_ascii=False, indent=2)
        
        # 직접 브랜드/제품명 탐지
        detected_brand, detected_product = detect_brand_and_product(text)
        
        # 탐지 결과가 있으면 컨텍스트에 포함
        detection_context = ""
        if detection_results and len(detection_results) > 0:
            detected_classes = [det['class'] for det in detection_results if det['class'] != 'other']
            if detected_classes:
                detection_context = f"\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: {', '.join(detected_classes)}"
        
        # 브랜드 탐지 컨텍스트
        brand_context = ""
        if detected_brand and detected_product:
            brand_context = f"\n\n중요: '{detected_brand} {detected_product}' 브랜드/제품이 탐지되었습니다."
        
        # 상세 분석 프롬프트
        prompt = f"""식품의 포장지를 OCR로 추출한 텍스트를 분석해서 상세한 정보를 제공해주세요.

추출된 텍스트: {text}{brand_context}{detection_context}

다음 정보를 JSON 형태로 제공해주세요:
{{
    "product_name": "추론된 제품명 (브랜드명 포함, 예: 농심 신라면)",
    "brand": "브랜드명",
    "category": "식품 카테고리",
    "flavor": "맛/향 정보",
    "confidence": "추론 신뢰도 (1-10)",
    "reasoning": "추론 근거",
    "is_food": true
}}

실제 유통 중인 제품명을 최우선으로 추론하세요. 브랜드명과 제품명이 모두 확인되면 반드시 그 조합을 사용하세요."""
        
        request_data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
        
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            data=json_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        inference_result = content['parts'][0]['text']
                        print(f"📊 Gemini API 상세 분석 결과: {inference_result}")
                        return inference_result
        
        # API 실패 시 직접 탐지된 결과로 기본 JSON 생성
        if detected_brand and detected_product:
            fallback_json = {
                "product_name": f"{detected_brand} {detected_product}",
                "brand": detected_brand,
                "category": "식품",
                "flavor": "확인 필요",
                "confidence": 8,
                "reasoning": "텍스트에서 브랜드와 제품명이 직접 탐지됨",
                "is_food": True
            }
            return json.dumps(fallback_json, ensure_ascii=False, indent=2)
        
        return None
        
    except Exception as e:
        print(f"❌ Gemini API 상세 분석 중 오류 발생: {e}")
        traceback.print_exc()
        return None

def test_brand_detection():
    """브랜드/제품명 탐지 테스트"""
    test_texts = [
        "농심 신라면 매운맛",
        "오뚜기 진라면 순한맛",
        "롯데 초코파이 12개들이",
        "삼양 불닭볶음면",
        "해태 허니버터칩",
        "광동 비타500"
    ]
    
    for text in test_texts:
        brand, product = detect_brand_and_product(text)
        print(f"텍스트: {text}")
        print(f"탐지 결과: 브랜드={brand}, 제품={product}")
        print("-" * 50)

def test_food_detection():
    """식품/비식품 판단 테스트"""
    test_texts = [
        "농심 신라면 칼로리 500kcal",  # 식품
        "삼성 갤럭시 S24 128GB",  # 비식품
        "영양성분: 탄수화물 20g, 단백질 5g",  # 식품
        "Python 프로그래밍 입문서",  # 비식품
        "유통기한 2024.12.31까지",  # 식품
    ]
    
    print("🧪 식품/비식품 판단 테스트")
    for text in test_texts:
        is_food = check_if_food_product(text)
        print(f"텍스트: {text}")
        print(f"판단 결과: {'식품' if is_food else '비식품'}")
        print("-" * 50)

def test_food_name_validation():
    """식품명 검증 테스트"""
    test_cases = [
        # (테스트 이름, 예상 결과)
        ("농심 신라면", True),
        ("123RF", False),
        ("SHUTTERSTOCK", False),
        ("삼성 갤럭시", False),
        ("오뚜기 진라면", True),
        ("APPLE IPHONE", False),
        ("롯데 초코파이", True),
        ("NIKE 운동화", False),
        ("ABC123", False),  # 제품코드 패턴
        ("바나나우유", True),
        ("전자기기", False),
        ("새우깡", True),
    ]
    
    print("🧪 식품명 검증 테스트")
    for food_name, expected in test_cases:
        result = is_valid_food_name(food_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{food_name}' -> {'식품' if result else '비식품'} (예상: {'식품' if expected else '비식품'})")
    print("-" * 50)

def test_gemini_setup():
    """Gemini 설정 테스트"""
    print("🧪 Gemini 설정 테스트")
    print(f"   GEMINI_API_KEY: {bool(GEMINI_API_KEY)}")
    
    if GEMINI_API_KEY:
        print("✅ Gemini 설정이 완료되었습니다")
        return True
    else:
        print("❌ Gemini 설정이 누락되었습니다")
        print("   .env 파일에 다음을 추가하세요:")
        print("   GEMINI_API_KEY=your_api_key")
        return False

if __name__ == "__main__":
    print("🧪 Gemini 모듈 테스트")
    
    # 설정 테스트
    test_gemini_setup()
    
    # 브랜드 탐지 테스트
    test_brand_detection()
    
    # 식품/비식품 판단 테스트  
    test_food_detection()
    
    # 식품명 검증 테스트
    test_food_name_validation()