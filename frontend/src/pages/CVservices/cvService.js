// frontend/src/components/Diet/services/cvService.js
const API_BASE_URL = process.env.REACT_APP_CV_SERVICE_URL || 'http://localhost:8080';
const GEMINI_API_KEY = process.env.REACT_APP_GEMINI_API_KEY || 'AIzaSyBBHRss0KLaEeeAgggsVOIGQ_zhS5ssDGw';
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent';

export const cvService = {
  // 객체 탐지
  detectFood: async (file, confidence = 0.5) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('confidence', confidence);
    
    const response = await fetch(`${API_BASE_URL}/api/detect`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Detection failed: ${response.status}`);
    }
    return response.json();
  },

  // OCR 분석
  analyzeOCR: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/ocr`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`OCR failed: ${response.status}`);
    }
    return response.json();
  },

  // Gemini 분석 (4단계 추론 시스템 적용)
  analyzeWithGemini: async (text, detectionResults = null) => {
    if (!text || text.trim() === "") {
      console.log("분석할 텍스트가 없습니다.");
      return null;
    }
    
    try {
      console.log(`🚀 Gemini API 호출 진행`);
      
      // 탐지 결과가 있으면 컨텍스트에 포함
      let detectionContext = "";
      if (detectionResults && detectionResults.length > 0) {
        const detectedClasses = detectionResults.filter(det => det.class !== 'other').map(det => det.class);
        if (detectedClasses.length > 0) {
          detectionContext = `\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: ${detectedClasses.join(', ')}`;
        }
      }

      // 4단계 추론 시스템에 맞춘 프롬프트
      const prompt = `식품의 포장지를 OCR로 추출한 텍스트를 분석해서 어떤 식품인지 추론해주세요.

추출된 텍스트: ${text}${detectionContext}

분석 지침 (중요도 순):
1. **브랜드+제품명 조합을 최우선으로 추론하세요**
   - 예시: "매일 두유99.9%", "농심 신라면", "롯데 초코파이"
   - 숫자나 퍼센트가 포함되어도 브랜드+제품명으로 답변
   
2. **ml 단위가 있고 음료 관련이면 해당 음료명으로 답변**
   - 예시: "우유 1000ml" → "우유", "매일두유 500ml" → "매일두유"
   
3. **구체적인 식재료명을 우선시**
   - 예시: "당근", "사과", "계란", "쌀" 등
   
4. **숫자 포함 제품명도 그대로 사용**
   - 예시: "매일두유99.9%" → "매일두유99.9%"
   
5. **응답 형식:**
   - 첫 번째 줄에만 추론된 식품명을 명확하게 작성
   - 가능한 한 원본 텍스트의 제품명을 보존

텍스트에 브랜드명이나 구체적인 제품명이 있다면 반드시 그것을 포함하여 답변하세요.`;
      
      const requestData = {
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.05,
          maxOutputTokens: 150,
          topP: 0.7,
          topK: 20
        }
      };
      
      console.log("🚀 Gemini API 요청 전송 중...");
      
      const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });
      
      console.log(`📡 Gemini API 응답 상태 코드: ${response.status}`);
      
      if (response.status === 200) {
        const result = await response.json();
        if (result.candidates && result.candidates.length > 0) {
          if (result.candidates[0].content) {
            const content = result.candidates[0].content;
            if (content.parts && content.parts.length > 0) {
              const inferenceResult = content.parts[0].text;
              console.log(`🤖 Gemini API 추론 결과: ${inferenceResult}`);
              
              // 결과 후처리
              const foodName = extractFoodNameFromGeminiResult(inferenceResult, text);
              console.log(`🍽️ 3단계 완료 - 최종 추출된 식품명: ${foodName}`);
              
              return foodName;
            }
          }
        }
      } else if (response.status === 429) {
        console.log(`⚠️ Gemini API 할당량 초과 (429) - fallback 진행`);
        return performFallback(text);
      }
      
      console.log(`❌ Gemini API 오류 - 상태 코드: ${response.status}`);
      return performFallback(text);
      
    } catch (error) {
      console.error(`❌ Gemini API 분석 중 오류 발생: ${error}`);
      return performFallback(text);
    }
  },

  // Detection 결과 번역 (Gemini 활용)
  translateDetectionResult: async (englishName) => {
    try {
      console.log(`🔄 Detection 번역 시작: "${englishName}"`);
      
      const prompt = `다음 영어 단어가 식재료/음식인지 판별하고, 맞다면 한국어로 번역해주세요.

영어 단어: "${englishName}"

🎯 판별 및 번역 규칙:
1. 식재료/음식이 맞는지 먼저 판별
2. 식재료/음식이면 정확한 한국어명으로 번역
3. 식재료/음식이 아니면 "NOT_FOOD" 반환

❌ 식재료/음식이 아닌 것들:
- 사람, 손, 몸의 일부 (person, hand, human)
- 포장재, 용기 (bottle, package, container, box, bag)
- 식기류 (plate, bowl, cup, glass, knife, fork, spoon)
- 가구, 건물 구조 (table, chair, wall, floor, window, door)
- 재질명 (plastic, metal, wood, paper, cloth, fabric)

✅ 식재료/음식인 것들:
- 과일, 채소, 육류, 생선, 유제품, 곡물 등

응답 형식:
- 식재료/음식인 경우: 한국어명만 (예: "사과", "당근", "닭고기")
- 식재료/음식이 아닌 경우: "NOT_FOOD"

응답:`;

      const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: prompt
            }]
          }],
          generationConfig: {
            temperature: 0.05,
            topK: 20,
            topP: 0.7,
            maxOutputTokens: 50,
          }
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const result = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim() || '';
        
        console.log(`🤖 Detection 번역 결과: "${result}"`);
        
        const cleanResult = result.replace(/[^\가-힣a-zA-Z_]/g, '').trim();
        
        if (cleanResult === 'NOT_FOOD' || cleanResult === 'NOTFOOD') {
          console.log(`❌ "${englishName}" → 식재료 아님`);
          return null;
        }
        
        if (cleanResult && cleanResult !== englishName && /[가-힣]/.test(cleanResult)) {
          console.log(`✅ "${englishName}" → "${cleanResult}"`);
          return cleanResult;
        }
        
        const fallbackResult = checkBasicFoodDictionary(englishName);
        console.log(`🔄 "${englishName}" → 기본 사전 확인: ${fallbackResult}`);
        return fallbackResult;
        
      } else {
        console.error(`❌ Detection 번역 API 오류: ${response.status}`);
        return checkBasicFoodDictionary(englishName);
      }
    } catch (error) {
      console.error(`❌ Detection 번역 중 오류: ${error}`);
      return checkBasicFoodDictionary(englishName);
    }
  }
};

// Gemini 결과에서 식품명 추출 헬퍼 함수
const extractFoodNameFromGeminiResult = (resultText, originalText) => {
  if (!resultText) {
    return performFallback(originalText);
  }
  
  try {
    const lines = resultText.trim().split('\n');
    let firstLine = lines[0].trim();
    
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
    
    firstLine = firstLine.replace(/\*\*/g, '').replace(/\*/g, '');
    
    if (firstLine.includes('(') && firstLine.includes(')')) {
      if (!firstLine.match(/\([0-9.%]+\)/)) {
        firstLine = firstLine.split('(')[0].trim();
      }
    }
    
    return firstLine || performFallback(originalText);
    
  } catch (error) {
    console.error('❌ Gemini 결과 추출 중 오류:', error);
    return performFallback(originalText);
  }
};

// Fallback 처리 함수
const performFallback = (text) => {
  console.log(`🔄 Fallback 추론 시작: "${text}"`);
  
  if (!text) return '식품';
  
  const cleanText = text.replace(/[^\w\s가-힣]/g, ' ').replace(/\s+/g, ' ').trim();
  
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
  
  const koreanWords = cleanText.match(/[가-힣]+/g);
  if (koreanWords && koreanWords.length > 0) {
    const firstKoreanWord = koreanWords[0];
    console.log(`🔍 첫 번째 한글 단어 사용: "${firstKoreanWord}"`);
    return firstKoreanWord;
  }
  
  return '식품';
};

// 기본 식재료 사전 확인 함수
const checkBasicFoodDictionary = (englishName) => {
  const FOOD_INGREDIENTS = {
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
    'corn': '옥수수',
    'cheese': '치즈',
    'yogurt': '요거트',
    'butter': '버터',
    'mushroom': '버섯',
    'garlic': '마늘',
    'ginger': '생강',
    'lemon': '레몬',
    'grape': '포도',
    'strawberry': '딸기'
  };
  
  const lowerName = englishName.toLowerCase();
  
  const nonFoodItems = ['person', 'hand', 'human', 'bottle', 'package', 'container', 'box', 'bag', 'plate', 'bowl', 'cup', 'glass', 'knife', 'fork', 'spoon', 'table', 'chair', 'wall', 'floor', 'ceiling', 'window', 'door', 'plastic', 'metal', 'wood', 'paper', 'cloth', 'fabric'];
  
  for (const nonFood of nonFoodItems) {
    if (lowerName.includes(nonFood)) {
      return null;
    }
  }
  
  const basicTranslation = FOOD_INGREDIENTS[lowerName];
  if (basicTranslation) {
    return basicTranslation;
  }
  
  for (const [englishKey, koreanValue] of Object.entries(FOOD_INGREDIENTS)) {
    if (lowerName.includes(englishKey) || englishKey.includes(lowerName)) {
      return koreanValue;
    }
  }
  
  return englishName;
};