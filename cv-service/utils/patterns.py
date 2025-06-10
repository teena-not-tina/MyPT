# utils/patterns.py - 패턴 매칭 관련 함수들

import re
from typing import List, Optional, Dict

# 패턴 데이터
INGREDIENT_PATTERNS = [
    {
        "keywords": ["오렌지농축과즙", "오렌지과즙", "오렌지농축"],
        "volume": "ml",
        "result": "오렌지주스",
        "confidence": 0.95
    },
    {
        "keywords": ["아몬드추출액", "아몬드우유", "아몬드밀크"],
        "volume": "ml",
        "result": "아몬드밀크",
        "confidence": 0.95
    },
    {
        "keywords": ["원액두유", "분리대두단백", "대두농축액"],
        "volume": "ml",
        "result": "두유",
        "confidence": 0.95
    },
    {
        "keywords": ["우유", "전유", "저지방우유"],
        "volume": "ml",
        "result": "우유",
        "confidence": 0.98
    },
    {
        "keywords": ["사과과즙", "사과농축과즙"],
        "volume": "ml",
        "result": "사과주스",
        "confidence": 0.95
    },
    {
        "keywords": ["포도과즙", "포도농축과즙"],
        "volume": "ml",
        "result": "포도주스",
        "confidence": 0.95
    },
    {
        "keywords": ["토마토과즙", "토마토농축액"],
        "volume": "ml",
        "result": "토마토주스",
        "confidence": 0.95
    },
    {
        "keywords": ["백오이", "백색오이"],
        "result": "오이",
        "confidence": 0.90
    },
    {
        "keywords": ["무우", "무"],
        "result": "무",
        "confidence": 0.95
    },
    {
        "keywords": ["당근", "홍당무"],
        "result": "당근",
        "confidence": 0.95
    },
    {
        "keywords": ["양배추", "캐비지"],
        "result": "양배추",
        "confidence": 0.90
    },
    {
        "keywords": ["상추", "청상추"],
        "result": "상추",
        "confidence": 0.90
    },
    {
        "keywords": ["배추", "백배추", "절임배추"],
        "result": "배추",
        "confidence": 0.95
    },
    {
        "keywords": ["사과", "홍옥사과", "부사"],
        "result": "사과",
        "confidence": 0.95
    },
    {
        "keywords": ["배", "신고배"],
        "result": "배",
        "confidence": 0.95
    },
    {
        "keywords": ["바나나"],
        "result": "바나나",
        "confidence": 0.98
    },
    {
        "keywords": ["오렌지", "네이블오렌지"],
        "result": "오렌지",
        "confidence": 0.95
    },
    {
        "keywords": ["삼겹살", "돼지삼겹살"],
        "result": "삼겹살",
        "confidence": 0.95
    },
    {
        "keywords": ["닭가슴살", "닭고기"],
        "result": "닭가슴살",
        "confidence": 0.95
    },
    {
        "keywords": ["쇠고기", "한우"],
        "result": "쇠고기",
        "confidence": 0.95
    },
    {
        "keywords": ["연어", "훈제연어"],
        "result": "연어",
        "confidence": 0.95
    },
    {
        "keywords": ["요구르트", "요거트", "플레인요구르트"],
        "result": "요구르트",
        "confidence": 0.95
    },
    {
        "keywords": ["치즈", "슬라이스치즈", "모짜렐라"],
        "result": "치즈",
        "confidence": 0.95
    },
    {
        "keywords": ["버터", "무염버터"],
        "result": "버터",
        "confidence": 0.95
    },
    {
        "keywords": ["쌀", "백미", "현미"],
        "result": "쌀",
        "confidence": 0.98
    },
    {
        "keywords": ["라면", "즉석라면"],
        "result": "라면",
        "confidence": 0.95
    },
    {
        "keywords": ["스파게티", "파스타"],
        "result": "파스타",
        "confidence": 0.95
    },
    {
        "keywords": ["간장", "양조간장"],
        "result": "간장",
        "confidence": 0.95
    },
    {
        "keywords": ["고추장", "태양초고추장"],
        "result": "고추장",
        "confidence": 0.95
    },
    {
        "keywords": ["마요네즈", "마요"],
        "result": "마요네즈",
        "confidence": 0.95
    },
    {
        "keywords": ["케첩", "토마토케첩"],
        "result": "케챱",
        "confidence": 0.95
    }
]

def extract_keywords_from_ocr(ocr_text: str) -> List[str]:
    """OCR 텍스트에서 키워드 추출"""
    if not ocr_text or not isinstance(ocr_text, str):
        return []
    
    clean_text = re.sub(r'\s+', '', ocr_text)
    clean_text = re.sub(r'[^\w가-힣]', '', clean_text)
    clean_text = clean_text.lower()
    
    keywords = []
    
    for i in range(2, 5):
        for j in range(len(clean_text) - i + 1):
            word = clean_text[j:j+i]
            if len(word) >= 2 and word not in keywords:
                keywords.append(word)
    
    return keywords[:10]

def infer_ingredient_from_patterns(ocr_text: str) -> Optional[Dict]:
    """패턴 기반 재료 추론"""
    if not ocr_text:
        return None
    
    normalized_text = ocr_text.lower().replace(' ', '')
    has_ml = 'ml' in normalized_text or '밀리리터' in normalized_text
    
    for pattern in INGREDIENT_PATTERNS:
        has_keyword = any(keyword.lower() in normalized_text for keyword in pattern["keywords"])
        
        if has_keyword:
            if pattern.get("volume") == "ml" and not has_ml:
                continue
            
            matched_keywords = [kw for kw in pattern["keywords"] if kw.lower() in normalized_text]
            
            return {
                "ingredient": pattern["result"],
                "confidence": pattern["confidence"],
                "matched_keywords": matched_keywords,
                "has_volume": has_ml,
                "source": "pattern_matching"
            }
    
    return None

def summarize_ocr_text(ocr_text: str) -> str:
    """OCR 텍스트 요약"""
    if not ocr_text:
        return ''
    
    keywords = extract_keywords_from_ocr(ocr_text)
    meaningful_keywords = [kw for kw in keywords if len(kw) >= 2][:3]
    
    return ' '.join(meaningful_keywords) if meaningful_keywords else ocr_text[:10]