 # utils/search.py - 검색 관련 함수들

import os
import requests
from typing import List, Dict, Optional
from .patterns import extract_keywords_from_ocr, infer_ingredient_from_patterns

async def perform_google_search(query: str) -> List[Dict]:
    """Google 검색 수행"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        
        if not api_key or not search_engine_id:
            print("Google API key or Search Engine ID not set")
            return generate_mock_search_results(query)
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": 10,
            "lr": "lang_ko",
            "safe": "medium"
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": "google_search"
                })
            
            return results
        else:
            print(f"Google search API error: {response.status_code}")
            return generate_mock_search_results(query)
            
    except Exception as e:
        print(f"Google search API call failed: {e}")
        return generate_mock_search_results(query)

def generate_mock_search_results(query: str) -> List[Dict]:
    """목 검색 결과 생성"""
    return [
        {
            "title": f"{query} - 네이버 백과사전",
            "snippet": f"{query}에 대한 상세한 정보와 영양성분을 확인하세요.",
            "url": "https://terms.naver.com",
            "source": "mock_search"
        },
        {
            "title": f"{query} 레시피 및 효능",
            "snippet": f"신선한 {query}의 선택법과 보관방법, 건강 효능을 소개합니다.",
            "url": "https://recipe.example.com",
            "source": "mock_search"
        },
        {
            "title": f"{query} 영양정보",
            "snippet": f"{query}의 칼로리, 단백질, 탄수화물 등 영양성분 정보입니다.",
            "url": "https://nutrition.example.com",
            "source": "mock_search"
        }
    ]

def extract_ingredients_from_search_results(search_results: List[Dict], original_keywords: List[str]) -> List[Dict]:
    """검색 결과에서 재료 추출"""
    common_ingredients = [
        '오이', '당근', '무', '배추', '상추', '양배추', '브로콜리', '시금치', '고구마', '감자',
        '양파', '마늘', '생강', '대파', '쪽파', '부추', '고추', '파프리카', '토마토', '가지',
        '사과', '배', '바나나', '오렌지', '포도', '딸기', '수박', '참외', '멜론', '복숭아',
        '자두', '키위', '망고', '파인애플', '레몬', '라임', '체리', '블루베리',
        '쇠고기', '돼지고기', '닭고기', '삼겹살', '닭가슴살', '갈비', '등심', '안심',
        '연어', '고등어', '참치', '명태', '조기', '갈치', '삼치', '새우', '오징어', '문어',
        '우유', '요구르트', '치즈', '버터', '크림', '아이스크림',
        '오렌지주스', '사과주스', '포도주스', '토마토주스', '두유', '아몬드밀크', '코코넛밀크',
        '쌀', '현미', '보리', '밀', '라면', '우동', '파스타', '스파게티', '국수',
        '간장', '고추장', '된장', '마요네즈', '케챱', '식초', '설탕', '소금', '후추',
        '달걀', '계란', '두부', '김치', '김', '미역', '다시마'
    ]
    
    results = []
    
    all_text = ' '.join([
        f"{result.get('title', '')} {result.get('snippet', '')}" 
        for result in search_results
    ]).lower()
    
    for ingredient in common_ingredients:
        if ingredient in all_text:
            match_score = calculate_match_score(ingredient, original_keywords)
            
            if match_score > 0.3:
                results.append({
                    "name": ingredient,
                    "confidence": min(0.95, 0.7 + match_score * 0.25),
                    "keywords": original_keywords,
                    "match_score": match_score
                })
    
    return sorted(results, key=lambda x: x["confidence"], reverse=True)

def calculate_match_score(ingredient: str, keywords: List[str]) -> float:
    """매칭 점수 계산"""
    if not keywords:
        return 0
    
    total_score = 0
    ingredient_chars = list(ingredient)
    
    for keyword in keywords:
        keyword_chars = list(keyword)
        match_count = sum(1 for char in keyword_chars if char in ingredient_chars)
        
        score = match_count / max(len(keyword_chars), len(ingredient_chars))
        total_score = max(total_score, score)
    
    return total_score

async def search_similar_ingredients(keywords: List[str], query: str) -> Optional[Dict]:
    """유사 재료 검색"""
    if not keywords:
        return None
    
    try:
        search_results = await perform_google_search(query)
        
        if not search_results:
            return None
        
        found_ingredients = extract_ingredients_from_search_results(search_results, keywords)
        
        if found_ingredients:
            return {
                "ingredient": found_ingredients[0]["name"],
                "confidence": found_ingredients[0]["confidence"],
                "matched_keywords": found_ingredients[0]["keywords"],
                "source": "web_search",
                "search_query": query,
                "total_results": len(search_results)
            }
    
    except Exception as e:
        print(f"Web search error: {e}")
    
    return None

async def enhanced_ocr_inference(ocr_text: str) -> Optional[Dict]:
    """향상된 OCR 추론"""
    if not ocr_text or not ocr_text.strip():
        return None
    
    print(f"Enhanced OCR inference started: \"{ocr_text}\"")
    
    pattern_result = infer_ingredient_from_patterns(ocr_text)
    if pattern_result and pattern_result["confidence"] >= 0.85:
        print(f"Pattern matching success: {pattern_result}")
        return pattern_result
    
    keywords = extract_keywords_from_ocr(ocr_text)
    print(f"Extracted keywords: {keywords}")
    
    if keywords:
        search_terms = ' '.join(keywords[:3])
        search_query = f"{search_terms} 식재료 음식 재료"
        
        web_search_result = await search_similar_ingredients(keywords, search_query)
        if web_search_result and web_search_result["confidence"] >= 0.7:
            print(f"Web search success: {web_search_result}")
            return web_search_result
    
    if pattern_result:
        print(f"Pattern matching (low confidence): {pattern_result}")
        return pattern_result
    
    print(f"OCR inference failed: \"{ocr_text}\"")
    return None