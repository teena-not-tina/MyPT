// frontend/src/components/Diet/utils/foodUtils.js

// 향상된 브랜드 패턴 데이터베이스
export const ENHANCED_BRAND_PATTERNS = {
  '농심': {
    '라면류': ['신라면', '너구리', '안성탕면', '짜파게티', '육개장', '새우탕', '튀김우동'],
    '스낵류': ['올리브', '포테토칩', '감자깡', '새우깡'],
    '기타': ['둥지냉면']
  },
  '오뚜기': {
    '라면류': ['진라면', '스낵면', '컵누들'],
    '소스류': ['참치마요', '케챱', '마요네즈'],
    '카레류': ['3분카레', '카레'],
    '조미료': ['미원', '다시다']
  },
  '롯데': {
    '과자류': ['초코파이', '빼빼로', '칸쵸', '꼬깔콘'],
    '초콜릿류': ['가나초콜릿', '드림카카오'],
    '아이스크림': ['메로나', '브라보콘'],
    '껌류': ['자일리톨']
  },
  '해태': {
    '과자류': ['홈런볼', '맛동산', '오예스', '허니버터칩'],
    '음료류': ['식혜', '수정과']
  },
  '오리온': {
    '과자류': ['초코파이', '참붕어빵', '치토스'],
    '음료류': ['닥터유']
  },
  '삼양': {
    '라면류': ['불닭볶음면', '까르보불닭', '삼양라면', '짜장불닭']
  },
  '팔도': {
    '라면류': ['팔도비빔면', '왕뚜껑']
  },
  'CJ': {
    '즉석밥': ['햇반'],
    '냉동식품': ['비비고'],
    '조미료': ['백설']
  },
  '동원': {
    '통조림': ['참치캔', '리챔'],
    '김치류': ['김치찌개', '양반김']
  },
  '빙그레': {
    '유제품': ['바나나우유', '딸기우유', '초코우유'],
    '아이스크림': ['메로나', '투게더', '빵빠레']
  },
  '매일': {
    '유제품': ['매일우유', '상하목장', '소화가잘되는우유', '두유']
  },
  '서울우유': {
    '유제품': ['서울우유', '아이셔', '카페라떼']
  }
};

// 식재료명 기반 분류 사전
export const INGREDIENT_CATEGORIES = {
  '곡류': [
    '쌀', '현미', '백미', '찹쌀', '흑미', '보리', '귀리', '밀', '옥수수', '수수', '조', '기장',
    '퀴노아', '메밀', '쌀가루', '밀가루', '옥수수가루', '전분', '떡', '누룽지', '식빵', '빵',
    '면', '국수', '파스타', '스파게티', '우동', '라면', '냉면', '당면', '쌀국수'
  ],
  '육류': [
    '소고기', '돼지고기', '닭고기', '오리고기', '양고기', '염소고기', '사슴고기', '토끼고기',
    '갈비', '불고기', '등심', '안심', '목살', '삼겹살', '앞다리', '뒷다리', '닭가슴살', '닭다리',
    '닭날개', '닭발', '족발', '순대', '소세지', '햄', '베이컨', '육회', '간', '콩팥', '심장',
    '곱창', '대창', '막창', '양', '육수', '사골', '도가니', '꼬리', '갈빗대', '목뼈'
  ],
  '어패류': [
    '생선', '고등어', '삼치', '갈치', '꽁치', '조기', '민어', '농어', '광어', '가자미', '우럭',
    '숭어', '연어', '참치', '다랑어', '명태', '대구', '아귀', '장어', '뱀장어', '붕어', '잉어',
    '송어', '전어', '멸치', '정어리', '새우', '게', '꽃게', '대게', '킹크랩', '랍스터',
    '조개', '굴', '전복', '소라', '키조개', '가리비', '홍합', '바지락', '재첩', '맛조개',
    '오징어', '낙지', '문어', '쭈꾸미', '갑오징어', '한치', '해삼', '성게', '멍게', '미역',
    '다시마', '김', '파래', '톳', '모자반', '젓갈', '굴비', '북어', '황태', '코다리'
  ],
  '채소류': [
    '배추', '양배추', '상추', '시금치', '미나리', '쑥갓', '근대', '청경채', '갓', '케일',
    '브로콜리', '콜리플라워', '양상추', '치커리', '아루굴라', '로메인', '적상추', '쌈채소',
    '무', '당근', '감자', '고구마', '토란', '마', '연근', '우엉', '도라지', '더덕',
    '양파', '대파', '쪽파', '부추', '마늘', '생강', '고추', '피망', '파프리카', '오이',
    '호박', '애호박', '단호박', '가지', '토마토', '방울토마토', '옥수수', '콩나물', '숙주',
    '고사리', '도라지', '버섯', '느타리버섯', '팽이버섯', '새송이버섯', '표고버섯', '송이버섯'
  ],
  '과일류': [
    '사과', '배', '복숭아', '자두', '살구', '체리', '포도', '딸기', '참외', '수박', '멜론',
    '바나나', '오렌지', '귤', '감', '곶감', '석류', '키위', '파인애플', '망고', '아보카도',
    '레몬', '라임', '자몽', '오미자', '대추', '무화과', '감귤', '한라봉', '천혜향', '레드향',
    '블루베리', '라즈베리', '크랜베리', '건포도', '건살구', '건자두', '견과류', '호두',
    '아몬드', '땅콩', '잣', '피스타치오', '헤이즐넛', '마카다미아', '피칸', '캐슈넛'
  ],
  '유제품': [
    '우유', '저지방우유', '무지방우유', '전지우유', '생크림', '휘핑크림', '사워크림',
    '크림치즈', '치즈', '체다치즈', '모짜렐라치즈', '파마산치즈', '고르곤졸라치즈',
    '까망베르치즈', '브리치즈', '슬라이스치즈', '스트링치즈', '리코타치즈', '마스카포네',
    '요거트', '요구르트', '그릭요거트', '플레인요거트', '딸기요거트', '블루베리요거트',
    '버터', '마가린', '발효버터', '무염버터', '유청', '연유', '분유', '아이스크림'
  ]
};

// 음료 관련 키워드
export const BEVERAGE_KEYWORDS = [
  '우유', '두유', '주스', '밀크', '드링크', '음료', '쥬스', '라떼', '커피', '차', '티',
  '콜라', '사이다', '탄산', '물', '생수', '이온', '스포츠', '에너지', '비타민',
  '요구르트', '요거트', '셰이크', '스무디', '프라페', '아메리카노', '에스프레소',
  '카푸치노', '마키아토', '모카', '녹차', '홍차', '보이차', '우롱차', '허브차',
  '레모네이드', '에이드', '코코아', '핫초콜릿', '소주', '맥주', '와인', '막걸리'
];

// OCR 텍스트 전처리 함수
export const preprocessTextForBrandDetection = (text) => {
  if (!text) return "";
  
  text = text.replace(/[^\w\s가-힣]/g, ' ');
  text = text.replace(/\s+/g, ' ').trim();
  
  return text;
};

// 향상된 브랜드/제품명 탐지 함수
export const detectBrandAndProductAdvanced = (text) => {
  if (!text) return { brand: null, product: null, category: null, confidence: 0 };
  
  const preprocessed = preprocessTextForBrandDetection(text);
  const textUpper = preprocessed.toUpperCase();
  
  let detectedBrand = null;
  let detectedProduct = null;
  let detectedCategory = null;
  let maxConfidence = 0;
  
  // 향상된 브랜드별 제품 탐지
  Object.entries(ENHANCED_BRAND_PATTERNS).forEach(([brand, categories]) => {
    const brandUpper = brand.toUpperCase();
    const hasBrand = preprocessed.includes(brand) || textUpper.includes(brandUpper);
    
    if (hasBrand) {
      Object.entries(categories).forEach(([category, products]) => {
        products.forEach(product => {
          const productUpper = product.toUpperCase();
          if (preprocessed.includes(product) || textUpper.includes(productUpper)) {
            const confidence = brand.length + product.length + 20;
            if (confidence > maxConfidence) {
              detectedBrand = brand;
              detectedProduct = product;
              detectedCategory = category;
              maxConfidence = confidence;
            }
          }
        });
      });
    }
  });
  
  // 브랜드 없이 제품명만 발견된 경우
  if (!detectedBrand) {
    Object.entries(ENHANCED_BRAND_PATTERNS).forEach(([brand, categories]) => {
      Object.entries(categories).forEach(([category, products]) => {
        products.forEach(product => {
          const productUpper = product.toUpperCase();
          if (preprocessed.includes(product) || textUpper.includes(productUpper)) {
            const confidence = product.length;
            if (confidence > maxConfidence) {
              detectedBrand = brand;
              detectedProduct = product;
              detectedCategory = category;
              maxConfidence = confidence;
            }
          }
        });
      });
    });
  }
  
  return {
    brand: detectedBrand,
    product: detectedProduct,
    category: detectedCategory,
    confidence: maxConfidence,
    fullName: detectedBrand && detectedProduct ? `${detectedBrand} ${detectedProduct}` : null
  };
};

// OCR 텍스트에서 ml 단위가 있고 음료 키워드가 포함되어 있는지 확인
export const isBeverageByMl = (ocrText) => {
  if (!ocrText) return false;
  
  const textLower = ocrText.toLowerCase();
  const hasMl = textLower.includes('ml');
  
  if (!hasMl) return false;
  
  for (const keyword of BEVERAGE_KEYWORDS) {
    if (ocrText.includes(keyword)) {
      return true;
    }
  }
  
  return false;
};

// 텍스트에서 식재료명 추출
export const extractIngredientsFromText = (text) => {
  if (!text) return [];
  
  const foundIngredients = [];
  
  for (const [category, ingredients] of Object.entries(INGREDIENT_CATEGORIES)) {
    for (const ingredient of ingredients) {
      if (text.includes(ingredient)) {
        foundIngredients.push({
          name: ingredient,
          category: category
        });
      }
    }
  }
  
  return foundIngredients;
};

// 텍스트에서 최대한 추론하는 함수
export const inferFromTextMaximally = (text) => {
  if (!text) return null;
  
  console.log(`🔍 텍스트 최대 추론 시작: "${text}"`);
  
  // 1. 브랜드명만 감지된 경우
  const brandOnly = detectBrandOnly(text);
  if (brandOnly) {
    console.log(`🏢 브랜드만 감지: "${brandOnly}"`);
    
    const representativeProduct = getRepresentativeProduct(brandOnly, text);
    if (representativeProduct) {
      const result = `${brandOnly} ${representativeProduct}`;
      console.log(`✅ 브랜드 대표제품 추론: "${result}"`);
      return result;
    }
  }
  
  // 2. 음료 키워드 기반 추론
  if (isBeverageByMl(text)) {
    for (const keyword of BEVERAGE_KEYWORDS) {
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
  
  // 4. 숫자 포함 텍스트 처리
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

// 브랜드명만 감지하는 함수
export const detectBrandOnly = (text) => {
  const preprocessed = preprocessTextForBrandDetection(text);
  const textUpper = preprocessed.toUpperCase();
  
  for (const brand of Object.keys(ENHANCED_BRAND_PATTERNS)) {
    const brandUpper = brand.toUpperCase();
    if (preprocessed.includes(brand) || textUpper.includes(brandUpper)) {
      return brand;
    }
  }
  return null;
};

// 브랜드의 대표 제품 추론
export const getRepresentativeProduct = (brand, text) => {
  const brandData = ENHANCED_BRAND_PATTERNS[brand];
  if (!brandData) return null;
  
  const textLower = text.toLowerCase();
  
  if (textLower.includes('ml')) {
    if (brandData['음료류']) return brandData['음료류'][0];
    if (brandData['유제품']) return brandData['유제품'][0];
  }
  
  const firstCategory = Object.keys(brandData)[0];
  return brandData[firstCategory][0];
};

// 숫자 포함 의미있는 텍스트 추출
export const extractMeaningfulTextWithNumbers = (text) => {
  const patterns = [
    /[가-힣]+\d+\.?\d*%/g,
    /[가-힣]+\d+\.?\d*[가-힣]*/g,
    /[가-힣]+\s*\d+\.?\d*/g
  ];
  
  for (const pattern of patterns) {
    const matches = text.match(pattern);
    if (matches && matches.length > 0) {
      const longestMatch = matches.reduce((a, b) => a.length > b.length ? a : b);
      if (longestMatch.length >= 4) {
        return longestMatch;
      }
    }
  }
  
  return null;
};