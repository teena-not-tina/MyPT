// utils/brandDetection.js

// 향상된 브랜드 패턴 데이터베이스 (제품별 카테고리 포함)
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
  },
  '코카콜라': {
    '음료류': ['코카콜라', '스프라이트', '환타', '파워에이드']
  },
  '펩시': {
    '음료류': ['펩시콜라', '마운틴듀', '칠성사이다']
  },
  '롯데칠성': {
    '음료류': ['칠성사이다', '델몬트', '트레비']
  },
  '동서식품': {
    '커피류': ['맥심', '카누'],
    '음료류': ['포스트']
  },
  '네슬레': {
    '커피류': ['네스카페'],
    '과자류': ['킷캣']
  },
  '크라운': {
    '과자류': ['산도', '쿠크다스']
  },
  '동양제과': {
    '과자류': ['초코하임', '요하임']
  },
  '남양': {
    '음료류': ['초코에몽 프로틴']
  }
};

// 음료 관련 키워드 (ml가 포함된 경우 확인용)
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
  
  // 불필요한 문자 제거 및 정규화
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
            const confidence = brand.length + product.length + 20; // 브랜드+제품 매칭시 높은 점수
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
  
  // ml 단위 확인 (대소문자 구분 없이)
  const textLower = ocrText.toLowerCase();
  const hasMl = textLower.includes('ml');
  
  if (!hasMl) return false;
  
  // 음료 키워드 확인
  for (const keyword of BEVERAGE_KEYWORDS) {
    if (ocrText.includes(keyword)) {
      return true;
    }
  }
  
  return false;
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
  
  // 텍스트에서 카테고리 힌트 찾기
  const textLower = text.toLowerCase();
  
  // ml이 있으면 음료/유제품 우선
  if (textLower.includes('ml')) {
    if (brandData['음료류']) return brandData['음료류'][0];
    if (brandData['유제품']) return brandData['유제품'][0];
  }
  
  // 첫 번째 카테고리의 첫 번째 제품 반환
  const firstCategory = Object.keys(brandData)[0];
  return brandData[firstCategory][0];
};