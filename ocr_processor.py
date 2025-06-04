# 📁 cv-service/modules/ocr_processor.py - 팀원 최신 + 고도화 기능 완전 통합
import requests
import json
import traceback
import os
import re
from typing import List, Dict, Optional

CLOVA_OCR_API_URL = os.environ.get("CLOVA_OCR_API_URL")
CLOVA_SECRET_KEY = os.environ.get("CLOVA_SECRET_KEY")

# ===== 팀원의 기본 브랜드 매핑 데이터 (완전 유지) =====
BRAND_MAPPINGS = {
    "커피": {
        "brands": [
            "메가커피", "MEGA", "MGC", "mega coffee",
            "컴포즈", "COMPOSE", "compose coffee",
            "스타벅스", "STARBUCKS", "starbucks",
            "투썸", "TWOSOME", "twosome place",
            "이디야", "EDIYA", "ediya coffee",
            "폴바셋", "PAUL BASSETT", "paul bassett",
            "할리스", "HOLLYS", "hollys coffee",
            "빽다방", "PAIK", "paiks coffee"
        ],
        "default_product": "커피",
        "common_products": [
            "아메리카노", "카페라떼", "카푸치노", "에스프레소", 
            "카페모카", "마키아토", "콜드브루", "바닐라라떼"
        ],
        "unit_size": 200  # ml 기준
    },
    "과자": {
        "brands": [
            "오리온", "ORION", "농심", "NONGSHIM", "롯데", "LOTTE",
            "해태", "HAITAI", "크라운", "CROWN"
        ],
        "default_product": "과자",
        "common_products": [
            "초코파이", "새우깡", "허니버터칩", "포카칩", "프링글스",
            "오감자", "꼬북칩", "치토스"
        ],
        "unit_size": 100  # g 기준
    },
    "음료": {
        "brands": [
            "코카콜라", "COCA COLA", "COKE", "펩시", "PEPSI",
            "칠성사이다", "CHILSUNG", "환타", "FANTA", "스프라이트", "SPRITE"
        ],
        "default_product": "음료",
        "common_products": [
            "콜라", "사이다", "환타", "스프라이트"
        ],
        "unit_size": 250  # ml 기준
    },
    "우유": {
        "brands": [
            "서울우유", "SEOUL MILK", "매일유업", "MAEIL", "남양", "NAMYANG",
            "덴마크", "DENMARK", "상하목장", "SANGHA"
        ],
        "default_product": "우유",
        "common_products": [
            "흰우유", "초콜릿우유", "딸기우유", "바나나우유", "두유"
        ],
        "unit_size": 200  # ml 기준
    }
}

# ===== 🆕 확장된 브랜드 매핑 데이터 (고도화 기능) =====
EXTENDED_BRAND_MAPPINGS = {
    "아이스크림": {
        "brands": [
            "하겐다즈", "HAAGEN DAZS", "베스킨라빈스", "BASKIN ROBBINS",
            "빙그레", "BINGGRAE", "롯데", "LOTTE", "나뚜루", "NATUUR",
            "설레임", "SEOLLEIM", "팥빙수", "빙그레우유"
        ],
        "default_product": "아이스크림",
        "common_products": [
            "바닐라", "초콜릿", "딸기", "민트초코", "쿠키앤크림",
            "메로나", "부라보콘", "끌레도르", "투게더"
        ],
        "unit_size": 150
    },
    "라면": {
        "brands": [
            "농심", "NONGSHIM", "오뚜기", "OTTOGI", "팔도", "PALDO",
            "삼양", "SAMYANG", "진라면", "신라면", "짜파게티"
        ],
        "default_product": "라면",
        "common_products": [
            "신라면", "진라면", "너구리", "짜파게티", "불닭볶음면",
            "진짬뽕", "육개장", "김치라면"
        ],
        "unit_size": 120
    },
    "요구르트": {
        "brands": [
            "야쿠르트", "YAKULT", "빙그레", "BINGGRAE", "매일", "MAEIL",
            "남양", "NAMYANG", "덴마크", "DENMARK"
        ],
        "default_product": "요구르트",
        "common_products": [
            "플레인요구르트", "딸기요구르트", "블루베리요구르트", 
            "바나나우유", "초콜릿우유", "그릭요거트"
        ],
        "unit_size": 150
    },
    "빵": {
        "brands": [
            "파리바게뜨", "PARIS BAGUETTE", "뚜레쥬르", "TOUS LES JOURS",
            "삼립", "SAMLIP", "SPC", "크라운", "CROWN", "오뚜기", "OTTOGI"
        ],
        "default_product": "빵",
        "common_products": [
            "식빵", "크로와상", "단팥빵", "크림빵", "소보로빵",
            "초코파이", "찹쌀떡", "카스테라"
        ],
        "unit_size": 100
    }
}

# 전체 브랜드 매핑 통합
ALL_BRAND_MAPPINGS = {**BRAND_MAPPINGS, **EXTENDED_BRAND_MAPPINGS}

# ===== 🆕 스마트 패턴 분석 데이터 =====
SMART_PATTERNS = {
    "milk_variations": {
        "patterns": [
            r"아몬드\s*우유", r"알몬드\s*우유", r"ALMOND\s*MILK",
            r"오트\s*우유", r"OAT\s*MILK", r"귀리\s*우유",
            r"코코넛\s*우유", r"COCONUT\s*MILK",
            r"두유", r"SOY\s*MILK", r"콩\s*우유"
        ],
        "category": "식물성우유",
        "default_name": "식물성우유",
        "confidence": 0.85
    },
    "juice_variations": {
        "patterns": [
            r"오렌지\s*주스", r"ORANGE\s*JUICE",
            r"사과\s*주스", r"APPLE\s*JUICE", 
            r"포도\s*주스", r"GRAPE\s*JUICE",
            r"토마토\s*주스", r"TOMATO\s*JUICE",
            r"당근\s*주스", r"CARROT\s*JUICE"
        ],
        "category": "과일주스",
        "default_name": "과일주스",
        "confidence": 0.9
    },
    "protein_products": {
        "patterns": [
            r"프로틴\s*바", r"PROTEIN\s*BAR",
            r"프로틴\s*쉐이크", r"PROTEIN\s*SHAKE",
            r"단백질\s*음료", r"WPI", r"WPC"
        ],
        "category": "단백질보충제",
        "default_name": "단백질보충제",
        "confidence": 0.8
    },
    "health_drinks": {
        "patterns": [
            r"비타민\s*음료", r"VITAMIN\s*DRINK",
            r"이온\s*음료", r"ION\s*DRINK", r"스포츠\s*음료",
            r"에너지\s*드링크", r"ENERGY\s*DRINK"
        ],
        "category": "기능성음료",
        "default_name": "기능성음료",
        "confidence": 0.75
    }
}

def extract_text_with_ocr(image_path):
    """원본 OCR 함수 (팀원 코드 100% 유지)"""
    try:
        print(f"OCR 시작: {image_path}")
        print(f"API URL: {CLOVA_OCR_API_URL}")
        print(f"Secret Key 존재: {bool(CLOVA_SECRET_KEY)}")
        
        request_json = {
            'images': [
                {
                    'format': 'jpg',
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
            ('file', ('food.jpg', file_data, 'image/jpeg'))
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

# ===== 팀원의 브랜드 매핑 기능 (100% 유지) =====

def analyze_brands_in_text(text: str) -> List[Dict]:
    """OCR 텍스트에서 브랜드 기반 제품 추론 (팀원 코드 유지)"""
    if not text or not text.strip():
        return []
    
    print(f"🏷️ 브랜드 분석 시작: {text}")
    
    results = []
    text_lower = text.lower()
    
    # 각 카테고리별 브랜드 검색 (팀원 방식)
    for category, mapping in BRAND_MAPPINGS.items():
        for brand in mapping["brands"]:
            if brand.lower() in text_lower:
                print(f"✅ 브랜드 발견: {brand} → {category}")
                
                # 구체적인 제품명 찾기
                specific_product = None
                for product in mapping["common_products"]:
                    if product.lower() in text_lower:
                        specific_product = product
                        break
                
                # 수량 추론
                quantity = estimate_quantity_from_text(text, mapping["unit_size"])
                
                result = {
                    "name": specific_product or mapping["default_product"],
                    "quantity": quantity,
                    "category": category,
                    "confidence": 0.9 if specific_product else 0.8,
                    "source": "brand_ocr",
                    "detected_brand": brand,
                    "original_text": text
                }
                
                results.append(result)
                break  # 카테고리당 하나의 브랜드만
    
    print(f"🏷️ 브랜드 분석 완료: {len(results)}개 제품")
    return results

def estimate_quantity_from_text(text: str, unit_size: int = 200) -> int:
    """텍스트에서 용량 기반 수량 추론 (팀원 코드 유지)"""
    # 직접적인 개수 표현
    count_match = re.search(r'(\d+)\s*개', text)
    if count_match:
        return int(count_match.group(1))
    
    # 용량 기반 추론
    volume_patterns = [
        r'(\d+)\s*ml', r'(\d+)\s*ML', r'(\d+)\s*mL',
        r'(\d+)\s*L', r'(\d+)\s*리터',
        r'(\d+)\s*g', r'(\d+)\s*G', r'(\d+)\s*그램'
    ]
    
    for pattern in volume_patterns:
        match = re.search(pattern, text)
        if match:
            volume = int(match.group(1))
            # 기본 단위로 나누어 개수 계산
            return max(1, volume // unit_size)
    
    return 1

# ===== 🆕 고도화된 OCR 분석 기능들 =====

def analyze_extended_brands_in_text(text: str) -> List[Dict]:
    """🆕 확장된 브랜드 매핑 분석 (아이스크림, 라면, 요구르트, 빵 포함)"""
    if not text or not text.strip():
        return []
    
    print(f"🏷️ 확장 브랜드 분석 시작: {text}")
    
    results = []
    text_lower = text.lower()
    
    # 확장된 브랜드 매핑 검색
    for category, mapping in EXTENDED_BRAND_MAPPINGS.items():
        for brand in mapping["brands"]:
            if brand.lower() in text_lower:
                print(f"✅ 확장 브랜드 발견: {brand} → {category}")
                
                # 구체적인 제품명 찾기
                specific_product = None
                for product in mapping["common_products"]:
                    if product.lower() in text_lower:
                        specific_product = product
                        break
                
                # 수량 추론
                quantity = estimate_quantity_from_text(text, mapping["unit_size"])
                
                result = {
                    "name": specific_product or mapping["default_product"],
                    "quantity": quantity,
                    "category": category,
                    "confidence": 0.85 if specific_product else 0.75,
                    "source": "extended_brand_ocr",
                    "detected_brand": brand,
                    "original_text": text
                }
                
                results.append(result)
                break
    
    print(f"🏷️ 확장 브랜드 분석 완료: {len(results)}개 제품")
    return results

def analyze_smart_patterns(text: str) -> List[Dict]:
    """🆕 스마트 패턴 분석 (특수 제품명 인식)"""
    if not text or not text.strip():
        return []
    
    print(f"🧠 스마트 패턴 분석 시작: {text}")
    
    results = []
    
    for pattern_name, pattern_info in SMART_PATTERNS.items():
        for pattern in pattern_info["patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                matched_text = match.group(0)
                print(f"✅ 패턴 매칭: {matched_text} → {pattern_info['category']}")
                
                # 더 구체적인 제품명 추출 시도
                specific_name = extract_specific_product_name(matched_text, pattern_info)
                
                # 수량 추론
                quantity = estimate_quantity_from_context(text, match.start(), match.end())
                
                result = {
                    "name": specific_name,
                    "quantity": quantity,
                    "category": pattern_info["category"],
                    "confidence": pattern_info["confidence"],
                    "source": "smart_pattern",
                    "matched_pattern": pattern,
                    "matched_text": matched_text,
                    "original_text": text
                }
                
                results.append(result)
    
    print(f"🧠 스마트 패턴 분석 완료: {len(results)}개 제품")
    return results

def extract_specific_product_name(matched_text: str, pattern_info: Dict) -> str:
    """🆕 매칭된 텍스트에서 구체적인 제품명 추출"""
    # 기본적으로 매칭된 텍스트를 정리해서 반환
    cleaned_name = re.sub(r'\s+', ' ', matched_text).strip()
    
    # 카테고리별 특별 처리
    category = pattern_info["category"]
    
    if category == "식물성우유":
        if "아몬드" in cleaned_name or "알몬드" in cleaned_name:
            return "아몬드우유"
        elif "오트" in cleaned_name or "귀리" in cleaned_name:
            return "오트우유"
        elif "코코넛" in cleaned_name:
            return "코코넛우유"
        elif "두유" in cleaned_name or "콩" in cleaned_name:
            return "두유"
    
    elif category == "과일주스":
        if "오렌지" in cleaned_name:
            return "오렌지주스"
        elif "사과" in cleaned_name:
            return "사과주스"
        elif "포도" in cleaned_name:
            return "포도주스"
        elif "토마토" in cleaned_name:
            return "토마토주스"
        elif "당근" in cleaned_name:
            return "당근주스"
    
    # 기본값 반환
    return cleaned_name if cleaned_name else pattern_info["default_name"]

def estimate_quantity_from_context(text: str, start_pos: int, end_pos: int) -> int:
    """🆕 매칭 위치 주변 컨텍스트에서 수량 추론"""
    # 매칭된 부분 앞뒤 50자 정도의 컨텍스트 추출
    context_start = max(0, start_pos - 50)
    context_end = min(len(text), end_pos + 50)
    context = text[context_start:context_end]
    
    # 개수 패턴 검색
    quantity_patterns = [
        r'(\d+)\s*개',
        r'(\d+)\s*병',
        r'(\d+)\s*캔',
        r'(\d+)\s*팩',
        r'(\d+)\s*box',
        r'(\d+)\s*BOX'
    ]
    
    for pattern in quantity_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # 용량에서 수량 추론
    volume_match = re.search(r'(\d+)\s*(ml|ML|mL|L|리터|g|G|그램)', context)
    if volume_match:
        volume = int(volume_match.group(1))
        unit = volume_match.group(2).lower()
        
        # 단위에 따른 기본 수량 계산
        if unit in ['l', '리터']:
            return max(1, volume)  # 리터는 그대로
        elif unit in ['ml', 'ml']:
            return max(1, volume // 250)  # 250ml 기준
        elif unit in ['g', '그램']:
            return max(1, volume // 100)  # 100g 기준
    
    return 1

def preprocess_ocr_text(text: str) -> str:
    """🆕 OCR 텍스트 전처리 및 정규화"""
    if not text:
        return ""
    
    # 1. 기본 정리
    text = text.strip()
    
    # 2. 다중 공백을 단일 공백으로
    text = re.sub(r'\s+', ' ', text)
    
    # 3. 특수문자 정리 (필요한 것만 유지)
    text = re.sub(r'[^\w\s가-힣.,()%-]', ' ', text)
    
    # 4. 숫자와 단위 사이 공백 정규화
    text = re.sub(r'(\d+)\s*(ml|ML|mL|L|리터|g|G|그램|개|병|캔)', r'\1\2', text)
    
    # 5. 브랜드명 정규화
    brand_normalizations = {
        'COCACOLA': 'COCA COLA',
        'STARBUCKS': 'STARBUCKS',
        'BASKINROBBINS': 'BASKIN ROBBINS'
    }
    
    for original, normalized in brand_normalizations.items():
        text = text.replace(original, normalized)
    
    return text.strip()

def smart_ocr_analysis(text: str) -> Dict:
    """🆕 종합 스마트 OCR 분석 - 모든 기능 통합"""
    if not text or not text.strip():
        return {
            "success": False,
            "error": "분석할 텍스트가 없습니다",
            "products": [],
            "total_found": 0
        }
    
    print(f"🧠 종합 스마트 OCR 분석 시작")
    print(f"📝 원본 텍스트: {text[:100]}...")
    
    # 1. 텍스트 전처리
    processed_text = preprocess_ocr_text(text)
    print(f"🔧 전처리된 텍스트: {processed_text[:100]}...")
    
    all_products = []
    
    # 2. 기본 브랜드 매핑 (팀원 코드)
    basic_brands = analyze_brands_in_text(processed_text)
    all_products.extend(basic_brands)
    print(f"🏷️ 기본 브랜드: {len(basic_brands)}개")
    
    # 3. 확장 브랜드 매핑
    extended_brands = analyze_extended_brands_in_text(processed_text)
    all_products.extend(extended_brands)
    print(f"🏷️ 확장 브랜드: {len(extended_brands)}개")
    
    # 4. 스마트 패턴 분석
    smart_patterns = analyze_smart_patterns(processed_text)
    all_products.extend(smart_patterns)
    print(f"🧠 스마트 패턴: {len(smart_patterns)}개")
    
    # 5. 중복 제거 및 신뢰도 기준 정렬
    unique_products = remove_duplicate_products(all_products)
    unique_products.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    # 6. 결과 구성
    result = {
        "success": True,
        "products": unique_products,
        "total_found": len(unique_products),
        "analysis_methods": {
            "basic_brands": len(basic_brands),
            "extended_brands": len(extended_brands),
            "smart_patterns": len(smart_patterns),
            "duplicates_removed": len(all_products) - len(unique_products)
        },
        "original_text": text,
        "processed_text": processed_text
    }
    
    print(f"✅ 종합 분석 완료: {len(unique_products)}개 고유 제품")
    
    return result

def remove_duplicate_products(products: List[Dict]) -> List[Dict]:
    """🆕 중복 제품 제거 (이름과 카테고리 기준)"""
    seen = set()
    unique_products = []
    
    for product in products:
        # 제품 식별 키 생성 (이름 + 카테고리)
        key = (
            product.get("name", "").lower().strip(),
            product.get("category", "").lower().strip()
        )
        
        if key not in seen and key[0]:  # 이름이 있는 경우만
            seen.add(key)
            unique_products.append(product)
    
    return unique_products

def extract_nutritional_info(text: str) -> Dict:
    """🆕 영양성분 정보 추출 (실험적 기능)"""
    nutritional_patterns = {
        "칼로리": [r'(\d+)\s*(kcal|칼로리|cal)', r'에너지\s*(\d+)'],
        "단백질": [r'단백질\s*(\d+(?:\.\d+)?)\s*g', r'protein\s*(\d+(?:\.\d+)?)'],
        "지방": [r'지방\s*(\d+(?:\.\d+)?)\s*g', r'fat\s*(\d+(?:\.\d+)?)'],
        "탄수화물": [r'탄수화물\s*(\d+(?:\.\d+)?)\s*g', r'carb\s*(\d+(?:\.\d+)?)'],
        "당류": [r'당류\s*(\d+(?:\.\d+)?)\s*g', r'sugar\s*(\d+(?:\.\d+)?)'],
        "나트륨": [r'나트륨\s*(\d+(?:\.\d+)?)\s*(mg|밀리그램)', r'sodium\s*(\d+(?:\.\d+)?)']
    }
    
    nutrition_info = {}
    
    for nutrient, patterns in nutritional_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    nutrition_info[nutrient] = value
                    break
                except (ValueError, IndexError):
                    continue
    
    return nutrition_info

# ===== 🆕 테스트 함수들 =====

def test_brand_analysis():
    """🆕 브랜드 분석 테스트 (팀원 코드 + 확장)"""
    test_texts = [
        # 팀원 기존 테스트
        "메가커피 아메리카노 500ml",
        "오리온 초코파이 12개입",
        "코카콜라 COCA COLA 250ml",
        "서울우유 흰우유 1000ml",
        "스타벅스 카페라떼 그란데",
        
        # 🆕 확장 테스트
        "하겐다즈 바닐라 아이스크림 473ml",
        "농심 신라면 5개입",
        "야쿠르트 플레인요구르트 4개입",
        "파리바게뜨 크로와상 2개",
        "아몬드 우유 1L",
        "오렌지 주스 500ml"
    ]
    
    print("🧪 통합 브랜드 분석 테스트 시작")
    print("=" * 60)
    
    for text in test_texts:
        print(f"\n테스트: {text}")
        
        # 기본 브랜드 분석 (팀원)
        basic_results = analyze_brands_in_text(text)
        
        # 확장 브랜드 분석
        extended_results = analyze_extended_brands_in_text(text)
        
        # 스마트 패턴 분석
        smart_results = analyze_smart_patterns(text)
        
        # 종합 분석
        comprehensive_results = smart_ocr_analysis(text)
        
        all_results = basic_results + extended_results + smart_results
        
        if all_results:
            for result in all_results:
                print(f"  → {result['name']} {result['quantity']}개 ({result['category']}) [{result['confidence']:.1f}] 출처: {result['source']}")
        else:
            print("  → 브랜드/패턴 인식 안됨")
        
        print(f"  📊 종합 분석 결과: {comprehensive_results['total_found']}개 고유 제품")

def test_smart_pattern_analysis():
    """🆕 스마트 패턴 분석 전용 테스트"""
    test_texts = [
        "아몬드 우유 1L 오가닉",
        "오렌지 주스 100% 500ml",
        "프로틴 바 초콜릿맛",
        "비타민 음료 멀티비타민",
        "이온 음료 포카리스웨트"
    ]
    
    print("🧪 스마트 패턴 분석 테스트")
    print("=" * 50)
    
    for text in test_texts:
        print(f"\n테스트: {text}")
        results = analyze_smart_patterns(text)
        
        if results:
            for result in results:
                print(f"  → {result['name']} ({result['category']}) [{result['confidence']:.1f}]")
                print(f"    매칭 패턴: {result['matched_pattern']}")
                print(f"    매칭 텍스트: {result['matched_text']}")
        else:
            print("  → 패턴 매칭 안됨")

if __name__ == "__main__":
    print("🧪 통합 OCR 프로세서 모듈 테스트")
    print("=" * 60)
    print("📋 테스트 내용:")
    print("  🔵 팀원 기존 기능 (100% 유지):")
    print("    - 기본 CLOVA OCR 연동")
    print("    - 기본 브랜드 매핑 (커피, 과자, 음료, 우유)")
    print("    - 용량 기반 수량 추론")
    print("  🟠 고도화 기능 (추가):")
    print("    - 확장 브랜드 매핑 (아이스크림, 라면, 요구르트, 빵)")
    print("    - 스마트 패턴 분석 (식물성우유, 과일주스 등)")
    print("    - 텍스트 전처리 및 정규화")
    print("    - 종합 OCR 분석")
    print("    - 중복 제거 시스템")
    print("=" * 60)
    
    # 팀원 기존 테스트 실행
    print("\n🔵 팀원 기존 브랜드 분석 테스트:")
    test_brand_analysis()
    
    # 고도화 기능 테스트 실행
    print("\n🟠 고도화 스마트 패턴 분석 테스트:")
    test_smart_pattern_analysis()
    
    print("\n✅ 통합 OCR 모듈 테스트 완료")
    print("📝 팀원 기존 코드와 100% 호환됩니다")