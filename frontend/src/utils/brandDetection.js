export const BRAND_PATTERNS = {
  '농심': ['신라면', '너구리', '안성탕면', '짜파게티', '육개장', '새우탕', '올리브'],
  '오뚜기': ['진라면', '스낵면', '컵누들', '참치마요', '카레', '3분카레'],
  // ... 기존 브랜드 패턴 데이터
};

export const detectBrandAndProduct = (text) => {
  if (!text) return { brand: null, product: null, confidence: 0 };
  
  // 기존 브랜드 탐지 로직을 여기로 이동
  const preprocessed = text.replace(/[^\w\s가-힣]/g, ' ').replace(/\s+/g, ' ').trim();
  // ... 브랜드 탐지 로직
  
  return {
    brand: detectedBrand,
    product: detectedProduct,
    confidence: maxConfidence,
    fullName: detectedBrand && detectedProduct ? `${detectedBrand} ${detectedProduct}` : null
  };
};