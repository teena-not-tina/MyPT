// utils/enhancedOCRInference.js
// OCR 텍스트에서 정밀한 식재료 추론을 위한 향상된 시스템

/**
 * 식재료 패턴 매칭 규칙
 */
const INGREDIENT_PATTERNS = [
  // 음료류 (ml 포함)
  { 
    keywords: ['오렌지농축과즙', '오렌지과즙', '오렌지농축'], 
    volume: 'ml', 
    result: '오렌지주스',
    confidence: 0.95
  },
  { 
    keywords: ['아몬드추출액', '아몬드우유', '아몬드밀크'], 
    volume: 'ml', 
    result: '아몬드밀크',
    confidence: 0.95
  },
  { 
    keywords: ['원액두유', '분리대두단백', '대두농축액'], 
    volume: 'ml', 
    result: '두유',
    confidence: 0.95
  },
  { 
    keywords: ['우유', '전유', '저지방우유'], 
    volume: 'ml', 
    result: '우유',
    confidence: 0.98
  },
  { 
    keywords: ['사과과즙', '사과농축과즙'], 
    volume: 'ml', 
    result: '사과주스',
    confidence: 0.95
  },
  { 
    keywords: ['포도과즙', '포도농축과즙'], 
    volume: 'ml', 
    result: '포도주스',
    confidence: 0.95
  },
  { 
    keywords: ['토마토과즙', '토마토농축액'], 
    volume: 'ml', 
    result: '토마토주스',
    confidence: 0.95
  },
  
  // 채소류
  { 
    keywords: ['백오이', '백색오이'], 
    result: '오이',
    confidence: 0.90
  },
  { 
    keywords: ['무우', '무'], 
    result: '무',
    confidence: 0.95
  },
  { 
    keywords: ['당근', '홍당무'], 
    result: '당근',
    confidence: 0.95
  },
  { 
    keywords: ['양배추', '캐비지'], 
    result: '양배추',
    confidence: 0.90
  },
  { 
    keywords: ['상추', '청상추'], 
    result: '상추',
    confidence: 0.90
  },
  { 
    keywords: ['배추', '백배추', '절임배추'], 
    result: '배추',
    confidence: 0.95
  },
  
  // 과일류
  { 
    keywords: ['사과', '홍옥사과', '부사'], 
    result: '사과',
    confidence: 0.95
  },
  { 
    keywords: ['배', '신고배'], 
    result: '배',
    confidence: 0.95
  },
  { 
    keywords: ['바나나', '바나나'], 
    result: '바나나',
    confidence: 0.98
  },
  { 
    keywords: ['오렌지', '네이블오렌지'], 
    result: '오렌지',
    confidence: 0.95
  },
  
  // 육류/어류
  { 
    keywords: ['삼겹살', '돼지삼겹살'], 
    result: '삼겹살',
    confidence: 0.95
  },
  { 
    keywords: ['닭가슴살', '닭고기'], 
    result: '닭가슴살',
    confidence: 0.95
  },
  { 
    keywords: ['쇠고기', '한우'], 
    result: '쇠고기',
    confidence: 0.95
  },
  { 
    keywords: ['연어', '훈제연어'], 
    result: '연어',
    confidence: 0.95
  },
  
  // 유제품
  { 
    keywords: ['요구르트', '요거트', '플레인요구르트'], 
    result: '요구르트',
    confidence: 0.95
  },
  { 
    keywords: ['치즈', '슬라이스치즈', '모짜렐라'], 
    result: '치즈',
    confidence: 0.95
  },
  { 
    keywords: ['버터', '무염버터'], 
    result: '버터',
    confidence: 0.95
  },
  
  // 곡물/면류
  { 
    keywords: ['쌀', '백미', '현미'], 
    result: '쌀',
    confidence: 0.98
  },
  { 
    keywords: ['라면', '즉석라면'], 
    result: '라면',
    confidence: 0.95
  },
  { 
    keywords: ['스파게티', '파스타'], 
    result: '파스타',
    confidence: 0.95
  },
  
  // 조미료/소스
  { 
    keywords: ['간장', '양조간장'], 
    result: '간장',
    confidence: 0.95
  },
  { 
    keywords: ['고추장', '태양초고추장'], 
    result: '고추장',
    confidence: 0.95
  },
  { 
    keywords: ['마요네즈', '마요'], 
    result: '마요네즈',
    confidence: 0.95
  },
  { 
    keywords: ['케첩', '토마토케첩'], 
    result: '케챱',
    confidence: 0.95
  }
];

/**
 * OCR 텍스트에서 키워드 추출 및 정규화
 */
export const extractKeywordsFromOCR = (ocrText) => {
  if (!ocrText || typeof ocrText !== 'string') return [];
  
  // 텍스트 정리
  const cleanText = ocrText
    .replace(/\s+/g, '') // 공백 제거
    .replace(/[^\w가-힣]/g, '') // 특수문자 제거 (한글, 영문, 숫자만)
    .toLowerCase();
  
  // 의미있는 단어들 추출 (2-4글자)
  const keywords = [];
  
  // 2-4글자 단어 추출
  for (let i = 2; i <= 4; i++) {
    for (let j = 0; j <= cleanText.length - i; j++) {
      const word = cleanText.substring(j, j + i);
      if (word.length >= 2 && !keywords.includes(word)) {
        keywords.push(word);
      }
    }
  }
  
  return keywords.slice(0, 10); // 최대 10개 키워드만
};

/**
 * 패턴 기반 식재료 추론
 */
export const inferIngredientFromPatterns = (ocrText) => {
  if (!ocrText) return null;
  
  const normalizedText = ocrText.toLowerCase().replace(/\s+/g, '');
  const hasML = normalizedText.includes('ml') || normalizedText.includes('밀리리터');
  
  // 패턴 매칭
  for (const pattern of INGREDIENT_PATTERNS) {
    const hasKeyword = pattern.keywords.some(keyword => 
      normalizedText.includes(keyword.toLowerCase())
    );
    
    if (hasKeyword) {
      // 음료류인 경우 ml 확인
      if (pattern.volume === 'ml' && !hasML) {
        continue; // ml이 없으면 건너뛰기
      }
      
      return {
        ingredient: pattern.result,
        confidence: pattern.confidence,
        matchedKeywords: pattern.keywords.filter(keyword => 
          normalizedText.includes(keyword.toLowerCase())
        ),
        hasVolume: hasML,
        source: 'pattern_matching'
      };
    }
  }
  
  return null;
};

/**
 * 웹 검색을 통한 식재료 검증 및 매칭
 */
export const searchSimilarIngredients = async (keywords, webSearchFunction) => {
  if (!keywords || keywords.length === 0) return null;
  
  try {
    // 상위 3개 키워드로 검색
    const searchTerms = keywords.slice(0, 3).join(' ');
    const searchQuery = `${searchTerms} 식재료 음식 재료`;
    
    console.log(`🔍 웹 검색: "${searchQuery}"`);
    
    // 웹 검색 실행
    const searchResults = await webSearchFunction(searchQuery);
    
    if (!searchResults || !searchResults.length) {
      return null;
    }
    
    // 검색 결과에서 식재료명 추출
    const foundIngredients = extractIngredientsFromSearchResults(searchResults, keywords);
    
    if (foundIngredients.length > 0) {
      return {
        ingredient: foundIngredients[0].name,
        confidence: foundIngredients[0].confidence,
        matchedKeywords: foundIngredients[0].keywords,
        source: 'web_search',
        searchQuery: searchQuery,
        totalResults: searchResults.length
      };
    }
    
    return null;
  } catch (error) {
    console.error('웹 검색 중 오류:', error);
    return null;
  }
};

/**
 * 검색 결과에서 식재료 추출
 */
const extractIngredientsFromSearchResults = (searchResults, originalKeywords) => {
  const commonIngredients = [
    // 채소류
    '오이', '당근', '무', '배추', '상추', '양배추', '브로콜리', '시금치', '고구마', '감자',
    '양파', '마늘', '생강', '대파', '쪽파', '부추', '고추', '파프리카', '토마토', '가지',
    
    // 과일류  
    '사과', '배', '바나나', '오렌지', '포도', '딸기', '수박', '참외', '멜론', '복숭아',
    '자두', '키위', '망고', '파인애플', '레몬', '라임', '체리', '블루베리',
    
    // 육류/어류
    '쇠고기', '돼지고기', '닭고기', '삼겹살', '닭가슴살', '갈비', '등심', '안심',
    '연어', '고등어', '참치', '명태', '조기', '갈치', '삼치', '새우', '오징어', '문어',
    
    // 유제품
    '우유', '요구르트', '치즈', '버터', '크림', '아이스크림',
    
    // 음료류
    '오렌지주스', '사과주스', '포도주스', '토마토주스', '두유', '아몬드밀크', '코코넛밀크',
    
    // 곡물/면류
    '쌀', '현미', '보리', '밀', '라면', '우동', '파스타', '스파게티', '국수',
    
    // 조미료/소스
    '간장', '고추장', '된장', '마요네즈', '케챱', '식초', '설탕', '소금', '후추',
    
    // 기타
    '달걀', '계란', '두부', '김치', '김', '미역', '다시마'
  ];
  
  const results = [];
  
  // 검색 결과 텍스트 합치기
  const allText = searchResults
    .map(result => `${result.title || ''} ${result.snippet || ''}`)
    .join(' ')
    .toLowerCase();
  
  // 일반적인 식재료명 찾기
  for (const ingredient of commonIngredients) {
    if (allText.includes(ingredient)) {
      // 원본 키워드와 매칭도 계산
      const matchScore = calculateMatchScore(ingredient, originalKeywords);
      
      if (matchScore > 0.3) { // 30% 이상 매칭
        results.push({
          name: ingredient,
          confidence: Math.min(0.95, 0.7 + matchScore * 0.25),
          keywords: originalKeywords,
          matchScore: matchScore
        });
      }
    }
  }
  
  // 신뢰도 순으로 정렬
  return results.sort((a, b) => b.confidence - a.confidence);
};

/**
 * 키워드 매칭 점수 계산
 */
const calculateMatchScore = (ingredient, keywords) => {
  if (!keywords || keywords.length === 0) return 0;
  
  let totalScore = 0;
  const ingredientChars = ingredient.split('');
  
  for (const keyword of keywords) {
    const keywordChars = keyword.split('');
    let matchCount = 0;
    
    // 글자 단위로 매칭 확인
    for (const char of keywordChars) {
      if (ingredientChars.includes(char)) {
        matchCount++;
      }
    }
    
    const score = matchCount / Math.max(keywordChars.length, ingredientChars.length);
    totalScore = Math.max(totalScore, score);
  }
  
  return totalScore;
};

/**
 * 향상된 OCR 추론 메인 함수
 */
export const enhancedOCRInference = async (ocrText, webSearchFunction) => {
  if (!ocrText || ocrText.trim().length === 0) {
    return null;
  }
  
  console.log(`🚀 향상된 OCR 추론 시작: "${ocrText}"`);
  
  // 1단계: 패턴 기반 추론 (가장 빠르고 정확)
  const patternResult = inferIngredientFromPatterns(ocrText);
  if (patternResult && patternResult.confidence >= 0.85) {
    console.log(`✅ 패턴 매칭 성공:`, patternResult);
    return patternResult;
  }
  
  // 2단계: 키워드 추출
  const keywords = extractKeywordsFromOCR(ocrText);
  console.log(`🔑 추출된 키워드:`, keywords);
  
  // 3단계: 웹 검색 기반 추론
  if (webSearchFunction && keywords.length > 0) {
    const webSearchResult = await searchSimilarIngredients(keywords, webSearchFunction);
    if (webSearchResult && webSearchResult.confidence >= 0.7) {
      console.log(`🌐 웹 검색 성공:`, webSearchResult);
      return webSearchResult;
    }
  }
  
  // 4단계: 패턴 결과가 있다면 낮은 신뢰도라도 반환
  if (patternResult) {
    console.log(`📋 패턴 매칭 (낮은 신뢰도):`, patternResult);
    return patternResult;
  }
  
  // 5단계: 실패
  console.log(`❌ OCR 추론 실패: "${ocrText}"`);
  return null;
};

// export const enhancedOCRInference = async (ocrText, webSearchFunction) => {
//   if (!ocrText || ocrText.trim().length === 0) {
//     return null;
//   }

//   console.log(`🚀 OCR 전체 텍스트 기반 추론 시작: "${ocrText}"`);

//   // 전체 OCR 텍스트를 그대로 검색 쿼리로 사용
//   const searchQuery = `${ocrText} 식재료 음식 재료`;
//   console.log(`🔍 웹 검색: "${searchQuery}"`);
//   const searchResults = await webSearchFunction(searchQuery);

//   if (!searchResults || !searchResults.length) {
//     console.log(`❌ 검색 결과 없음`);
//     return null;
//   }

//   // 키워드는 여전히 추출하여 보조 판단에 사용
//   const keywords = extractKeywordsFromOCR(ocrText);
//   const foundIngredients = extractIngredientsFromSearchResults(searchResults, keywords);

//   if (foundIngredients.length > 0) {
//     const top = foundIngredients[0];
//     console.log(`🌐 웹 검색 결과 기반 추론 성공:`, top);
//     return {
//       ingredient: top.name,
//       confidence: top.confidence,
//       matchedKeywords: top.keywords,
//       source: 'google_search_full_text',
//       searchQuery,
//       totalResults: searchResults.length
//     };
//   }

//   console.log(`❌ 추론 실패: 식재료 없음`);
//   return null;
// };


/**
 * OCR 텍스트를 2-3단어로 축약
 */
export const summarizeOCRText = (ocrText) => {
  if (!ocrText) return '';
  
  const keywords = extractKeywordsFromOCR(ocrText);
  
  // 가장 의미있는 2-3개 키워드 선택
  const meaningfulKeywords = keywords
    .filter(keyword => keyword.length >= 2) // 2글자 이상
    .slice(0, 3); // 최대 3개
  
  return meaningfulKeywords.join(' ') || ocrText.substring(0, 10);
};