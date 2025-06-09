// utils/inferenceEngine.js
import { 
  detectBrandAndProductAdvanced, 
  isBeverageByMl, 
  detectBrandOnly,
  getRepresentativeProduct
} from './brandDetection';
import { 
  extractIngredientsFromText, 
  classifyByIngredientsOnly 
} from './ingredientClassification';
import { 
  extractMeaningfulTextWithNumbers,
  performSimpleTextInference 
} from './foodProcessing';

// 텍스트에서 최대한 추론하는 함수 (브랜드+제품 조합 없을 때)
export const inferFromTextMaximally = (text) => {
  if (!text) return null;
  
  console.log(`🔍 텍스트 최대 추론 시작: "${text}"`);
  
  // 1. 브랜드명만 감지된 경우
  const brandOnly = detectBrandOnly(text);
  if (brandOnly) {
    console.log(`🏢 브랜드만 감지: "${brandOnly}"`);
    
    // 해당 브랜드의 대표 제품 추론
    const representativeProduct = getRepresentativeProduct(brandOnly, text);
    if (representativeProduct) {
      const result = `${brandOnly} ${representativeProduct}`;
      console.log(`✅ 브랜드 대표제품 추론: "${result}"`);
      return result;
    }
  }
  
  // 2. 음료 키워드 기반 추론
  if (isBeverageByMl(text)) {
    const beverageKeywords = [
      '우유', '두유', '주스', '밀크', '드링크', '음료', '쥬스', '라떼', '커피', '차', '티',
      '콜라', '사이다', '탄산', '물', '생수', '이온', '스포츠', '에너지', '비타민',
      '요구르트', '요거트', '셰이크', '스무디', '프라페', '아메리카노', '에스프레소',
      '카푸치노', '마키아토', '모카', '녹차', '홍차', '보이차', '우롱차', '허브차',
      '레모네이드', '에이드', '코코아', '핫초콜릿', '소주', '맥주', '와인', '막걸리'
    ];
    
    for (const keyword of beverageKeywords) {
      if (text.includes(keyword)) {
        console.log(`🥤 음료 키워드 기반 추론: "${keyword}"`);
        return keyword;
      }
    }
  }
  
  // 3. 식재료명 기반 추론
  const ingredientResult = extractIngredientsFromText(text);
  if (ingredientResult.length > 0) {
    const bestIngredient = ingredientResult[0].name;
    console.log(`🥬 식재료명 기반 추론: "${bestIngredient}"`);
    return bestIngredient;
  }
  
  // 4. 숫자 포함 텍스트 처리 (예: "매일두유99.9%")
  const textWithNumbers = extractMeaningfulTextWithNumbers(text);
  if (textWithNumbers) {
    console.log(`🔢 숫자 포함 텍스트 추론: "${textWithNumbers}"`);
    return textWithNumbers;
  }
  
  // 5. 첫 번째 의미있는 한글 단어
  const koreanWords = text.match(/[가-힣]{2,}/g);
  if (koreanWords && koreanWords.length > 0) {
    const meaningfulWord = koreanWords[0];
    console.log(`📝 의미있는 한글 단어: "${meaningfulWord}"`);
    return meaningfulWord;
  }
  
  return null;
};

// 개선된 4단계 추론 시스템
export const performAdvancedInference = (ocrText) => {
  if (!ocrText) {
    return {
      result: null,
      stage: 'no_input',
      confidence: 0.0,
      reasoning: '입력 텍스트가 없습니다.'
    };
  }

  console.log(`🚀 4단계 추론 시스템 시작: "${ocrText}"`);

  // 1단계: ml 음료 감지 → 브랜드명 감지 → 브랜드 제품 감지 → 브랜드 제품 없을 경우 추출텍스트에서 최대한 추론
  if (isBeverageByMl(ocrText)) {
    console.log(`🥤 1단계: ml 음료 감지 성공`);
    
    // 브랜드+제품 감지 시도
    const brandResult = detectBrandAndProductAdvanced(ocrText);
    if (brandResult.brand && brandResult.product) {
      const result = `${brandResult.brand} ${brandResult.product}`;
      console.log(`✅ 1단계 완료 - 브랜드+제품: "${result}"`);
      return {
        result: result,
        stage: 'ml_brand_product',
        confidence: 0.95,
        reasoning: `ml 단위 음료에서 브랜드+제품 감지: ${result}`
      };
    }
    
    // 브랜드+제품 없을 경우 최대한 추론
    const maxInference = inferFromTextMaximally(ocrText);
    if (maxInference) {
      console.log(`✅ 1단계 완료 - 최대 추론: "${maxInference}"`);
      return {
        result: maxInference,
        stage: 'ml_max_inference',
        confidence: 0.85,
        reasoning: `ml 단위 음료에서 최대 추론: ${maxInference}`
      };
    }
    
    // 기본 음료 반환
    console.log(`✅ 1단계 완료 - 기본 음료`);
    return {
      result: '음료',
      stage: 'ml_default',
      confidence: 0.8,
      reasoning: 'ml 단위와 음료 키워드가 감지되어 음료로 분류'
    };
  }

  // 2단계: 식재료명 직접 매칭
  const foundIngredients = extractIngredientsFromText(ocrText);
  if (foundIngredients.length > 0) {
    const bestIngredient = foundIngredients[0].name;
    console.log(`✅ 2단계 완료 - 식재료명 직접 매칭: "${bestIngredient}"`);
    return {
      result: bestIngredient,
      stage: 'ingredient_direct',
      confidence: 0.9,
      reasoning: `식재료명 직접 매칭: ${bestIngredient}`
    };
  }

  // 3단계: Gemini API 호출 필요 (여기서는 준비만)
  console.log(`🤖 3단계: Gemini API 호출 필요`);
  return {
    result: null,
    stage: 'need_gemini',
    confidence: 0.0,
    reasoning: 'Gemini API 호출이 필요합니다.'
  };
};

// 개선된 fallback 추론 함수 (4단계용)
export const performAdvancedFallback = (ocrText) => {
  console.log(`🔄 4단계: 고급 fallback 추론 시작`);
  
  // 브랜드+제품 조합 시도
  const brandResult = detectBrandAndProductAdvanced(ocrText);
  if (brandResult.brand && brandResult.product) {
    const result = `${brandResult.brand} ${brandResult.product}`;
    console.log(`✅ 4단계 - 브랜드+제품: "${result}"`);
    return result;
  }
  
  // 최대 추론 시도
  const maxInference = inferFromTextMaximally(ocrText);
  if (maxInference) {
    console.log(`✅ 4단계 - 최대 추론: "${maxInference}"`);
    return maxInference;
  }
  
  // 간단한 텍스트 추론
  const simpleResult = performSimpleTextInference(ocrText, classifyByIngredientsOnly);
  console.log(`✅ 4단계 - 간단 추론: "${simpleResult}"`);
  return simpleResult || '식품';
};

// 새로운 4단계 추론 시스템으로 대체된 함수
export const classifyByAdvancedInference = (ocrText) => {
  const inferenceResult = performAdvancedInference(ocrText);
  
  if (inferenceResult.result) {
    return {
      predicted_category: inferenceResult.result,
      confidence: inferenceResult.confidence,
      found_ingredients: [],
      reasoning: inferenceResult.reasoning,
      stage: inferenceResult.stage
    };
  } else if (inferenceResult.stage === 'need_gemini') {
    return {
      predicted_category: null,
      confidence: 0.0,
      found_ingredients: extractIngredientsFromText(ocrText),
      reasoning: 'Gemini API 호출이 필요합니다.',
      stage: 'need_gemini'
    };
  } else {
    return {
      predicted_category: '기타',
      confidence: 0.1,
      found_ingredients: [],
      reasoning: '추론할 수 없어 기타로 분류했습니다.',
      stage: 'failed'
    };
  }
};