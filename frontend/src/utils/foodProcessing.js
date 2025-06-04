export const processOCRResults = (text) => {
  // 기존 OCR 처리 로직을 여기로 이동
  const ingredients = [];
  const lines = text.split('\n').filter(line => line.trim());
  
  // 스마트 분석 및 식재료 추출 로직
  // ...
  
  return ingredients;
};

export const performSmartAnalysis = (text) => {
  // 기존 스마트 분석 로직을 여기로 이동
  const results = [];
  
  // 한국어 특화 분석 규칙들
  // ...
  
  return results;
};

export const translateToKoreanFallback = (englishName) => {
  const basicTranslations = {
    'apple': '사과',
    'banana': '바나나', 
    'carrot': '당근',
    // ... 기존 번역 테이블
  };
  
  return basicTranslations[englishName.toLowerCase()] || englishName;
};