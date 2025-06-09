// utils/foodProcessing.js

// 식재료 관련 영어 단어들 (detection 결과 번역용)
export const FOOD_INGREDIENTS = {
  'apple': '사과',
  'banana': '바나나', 
  'carrot': '당근',
  'tomato': '토마토',
  'orange': '오렌지',
  'onion': '양파',
  'potato': '감자',
  'cucumber': '오이',
  'lettuce': '상추',
  'broccoli': '브로콜리',
  'cabbage': '양배추',
  'eggs': '계란',
  'egg': '계란',
  'milk': '우유',
  'bread': '빵',
  'rice': '쌀',
  'chicken': '닭고기',
  'beef': '소고기',
  'pork': '돼지고기',
  'fish': '생선',
  'blueberry': '블루베리',
  'strawberry': '딸기',
  'eggplant': '가지',
  'zucchini': '호박',
  'bell pepper': '피망',
  'cauliflower': '콜리플라워',
  'spinach': '시금치',
  'shrimp': '새우',
  'corn': '옥수수',
  'cheese': '치즈',
  'yogurt': '요거트',
  'butter': '버터',
  'flour': '밀가루',
  'sugar': '설탕',
  'salt': '소금',
  'mushroom': '버섯',
  'garlic': '마늘',
  'ginger': '생강',
  'lemon': '레몬',
  'lime': '라임',
  'grape': '포도',
  'watermelon': '수박',
  'pineapple': '파인애플',
  'avocado': '아보카도',
  'radish': '무',
  'pepper': '고추',
  'bean': '콩',
  'celery': '셀러리',
  'asparagus': '아스파라거스',
  'kale': '케일',
  'sweet potato': '고구마',
  'bell_pepper': '피망',
  'pumpkin': '호박'
};

// Gemini 결과에서 식품명 추출
export const extractFoodNameFromGeminiResult = (resultText, originalText, performAdvancedFallback) => {
  if (!resultText) {
    // Gemini 결과가 없으면 fallback 사용
    return performAdvancedFallback(originalText);
  }
  
  try {
    // 줄 단위로 분리
    const lines = resultText.trim().split('\n');
    
    // 첫 번째 줄에서 식품명 추출
    let firstLine = lines[0].trim();
    
    // 불필요한 접두사 제거
    const prefixesToRemove = [
      "추론된 식품:", "식품명:", "제품명:", "상품명:", "식재료:",
      "분석 결과:", "결과:", "답변:", "식품:",
      "추론 결과:", "판단 결과:", "**", "*"
    ];
    
    for (const prefix of prefixesToRemove) {
      if (firstLine.startsWith(prefix)) {
        firstLine = firstLine.substring(prefix.length).trim();
      }
    }
    
    // 마크다운 굵은 글씨 제거
    firstLine = firstLine.replace(/\*\*/g, '').replace(/\*/g, '');
    
    // 괄호 안의 부가 설명 제거 (단, 중요한 정보는 보존)
    if (firstLine.includes('(') && firstLine.includes(')')) {
      // "매일두유(99.9%)" 같은 경우는 보존
      if (!firstLine.match(/\([0-9.%]+\)/)) {
        firstLine = firstLine.split('(')[0].trim();
      }
    }
    
    return firstLine || performAdvancedFallback(originalText);
    
  } catch (error) {
    console.error('❌ Gemini 결과 추출 중 오류:', error);
    return performAdvancedFallback(originalText);
  }
};

// 간단한 텍스트 추론 함수
export const performSimpleTextInference = (text, classifyByIngredientsOnly) => {
  if (!text) return null;
  
  const cleanText = text.replace(/[^\w\s가-힣]/g, ' ').replace(/\s+/g, ' ').trim();
  
  // 먼저 식재료명 기반 분류 시도
  const ingredientResult = classifyByIngredientsOnly(text);
  if (ingredientResult.found_ingredients.length > 0) {
    return ingredientResult.found_ingredients[0].name;
  }
  
  // 일반적인 식품 키워드 탐지 (fallback)
  const foodKeywords = {
    '라면': ['라면', '면', 'RAMEN', 'NOODLE'],
    '우유': ['우유', 'MILK', '밀크'],
    '초콜릿': ['초콜릿', 'CHOCOLATE', '쇼콜라'],
    '과자': ['과자', 'SNACK', '스낵'],
    '음료': ['음료', 'DRINK', '드링크', '사이다', '콜라'],
    '빵': ['빵', 'BREAD', '브레드'],
    '치킨': ['치킨', 'CHICKEN', '닭'],
    '햄버거': ['햄버거', 'BURGER', '버거']
  };
  
  const upperText = cleanText.toUpperCase();
  
  for (const [category, keywords] of Object.entries(foodKeywords)) {
    for (const keyword of keywords) {
      if (cleanText.includes(keyword) || upperText.includes(keyword.toUpperCase())) {
        console.log(`🔍 키워드 매칭: "${keyword}" → "${category}"`);
        return category;
      }
    }
  }
  
  // 키워드 매칭 실패 시 첫 번째 한글 단어 반환
  const koreanWords = cleanText.match(/[가-힣]+/g);
  if (koreanWords && koreanWords.length > 0) {
    const firstKoreanWord = koreanWords[0];
    console.log(`🔍 첫 번째 한글 단어 사용: "${firstKoreanWord}"`);
    return firstKoreanWord;
  }
  
  return '식품';
};

// 숫자 포함 의미있는 텍스트 추출 (예: "매일두유99.9%")
export const extractMeaningfulTextWithNumbers = (text) => {
  // 한글+숫자+% 조합 찾기
  const patterns = [
    /[가-힣]+\d+\.?\d*%/g,  // "매일두유99.9%"
    /[가-힣]+\d+\.?\d*[가-힣]*/g,  // "매일두유1000ml"
    /[가-힣]+\s*\d+\.?\d*/g  // "매일두유 99.9"
  ];
  
  for (const pattern of patterns) {
    const matches = text.match(pattern);
    if (matches && matches.length > 0) {
      // 가장 긴 매치 반환
      const longestMatch = matches.reduce((a, b) => a.length > b.length ? a : b);
      if (longestMatch.length >= 4) {  // 최소 길이 체크
        return longestMatch;
      }
    }
  }
  
  return null;
};

// 기본 식재료 사전 확인 (fallback)
export const checkBasicFoodDictionary = (englishName) => {
  const lowerName = englishName.toLowerCase();
  
  // 명확한 비식재료는 제외
  const nonFoodItems = ['person', 'hand', 'human', 'bottle', 'package', 'container', 'box', 'bag', 'plate', 'bowl', 'cup', 'glass', 'knife', 'fork', 'spoon', 'table', 'chair', 'wall', 'floor', 'ceiling', 'window', 'door', 'plastic', 'metal', 'wood', 'paper', 'cloth', 'fabric'];
  
  for (const nonFood of nonFoodItems) {
    if (lowerName.includes(nonFood)) {
      return null;
    }
  }
  
  // 기본 식재료 사전에서 확인
  const basicTranslation = FOOD_INGREDIENTS[lowerName];
  if (basicTranslation) {
    return basicTranslation;
  }
  
  // 부분 매칭
  for (const [englishKey, koreanValue] of Object.entries(FOOD_INGREDIENTS)) {
    if (lowerName.includes(englishKey) || englishKey.includes(lowerName)) {
      return koreanValue;
    }
  }
  
  // 기본 사전에 없으면 원본 반환 (식재료일 가능성을 위해)
  return englishName;
};