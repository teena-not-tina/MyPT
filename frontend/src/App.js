import React, { useState, useRef, useEffect } from 'react';

const FoodDetectionApp = () => {
  // 상태 관리 (바로 homeCooking 모드로 시작)
  const [currentMode, setCurrentMode] = useState('homeCooking');
  const [images, setImages] = useState([]);
  const [detectionResults, setDetectionResults] = useState({});
  const [ocrResults, setOcrResults] = useState({});
  const [geminiResults, setGeminiResults] = useState({});
  const [fridgeIngredients, setFridgeIngredients] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [confidence, setConfidence] = useState(0.8);
  const [statusMessage, setStatusMessage] = useState('냉장고 속 식재료 이미지를 업로드하세요.');
  const [isDragOver, setIsDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState('detection');
  const [showSaveButton, setShowSaveButton] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [userId, setUserId] = useState('user_' + Date.now());
  const [clearBeforeAnalysis, setClearBeforeAnalysis] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [processingImageIndex, setProcessingImageIndex] = useState(-1);
  
  // FatSecret 관련 상태
  const [fatSecretResults, setFatSecretResults] = useState({});
  const [dashboardData, setDashboardData] = useState([]);
  const [isUploadingToDashboard, setIsUploadingToDashboard] = useState(false);
  const [fatSecretSearchEnabled, setFatSecretSearchEnabled] = useState(true);
  
  // 직접 추가 기능 관련 상태
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualIngredientName, setManualIngredientName] = useState('');
  const [manualIngredientQuantity, setManualIngredientQuantity] = useState(1);
  const [isAddingManual, setIsAddingManual] = useState(false);
  
  // Detection 결과 표시용 번역 캐시
  const [detectionTranslations, setDetectionTranslations] = useState({});

  // Refs
  const fileInputRef = useRef(null);
  const analysisTimeoutRef = useRef(null);
  const manualInputRef = useRef(null);
  
  // API 설정
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://192.168.0.19:8080';
  const GEMINI_API_KEY = process.env.REACT_APP_GEMINI_API_KEY || 'AIzaSyBBHRss0KLaEeeAgggsVOIGQ_zhS5ssDGw';
  const GEMINI_API_URL = process.env.REACT_APP_GEMINI_API_URL || 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent';

  // ===== 향상된 브랜드 패턴 데이터베이스 =====
  
  // 향상된 브랜드 패턴 데이터베이스 (제품별 카테고리 포함)
  const ENHANCED_BRAND_PATTERNS = {
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
    }
  };

  // ===== 새로운 식재료 분류 시스템 =====
  
  // 식재료명 기반 분류 사전
  const INGREDIENT_CATEGORIES = {
    // 곡류
    '곡류': [
      '쌀', '현미', '백미', '찹쌀', '흑미', '보리', '귀리', '밀', '옥수수', '수수', '조', '기장',
      '퀴노아', '메밀', '쌀가루', '밀가루', '옥수수가루', '전분', '떡', '누룽지', '식빵', '빵',
      '면', '국수', '파스타', '스파게티', '우동', '라면', '냉면', '당면', '쌀국수'
    ],
    
    // 육류
    '육류': [
      '소고기', '돼지고기', '닭고기', '오리고기', '양고기', '염소고기', '사슴고기', '토끼고기',
      '갈비', '불고기', '등심', '안심', '목살', '삼겹살', '앞다리', '뒷다리', '닭가슴살', '닭다리',
      '닭날개', '닭발', '족발', '순대', '소세지', '햄', '베이컨', '육회', '간', '콩팥', '심장',
      '곱창', '대창', '막창', '양', '육수', '사골', '도가니', '꼬리', '갈빗대', '목뼈'
    ],
    
    // 어패류
    '어패류': [
      '생선', '고등어', '삼치', '갈치', '꽁치', '조기', '민어', '농어', '광어', '가자미', '우럭',
      '숭어', '연어', '참치', '다랑어', '명태', '대구', '아귀', '장어', '뱀장어', '붕어', '잉어',
      '송어', '전어', '멸치', '정어리', '새우', '게', '꽃게', '대게', '킹크랩', '랍스터',
      '조개', '굴', '전복', '소라', '키조개', '가리비', '홍합', '바지락', '재첩', '맛조개',
      '오징어', '낙지', '문어', '쭈꾸미', '갑오징어', '한치', '해삼', '성게', '멍게', '미역',
      '다시마', '김', '파래', '톳', '모자반', '젓갈', '굴비', '북어', '황태', '코다리',
      '마른오징어', '건새우', '마른멸치', '어묵', '게맛살', '맛살', '젓갈', '액젓', '새우젓'
    ],
    
    // 채소류
    '채소류': [
      '배추', '양배추', '상추', '시금치', '미나리', '쑥갓', '근대', '청경채', '갓', '케일',
      '브로콜리', '콜리플라워', '양상추', '치커리', '아루굴라', '로메인', '적상추', '쌈채소',
      '무', '당근', '감자', '고구마', '토란', '마', '연근', '우엉', '도라지', '더덕',
      '양파', '대파', '쪽파', '부추', '마늘', '생강', '고추', '피망', '파프리카', '오이',
      '호박', '애호박', '단호박', '가지', '토마토', '방울토마토', '옥수수', '콩나물', '숙주',
      '고사리', '도라지', '버섯', '느타리버섯', '팽이버섯', '새송이버섯', '표고버섯', '송이버섯',
      '목이버섯', '석이버섯', '만가닥버섯', '양송이버섯', '죽순', '연잎', '연뿌리', '치자',
      '깻잎', '상추', '겨자채', '냉이', '달래', '두릅', '죽순', '고춧잎', '호박잎',
      '김치', '깍두기', '총각김치', '오이소박이', '물김치', '동치미', '장아찌', '피클'
    ],
    
    // 과일류
    '과일류': [
      '사과', '배', '복숭아', '자두', '살구', '체리', '포도', '딸기', '참외', '수박', '멜론',
      '바나나', '오렌지', '귤', '감', '곶감', '석류', '키위', '파인애플', '망고', '아보카도',
      '레몬', '라임', '자몽', '오미자', '대추', '무화과', '감귤', '한라봉', '천혜향', '레드향',
      '블루베리', '라즈베리', '크랜베리', '건포도', '건살구', '건자두', '견과류', '호두',
      '아몬드', '땅콩', '잣', '피스타치오', '헤이즐넛', '마카다미아', '피칸', '캐슈넛',
      '밤', '은행', '도토리', '해바라기씨', '호박씨', '참깨', '들깨', '검은깨', '잼',
      '마멀레이드', '과일청', '과일즙', '과일퓨레'
    ],
    
    // 콩류
    '콩류': [
      '콩', '대두', '검은콩', '서리태', '완두콩', '강낭콩', '팥', '녹두', '렌틸콩', '병아리콩',
      '두부', '순두부', '연두부', '부침개용두부', '유부', '콩나물', '두유', '콩가루', '콩기름',
      '된장', '간장', '고추장', '쌈장', '청국장', '낫토', '미소', '두반장', '콩비지',
      '콩국수', '콩죽', '인절미', '콩떡', '콩조림', '콩자반', '콩엿', '템페'
    ],
    
    // 유제품
    '유제품': [
      '우유', '저지방우유', '무지방우유', '전지우유', '생크림', '휘핑크림', '사워크림',
      '크림치즈', '치즈', '체다치즈', '모짜렐라치즈', '파마산치즈', '고르곤졸라치즈',
      '까망베르치즈', '브리치즈', '슬라이스치즈', '스트링치즈', '리코타치즈', '마스카포네',
      '요거트', '요구르트', '그릭요거트', '플레인요거트', '딸기요거트', '블루베리요거트',
      '버터', '마가린', '발효버터', '무염버터', '유청', '연유', '분유', '아이스크림',
      '젤라토', '셔벗', '유산균음료', '케피어', '라씨'
    ],
    
    // 계란류
    '계란류': [
      '계란', '달걀', '메추리알', '오리알', '염란', '피단', '삶은계란', '날계란', '계란흰자',
      '계란노른자', '계란물', '스크램블', '오믈렛', '계란찜', '계란말이', '계란후라이',
      '계란샐러드', '마요네즈', '계란국', '계란죽', '계란빵', '카스테라'
    ],
    
    // 조미료/양념류
    '조미료': [
      '소금', '설탕', '흑설탕', '황설탕', '꿀', '메이플시럽', '올리고당', '물엿', '조청',
      '식초', '사과식초', '현미식초', '발사믹식초', '와인식초', '미림', '맛술', '청주',
      '소주', '맥주', '와인', '브랜디', '럼', '진', '보드카', '위스키', '사케',
      '참기름', '들기름', '올리브오일', '포도씨오일', '카놀라오일', '해바라기유', '코코넛오일',
      '버터', '라드', '쇼트닝', '마가린', '식용유', '튀김기름', '후추', '계피', '정향',
      '육두구', '올스파이스', '바질', '로즈마리', '타임', '오레가노', '파슬리', '고수',
      '딜', '세이지', '라벤더', '민트', '강황', '커리가루', '카레가루', '칠리파우더',
      '파프리카파우더', '마늘가루', '양파가루', '생강가루', '후추가루', '계피가루',
      '겨자', '와사비', '고추냉이', '마요네즈', '케첩', '머스타드', '타바스코', '핫소스',
      '우스터소스', '굴소스', '어간장', '생선간장', '국간장', '진간장', '양조간장',
      '미소', '멘츠유', '폰즈', '테리야키소스', '바베큐소스', '스테이크소스', '토마토소스',
      '파스타소스', '피자소스', '살사소스', '페스토', '치즈소스', '화이트소스', '브라운소스'
    ],
    
    // 기타/가공식품
    '기타': [
      '라면', '컵라면', '우동', '소바', '쌀국수', '파스타', '마카로니', '시리얼', '콘플레이크',
      '오트밀', '그래놀라', '뮤즐리', '크래커', '비스킷', '쿠키', '케이크', '파이', '도넛',
      '머핀', '스콘', '와플', '팬케이크', '토스트', '샌드위치', '햄버거', '핫도그', '피자',
      '만두', '교자', '슈마이', '딤섬', '춘권', '튀김', '돈까스', '치킨', '너겟', '소시지',
      '햄', '베이컨', '살라미', '통조림', '참치캔', '옥수수캔', '토마토캔', '콩캔', '스팸',
      '인스턴트', '즉석밥', '죽', '스프', '육수', '다시마', '멸치', '북어', '황태',
      '젓갈', '김치', '장아찌', '피클', '올리브', '케이퍼', '아몬드', '견과류', '건과일',
      '과자', '초콜릿', '사탕', '젤리', '푸딩', '요거트', '아이스크림', '빙수', '팥빙수',
      '호떡', '붕어빵', '잇템빵', '찐빵', '단팥빵', '크림빵', '소보로빵', '식빵', '바게트',
      '치아바타', '베이글', '크루아상', '데니쉬', '브리오슈', '프레첼', '나초', '팝콘',
      '견과류', '드라이프루츠', '육포', '어포', '김', '멸치', '오징어', '새우깡', '감자칩'
    ]
  };

  // 음료 관련 키워드 (ml가 포함된 경우 확인용)
  const BEVERAGE_KEYWORDS = [
    '우유', '두유', '주스', '밀크', '드링크', '음료', '쥬스', '라떼', '커피', '차', '티',
    '콜라', '사이다', '탄산', '물', '생수', '이온', '스포츠', '에너지', '비타민',
    '요구르트', '요거트', '셰이크', '스무디', '프라페', '아메리카노', '에스프레소',
    '카푸치노', '마키아토', '모카', '녹차', '홍차', '보이차', '우롱차', '허브차',
    '레모네이드', '에이드', '코코아', '핫초콜릿', '소주', '맥주', '와인', '막걸리'
  ];

  // FatSecret Korea에서 식품 검색하는 함수
  const searchFatSecret = async (foodName) => {
    if (!foodName || !fatSecretSearchEnabled) {
      return null;
    }

    try {
      console.log(`🔍 FatSecret 검색 시작: "${foodName}"`);
      setProcessingStep(`FatSecret에서 "${foodName}" 검색 중...`);

      // 백엔드 API를 통한 FatSecret 검색 요청
      const searchResponse = await fetch(`${API_BASE_URL}/api/fatsecret/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: foodName,
          userId: userId
        }),
      });

      if (searchResponse.ok) {
        const searchResult = await searchResponse.json();
        console.log(`✅ FatSecret 검색 성공:`, searchResult);

        if (searchResult.found && searchResult.nutritionData) {
          console.log(`📊 영양정보 발견: ${searchResult.nutritionData.name}`);
          return {
            found: true,
            foodName: foodName,
            originalQuery: foodName,
            nutritionData: searchResult.nutritionData,
            fatSecretUrl: searchResult.url || `https://www.fatsecret.kr/#search-food=${encodeURIComponent(foodName)}`,
            searchedAt: new Date().toISOString()
          };
        } else {
          console.log(`❌ FatSecret에서 "${foodName}" 매칭 결과 없음`);
          return {
            found: false,
            foodName: foodName,
            originalQuery: foodName,
            message: '매칭되는 영양정보를 찾을 수 없습니다.',
            searchedAt: new Date().toISOString()
          };
        }
      } else {
        throw new Error(`FatSecret 검색 API 오류: ${searchResponse.status}`);
      }
    } catch (error) {
      console.error(`❌ FatSecret 검색 중 오류:`, error);
      return {
        found: false,
        foodName: foodName,
        originalQuery: foodName,
        error: error.message,
        searchedAt: new Date().toISOString()
      };
    }
  };

  // 대시보드에 영양정보 업로드하는 함수
  const uploadToDashboard = async (nutritionData, imageId = null) => {
    if (!nutritionData || !nutritionData.found) {
      return false;
    }

    try {
      console.log(`📤 대시보드 업로드 시작:`, nutritionData.foodName);
      setIsUploadingToDashboard(true);
      setProcessingStep(`"${nutritionData.foodName}" 대시보드 업로드 중...`);

      // 대시보드 업로드를 위한 데이터 구성
      const dashboardEntry = {
        id: Date.now() + Math.random(),
        userId: userId,
        foodName: nutritionData.foodName,
        originalQuery: nutritionData.originalQuery,
        nutritionData: nutritionData.nutritionData,
        fatSecretUrl: nutritionData.fatSecretUrl,
        imageId: imageId,
        uploadedAt: new Date().toISOString(),
        source: 'fatsecret_auto'
      };

      // 백엔드 대시보드 API 호출
      const uploadResponse = await fetch(`${API_BASE_URL}/api/dashboard/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dashboardEntry),
      });

      if (uploadResponse.ok) {
        const uploadResult = await uploadResponse.json();
        console.log(`✅ 대시보드 업로드 성공:`, uploadResult);

        // 로컬 대시보드 데이터 업데이트
        setDashboardData(prev => [dashboardEntry, ...prev]);

        setStatusMessage(`✅ "${nutritionData.foodName}" 영양정보가 대시보드에 업로드되었습니다!`);
        return true;
      } else {
        throw new Error(`대시보드 업로드 API 오류: ${uploadResponse.status}`);
      }
    } catch (error) {
      console.error(`❌ 대시보드 업로드 중 오류:`, error);
      setStatusMessage(`❌ "${nutritionData.foodName}" 대시보드 업로드 실패: ${error.message}`);
      return false;
    } finally {
      setIsUploadingToDashboard(false);
    }
  };

  // FatSecret 검색 결과를 포함한 종합 추론 함수
  const performInferenceWithFatSecret = async (ocrText, imageId = null) => {
    console.log(`🚀 FatSecret 포함 종합 추론 시작: "${ocrText}"`);

    // 1단계: 기존 4단계 추론 수행
    const basicInference = await callGeminiAPIWithAdvancedInference(ocrText);
    
    if (!basicInference) {
      console.log(`❌ 기본 추론 실패`);
      return {
        foodName: null,
        fatSecretResult: null,
        dashboardUploaded: false
      };
    }

    console.log(`✅ 기본 추론 완료: "${basicInference}"`);

    // 2단계: FatSecret에서 영양정보 검색
    if (fatSecretSearchEnabled) {
      setProcessingStep(`FatSecret에서 영양정보 검색 중...`);
      
      const fatSecretResult = await searchFatSecret(basicInference);
      
      // FatSecret 결과 저장
      if (imageId) {
        setFatSecretResults(prev => ({
          ...prev,
          [imageId]: fatSecretResult
        }));
      }

      // 3단계: 매칭되는 경우 대시보드 업로드
      let dashboardUploaded = false;
      if (fatSecretResult && fatSecretResult.found) {
        console.log(`📊 FatSecret 매칭 성공 - 대시보드 업로드 시도`);
        dashboardUploaded = await uploadToDashboard(fatSecretResult, imageId);
      } else {
        console.log(`❌ FatSecret 매칭 실패 - 대시보드 업로드 생략`);
      }

      return {
        foodName: basicInference,
        fatSecretResult: fatSecretResult,
        dashboardUploaded: dashboardUploaded
      };
    } else {
      console.log(`⚠️ FatSecret 검색 비활성화됨`);
      return {
        foodName: basicInference,
        fatSecretResult: null,
        dashboardUploaded: false
      };
    }
  };

  // 대시보드 데이터 불러오기
  const loadDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard/load/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data.entries || []);
        console.log(`📥 대시보드 데이터 불러오기 완료: ${data.entries?.length || 0}개`);
      }
    } catch (error) {
      console.error('❌ 대시보드 데이터 불러오기 실패:', error);
    }
  };

  // 대시보드에서 항목 삭제
  const removeDashboardEntry = async (entryId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard/delete/${entryId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setDashboardData(prev => prev.filter(entry => entry.id !== entryId));
        setStatusMessage('✅ 대시보드 항목이 삭제되었습니다.');
      }
    } catch (error) {
      console.error('❌ 대시보드 항목 삭제 실패:', error);
      setStatusMessage('❌ 대시보드 항목 삭제에 실패했습니다.');
    }
  };

  // OCR 텍스트 전처리 함수
  const preprocessTextForBrandDetection = (text) => {
    if (!text) return "";
    
    // 불필요한 문자 제거 및 정규화
    text = text.replace(/[^\w\s가-힣]/g, ' ');
    text = text.replace(/\s+/g, ' ').trim();
    
    return text;
  };

  // 향상된 브랜드/제품명 탐지 함수
  const detectBrandAndProductAdvanced = (text) => {
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
  const isBeverageByMl = (ocrText) => {
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

  // 텍스트에서 최대한 추론하는 함수 (브랜드+제품 조합 없을 때)
  const inferFromTextMaximally = (text) => {
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

  // 브랜드명만 감지하는 함수
  const detectBrandOnly = (text) => {
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
  const getRepresentativeProduct = (brand, text) => {
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

  // 숫자 포함 의미있는 텍스트 추출 (예: "매일두유99.9%")
  const extractMeaningfulTextWithNumbers = (text) => {
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

  // 텍스트에서 식재료명 추출
  const extractIngredientsFromText = (text) => {
    if (!text) return [];
    
    const foundIngredients = [];
    
    // 모든 카테고리의 식재료를 검색
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

  // 개선된 4단계 추론 시스템
  const performAdvancedInference = (ocrText) => {
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
  const performAdvancedFallback = (ocrText) => {
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
    const simpleResult = performSimpleTextInference(ocrText);
    console.log(`✅ 4단계 - 간단 추론: "${simpleResult}"`);
    return simpleResult || '식품';
  };

  // 새로운 4단계 추론 시스템으로 대체된 함수
  const classifyByAdvancedInference = (ocrText) => {
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

  // 개선된 4단계 추론 시스템을 적용한 Gemini API 호출 함수
  const callGeminiAPIWithAdvancedInference = async (text, detectionResults = null) => {
    if (!text || text.trim() === "") {
      console.log("분석할 텍스트가 없습니다.");
      return null;
    }
    
    try {
      console.log(`🚀 4단계 추론 시스템 시작 - 텍스트 길이: ${text.length}`);
      
      // 1~2단계: 고급 추론 시도
      const advancedResult = performAdvancedInference(text);
      
      // 1~2단계에서 결과가 나오면 바로 반환 (API 호출 없이)
      if (advancedResult.result && advancedResult.stage !== 'need_gemini') {
        console.log(`✅ ${advancedResult.stage} 단계에서 해결 - API 호출 생략: "${advancedResult.result}"`);
        return advancedResult.result;
      }
      
      // 3단계: Gemini API 호출
      console.log(`🤖 3단계: Gemini API 호출 진행`);
      
      // 탐지 결과가 있으면 컨텍스트에 포함
      let detectionContext = "";
      if (detectionResults && detectionResults.length > 0) {
        const detectedClasses = detectionResults.filter(det => det.class !== 'other').map(det => det.class);
        if (detectedClasses.length > 0) {
          detectionContext = `\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: ${detectedClasses.join(', ')}`;
        }
      }
      
      // 브랜드 감지 컨텍스트 추가
      const brandResult = detectBrandAndProductAdvanced(text);
      let brandContext = "";
      if (brandResult.brand && brandResult.product) {
        brandContext = `\n\n중요: 텍스트에서 '${brandResult.brand} ${brandResult.product}' 브랜드/제품이 직접 탐지되었습니다. 이를 최우선으로 고려하세요.`;
      } else if (brandResult.brand) {
        brandContext = `\n\n중요: 텍스트에서 '${brandResult.brand}' 브랜드가 탐지되었습니다.`;
      }

      // 4단계 추론 시스템에 맞춘 프롬프트
      const prompt = `식품의 포장지를 OCR로 추출한 텍스트를 분석해서 어떤 식품인지 추론해주세요.

추출된 텍스트: ${text}${brandContext}${detectionContext}

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
        // 할당량 초과 시 4단계 fallback 사용
        console.log(`⚠️ Gemini API 할당량 초과 (429) - 4단계 fallback 진행`);
        const fallbackResult = performAdvancedFallback(text);
        console.log(`🔄 4단계 fallback 완료: ${fallbackResult}`);
        return fallbackResult;
      }
      
      console.log(`❌ Gemini API 오류 - 상태 코드: ${response.status}`);
      
      // 4단계: API 실패 시 고급 fallback
      const fallbackResult = performAdvancedFallback(text);
      console.log(`🔄 4단계 API 실패 fallback: ${fallbackResult}`);
      return fallbackResult;
      
    } catch (error) {
      console.error(`❌ Gemini API 분석 중 오류 발생: ${error}`);
      
      // 4단계: 오류 시에도 고급 fallback
      const fallbackResult = performAdvancedFallback(text);
      console.log(`🔄 4단계 오류 fallback: ${fallbackResult}`);
      return fallbackResult;
    }
  };

  // Gemini 결과에서 식품명 추출 (4단계 시스템용)
  const extractFoodNameFromGeminiResult = (resultText, originalText) => {
    if (!resultText) {
      // Gemini 결과가 없으면 4단계 fallback 사용
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

  // 간단한 텍스트 추론 함수 (수정됨)
  const performSimpleTextInference = (text) => {
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

  // 식재료 기반 분류 함수 (fallback용)
  const classifyByIngredientsOnly = (text) => {
    const foundIngredients = extractIngredientsFromText(text);
    
    return {
      found_ingredients: foundIngredients,
      predicted_category: foundIngredients.length > 0 ? foundIngredients[0].name : null,
      confidence: foundIngredients.length > 0 ? 0.8 : 0.0
    };
  };

  // Detection 결과의 번역을 캐시하는 함수
  const getOrTranslateDetection = async (englishName) => {
    if (detectionTranslations[englishName]) {
      return detectionTranslations[englishName];
    }
    
    const translated = await translateDetectionResultWithGemini(englishName);
    setDetectionTranslations(prev => ({
      ...prev,
      [englishName]: translated
    }));
    
    return translated;
  };

  // 식재료 관련 영어 단어들 (detection 결과 번역용)
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
    'pumpkin': '호박'
  };

  // 아이콘 컴포넌트들 (FatSecret 관련 추가)
  const CookingIcon = () => <span className="text-2xl md:text-3xl">👨‍🍳</span>;
  const EatingIcon = () => <span className="text-2xl md:text-3xl">🍽️</span>;
  const UploadIcon = () => <span className="text-sm">📁</span>;
  const EyeIcon = () => <span className="text-sm">👁️</span>;
  const BrainIcon = () => <span className="text-sm">🧠</span>;
  const FileTextIcon = () => <span className="text-sm">📄</span>;
  const FridgeIcon = () => <span className="text-lg md:text-xl">🧊</span>;
  const BackIcon = () => <span className="text-sm">←</span>;
  const PlusIcon = () => <span className="text-sm">+</span>;
  const MinusIcon = () => <span className="text-sm">-</span>;
  const DeleteIcon = () => <span className="text-sm">🗑️</span>;
  const SaveIcon = () => <span className="text-sm">💾</span>;
  const CheckIcon = () => <span className="text-sm">✅</span>;
  const CloseIcon = () => <span className="text-sm">✕</span>;
  const EditIcon = () => <span className="text-sm">✏️</span>;
  const AllIcon = () => <span className="text-sm">🔄</span>;
  const FatSecretIcon = () => <span className="text-sm">🔍</span>;
  const DashboardIcon = () => <span className="text-sm">📊</span>;
  const NutritionIcon = () => <span className="text-sm">🥗</span>;
  const LinkIcon = () => <span className="text-sm">🔗</span>;
  const LoadingSpinner = () => (
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
  );

  // useEffect hooks (FatSecret 관련 추가)
  useEffect(() => {
    return () => {
      if (analysisTimeoutRef.current) {
        clearTimeout(analysisTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (showManualAdd && manualInputRef.current) {
      manualInputRef.current.focus();
    }
  }, [showManualAdd]);

  // 컴포넌트 마운트 시 대시보드 데이터 불러오기
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Gemini를 활용한 Detection 결과 번역 및 식재료 판별 함수
  const translateDetectionResultWithGemini = async (englishName) => {
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
        
        // 결과 정리
        const cleanResult = result.replace(/[^\가-힣a-zA-Z_]/g, '').trim();
        
        if (cleanResult === 'NOT_FOOD' || cleanResult === 'NOTFOOD') {
          console.log(`❌ "${englishName}" → 식재료 아님`);
          return null; // 식재료가 아님
        }
        
        if (cleanResult && cleanResult !== englishName && /[가-힣]/.test(cleanResult)) {
          console.log(`✅ "${englishName}" → "${cleanResult}"`);
          return cleanResult; // 한국어 번역 결과
        }
        
        // Gemini가 영어 그대로 반환했거나 애매한 경우 기본 사전 확인
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
  };

  // 기본 식재료 사전 확인 (fallback)
  const checkBasicFoodDictionary = (englishName) => {
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

  // 식재료 관리 함수들
  const updateIngredientQuantity = (id, newQuantity) => {
    if (newQuantity < 0) return;
    setFridgeIngredients(prev => 
      prev.map(ingredient => 
        ingredient.id === id 
          ? { ...ingredient, quantity: newQuantity }
          : ingredient
      )
    );
  };

  const removeIngredient = (id) => {
    setFridgeIngredients(prev => 
      prev.filter(ingredient => ingredient.id !== id)
    );
  };

  const addManualIngredient = () => {
    const ingredientName = manualIngredientName.trim();
    
    if (!ingredientName) {
      alert('식재료 이름을 입력해주세요.');
      return;
    }

    if (manualIngredientQuantity < 1) {
      alert('수량은 1개 이상이어야 합니다.');
      return;
    }

    setIsAddingManual(true);

    const existingIngredient = fridgeIngredients.find(item => 
      item.name.trim().toLowerCase() === ingredientName.toLowerCase()
    );

    if (existingIngredient) {
      setFridgeIngredients(prev => 
        prev.map(ingredient => 
          ingredient.id === existingIngredient.id
            ? { ...ingredient, quantity: ingredient.quantity + manualIngredientQuantity }
            : ingredient
        )
      );
      setStatusMessage(`✅ ${ingredientName} 수량이 ${manualIngredientQuantity}개 추가되었습니다.`);
    } else {
      const maxId = fridgeIngredients.length > 0 ? Math.max(...fridgeIngredients.map(item => item.id)) : 0;
      const newIngredient = {
        id: maxId + 1,
        name: ingredientName,
        quantity: manualIngredientQuantity,
        confidence: 1.0,
        source: 'manual'
      };

      setFridgeIngredients(prev => [...prev, newIngredient]);
      setStatusMessage(`✅ ${ingredientName} ${manualIngredientQuantity}개가 추가되었습니다.`);
    }

    setShowSaveButton(true);
    setManualIngredientName('');
    setManualIngredientQuantity(1);
    setShowManualAdd(false);
    setIsAddingManual(false);

    setTimeout(() => {
      setStatusMessage('식재료가 추가되었습니다.');
    }, 3000);
  };

  const closeManualAdd = () => {
    setShowManualAdd(false);
    setManualIngredientName('');
    setManualIngredientQuantity(1);
  };

  const handleManualInputKeyPress = (e) => {
    if (e.key === 'Enter') {
      addManualIngredient();
    }
  };

  // 저장/불러오기 함수들
  const saveToMongoDB = async () => {
    if (fridgeIngredients.length === 0) {
      setStatusMessage('저장할 식재료가 없습니다.');
      return;
    }

    setIsSaving(true);

    try {
      const saveData = {
        userId: userId,
        ingredients: fridgeIngredients,
        timestamp: new Date().toISOString(),
        totalCount: fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0),
        totalTypes: fridgeIngredients.length
      };

      const saveResponse = await fetch(`${API_BASE_URL}/api/fridge/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveData),
      });

      if (saveResponse.ok) {
        const result = await saveResponse.json();
        setStatusMessage(`✅ 냉장고 데이터가 성공적으로 저장되었습니다! (총 ${fridgeIngredients.length}종류)`);
        setShowSaveButton(false);
        
        setTimeout(() => {
          setStatusMessage('저장 완료');
        }, 3000);
      } else {
        const errorData = await saveResponse.json();
        throw new Error(errorData.message || '저장 실패');
      }
    } catch (error) {
      console.error('❌ MongoDB 저장 실패:', error);
      
      try {
        const localData = {
          userId: userId,
          ingredients: fridgeIngredients,
          timestamp: new Date().toISOString(),
          totalCount: fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0),
          totalTypes: fridgeIngredients.length
        };
        
        setStatusMessage(`📱 로컬에 저장되었습니다 (총 ${fridgeIngredients.length}종류) - 서버 연결 실패`);
        setShowSaveButton(false);
      } catch (localError) {
        setStatusMessage(`❌ 저장 실패: ${error.message}`);
      }
    } finally {
      setIsSaving(false);
    }
  };

  // 버전3 데이터를 현재 형식으로 변환하는 함수
  const convertV3DataToCurrentFormat = (v3Data) => {
    if (!v3Data || !Array.isArray(v3Data)) {
      return [];
    }

    return v3Data.map((item, index) => {
      // 다양한 버전3 데이터 형식을 현재 형식으로 변환
      const convertedItem = {
        id: item.id || (Date.now() + index),
        name: item.name || item.ingredient || item.food || item.foodName || '알 수 없는 식재료',
        quantity: item.quantity || item.count || item.amount || 1,
        confidence: item.confidence || item.certainty || 0.8,
        source: item.source || 'v3_migration'
      };

      // 텍스트만 있는 경우 처리
      if (typeof item === 'string') {
        convertedItem.name = item;
        convertedItem.id = Date.now() + index;
        convertedItem.quantity = 1;
        convertedItem.confidence = 0.7;
        convertedItem.source = 'v3_text_migration';
      }

      return convertedItem;
    });
  };

  // 버전3 데이터 불러오기 (404 시 자동으로 로컬 스토리지 확인)
  const loadFromV3Data = async () => {
    try {
      setStatusMessage('📥 버전3 서버 데이터를 확인하는 중...');
      
      // 먼저 현재 API를 통해 일반 데이터 확인
      const loadResponse = await fetch(`${API_BASE_URL}/api/fridge/load/${userId}`);

      if (loadResponse.ok) {
        const result = await loadResponse.json();
        
        if (result.success && result.ingredients && result.ingredients.length > 0) {
          // 기존 데이터가 있으면 사용할지 물어보기
          const shouldUse = window.confirm(`서버에 ${result.ingredients.length}개의 식재료 데이터가 있습니다.\n이 데이터를 불러오시겠습니까?\n\n확인: 서버 데이터 사용\n취소: 로컬 버전3 데이터 찾기`);
          
          if (shouldUse) {
            setFridgeIngredients(result.ingredients);
            setStatusMessage(`📥 서버 데이터를 불러왔습니다 (${result.ingredients.length}개 항목)`);
            setShowSaveButton(false);
            return;
          }
        }
      }
      
      // 서버에 데이터가 없거나 사용자가 거부한 경우 로컬 스토리지 확인
      setStatusMessage('📥 버전3 API가 없습니다. 로컬 데이터를 자동으로 확인합니다...');
      setTimeout(() => {
        loadFromV3LocalStorage();
      }, 1000);
      
    } catch (error) {
      console.error('❌ 서버 연결 실패:', error);
      
      // 네트워크 오류나 서버 오류 시에도 로컬 스토리지 확인
      setStatusMessage('❌ 서버 연결 실패. 로컬 버전3 데이터를 확인합니다...');
      setTimeout(() => {
        loadFromV3LocalStorage();
      }, 1000);
    }
  };

  // 로컬 스토리지에서 버전3 데이터 불러오기 (백엔드가 없는 경우)
  const loadFromV3LocalStorage = () => {
    try {
      setStatusMessage('📥 로컬 버전3 데이터를 확인하는 중...');
      
      // 버전3에서 사용했을 가능성이 있는 로컬 스토리지 키들
      const possibleKeys = [
        'foodDetectionData',
        'fridgeIngredients',
        'savedIngredients',
        `fridge_${userId}`,
        'fridge_data_v3',
        'ingredients',
        'food_list',
        'detected_foods',
        'analyzed_results',
        // 날짜별로 저장되었을 수도 있음
        `fridge_data_${new Date().getFullYear()}`,
        `ingredients_${new Date().getFullYear()}`
      ];

      let foundData = null;
      let usedKey = null;
      let totalChecked = 0;

      for (const key of possibleKeys) {
        const stored = localStorage.getItem(key);
        totalChecked++;
        
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            
            // 배열인 경우
            if (Array.isArray(parsed) && parsed.length > 0) {
              foundData = parsed;
              usedKey = key;
              break;
            }
            
            // 객체에 ingredients 속성이 있는 경우
            if (parsed && typeof parsed === 'object') {
              if (parsed.ingredients && Array.isArray(parsed.ingredients)) {
                foundData = parsed.ingredients;
                usedKey = key + '.ingredients';
                break;
              }
              if (parsed.data && Array.isArray(parsed.data)) {
                foundData = parsed.data;
                usedKey = key + '.data';
                break;
              }
              if (parsed.items && Array.isArray(parsed.items)) {
                foundData = parsed.items;
                usedKey = key + '.items';
                break;
              }
            }
          } catch (parseError) {
            console.warn(`로컬 스토리지 키 "${key}" 파싱 실패:`, parseError);
          }
        }
      }

      if (foundData) {
        const convertedData = convertV3DataToCurrentFormat(foundData);
        
        // 기존 데이터와 병합할지 물어보기
        const shouldMerge = fridgeIngredients.length > 0 && 
          window.confirm(`현재 냉장고에 ${fridgeIngredients.length}개의 식재료가 있습니다. 버전3 데이터(${convertedData.length}개)와 병합하시겠습니까?\n\n확인: 병합\n취소: 덮어쓰기`);
        
        if (shouldMerge) {
          // 중복 제거하면서 병합
          const mergedData = [...fridgeIngredients];
          let addedCount = 0;
          
          convertedData.forEach(newItem => {
            const existingIndex = mergedData.findIndex(existing => 
              existing.name.toLowerCase() === newItem.name.toLowerCase()
            );
            
            if (existingIndex !== -1) {
              // 기존 항목의 수량 증가
              mergedData[existingIndex].quantity += newItem.quantity;
            } else {
              // 새 항목 추가
              mergedData.push({
                ...newItem,
                id: Date.now() + Math.random()
              });
              addedCount++;
            }
          });
          
          setFridgeIngredients(mergedData);
          setStatusMessage(`📥 버전3 데이터를 병합했습니다! (${addedCount}개 새로 추가, 키: ${usedKey})`);
        } else {
          setFridgeIngredients(convertedData);
          setStatusMessage(`📥 버전3 데이터를 불러왔습니다! (${convertedData.length}개 항목, 키: ${usedKey})`);
        }
        
        setShowSaveButton(true);
        
        console.log(`✅ 버전3 데이터 로드 성공:`, {
          usedKey,
          originalData: foundData,
          convertedData,
          totalKeysChecked: totalChecked
        });
        
      } else {
        setStatusMessage(`❌ 로컬 스토리지에서 버전3 데이터를 찾을 수 없습니다. (${totalChecked}개 키 확인됨)`);
        
        // 디버깅을 위해 모든 로컬 스토리지 키 출력
        console.log('🔍 확인된 로컬 스토리지 키들:', Object.keys(localStorage));
      }
    } catch (error) {
      console.error('❌ 로컬 버전3 데이터 로드 실패:', error);
      setStatusMessage('❌ 로컬 버전3 데이터 불러오기에 실패했습니다.');
    }
  };

  const loadFromMongoDB = async () => {
    try {
      const loadResponse = await fetch(`${API_BASE_URL}/api/fridge/load/${userId}`);

      if (loadResponse.ok) {
        const result = await loadResponse.json();
        
        if (result.ingredients && result.ingredients.length > 0) {
          setFridgeIngredients(result.ingredients);
          setStatusMessage(`📥 저장된 데이터를 불러왔습니다 (${result.totalTypes}종류, ${result.totalCount}개)`);
          setShowSaveButton(false);
        } else {
          setStatusMessage('저장된 데이터가 없습니다.');
        }
      } else {
        throw new Error('데이터 로드 실패');
      }
    } catch (error) {
      console.error('❌ MongoDB 로드 실패:', error);
      setStatusMessage('저장된 데이터가 없습니다.');
    }
  };

  const addToFridge = (newIngredients) => {
    setFridgeIngredients(prevIngredients => {
      const updatedIngredients = [...prevIngredients];
      let maxId = updatedIngredients.length > 0 ? Math.max(...updatedIngredients.map(item => item.id)) : 0;

      newIngredients.forEach(newItem => {
        const existingItemIndex = updatedIngredients.findIndex(item => 
          item.name.trim().toLowerCase() === newItem.name.trim().toLowerCase()
        );

        if (existingItemIndex !== -1) {
          const oldQuantity = updatedIngredients[existingItemIndex].quantity;
          updatedIngredients[existingItemIndex] = {
            ...updatedIngredients[existingItemIndex],
            quantity: oldQuantity + newItem.quantity,
            confidence: Math.max(
              updatedIngredients[existingItemIndex].confidence || 0, 
              newItem.confidence || 0
            ),
            source: newItem.source || updatedIngredients[existingItemIndex].source
          };
        } else {
          const newIngredient = {
            id: ++maxId,
            name: newItem.name.trim(),
            quantity: newItem.quantity,
            confidence: newItem.confidence || 0.8,
            source: newItem.source || 'analysis'
          };
          updatedIngredients.push(newIngredient);
        }
      });
      
      if (updatedIngredients.length > 0) {
        setShowSaveButton(true);
      }
      
      return updatedIngredients;
    });
  };

  // 드래그 앤 드롭 핸들러
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length > 0) {
      processImageFiles(imageFiles);
    } else {
      setStatusMessage('이미지 파일만 업로드 가능합니다.');
    }
  };

  // 이미지 처리 함수들
  const processImageFiles = (files) => {
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
      setStatusMessage('이미지 파일만 업로드 가능합니다.');
      return;
    }

    const processedImages = [];
    let processedCount = 0;

    imageFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        processedImages[index] = {
          id: Date.now() + index,
          file: file,
          dataUrl: e.target.result,
          name: file.name,
          size: file.size,
          processed: false
        };
        
        processedCount++;
        if (processedCount === imageFiles.length) {
          setImages(prev => [...prev, ...processedImages.filter(img => img)]);
          setSelectedImageIndex(images.length);
          setStatusMessage(`✅ ${imageFiles.length}개 이미지가 추가되었습니다.`);
        }
      };
      
      reader.onerror = () => {
        processedCount++;
        if (processedCount === imageFiles.length) {
          const validImages = processedImages.filter(img => img);
          if (validImages.length > 0) {
            setImages(prev => [...prev, ...validImages]);
            setSelectedImageIndex(images.length);
            setStatusMessage(`✅ ${validImages.length}개 이미지가 추가되었습니다.`);
          }
        }
      };
      
      reader.readAsDataURL(file);
    });
  };

  const handleImageLoad = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      processImageFiles(files);
    }
  };

  const removeImage = (imageId) => {
    setImages(prev => {
      const filtered = prev.filter(img => img.id !== imageId);
      if (filtered.length === 0) {
        setSelectedImageIndex(0);
        setStatusMessage('모든 이미지가 삭제되었습니다.');
      } else if (selectedImageIndex >= filtered.length) {
        setSelectedImageIndex(filtered.length - 1);
      }
      return filtered;
    });
    
    setDetectionResults(prev => {
      const newResults = { ...prev };
      delete newResults[imageId];
      return newResults;
    });
    
    setOcrResults(prev => {
      const newResults = { ...prev };
      delete newResults[imageId];
      return newResults;
    });
    
    setGeminiResults(prev => {
      const newResults = { ...prev };
      delete newResults[imageId];
      return newResults;
    });
  };

  // FatSecret 포함 개선된 고급 분석 함수
  const analyzeImageAdvanced = async (imageIndex) => {
    if (imageIndex < 0 || imageIndex >= images.length) {
      setStatusMessage('유효하지 않은 이미지입니다.');
      return;
    }

    const image = images[imageIndex];
    if (!image || !image.file) {
      setStatusMessage('이미지 파일이 없습니다.');
      return;
    }

    if (isProcessing) {
      return;
    }

    setIsProcessing(true);
    setProcessingImageIndex(imageIndex);

    try {
      setProcessingStep(`이미지 ${imageIndex + 1} 4단계 추론 + FatSecret 분석 중...`);
      setStatusMessage(`이미지 ${imageIndex + 1} 4단계 추론 + FatSecret 분석 중...`);

      let finalIngredients = [];
      let detectionResult = null;
      let ocrResult = null;

      // 1단계: OCR API 호출 (우선순위 1)
      setProcessingStep(`1/4 - 텍스트 추출 중...`);
      const ocrFormData = new FormData();
      ocrFormData.append('file', image.file);

      try {
        const ocrResponse = await fetch(`${API_BASE_URL}/api/ocr`, {
          method: 'POST',
          body: ocrFormData,
        });

        if (ocrResponse.ok) {
          ocrResult = await ocrResponse.json();
          setOcrResults(prev => ({
            ...prev,
            [image.id]: ocrResult
          }));
          console.log(`📄 OCR 결과: "${ocrResult.text || '텍스트 없음'}"`);
        }
      } catch (error) {
        console.error('OCR 실패:', error);
      }

      // 2단계: Detection API 호출 (backup)
      setProcessingStep(`2/4 - 객체 탐지 중...`);
      const detectFormData = new FormData();
      detectFormData.append('file', image.file);
      detectFormData.append('confidence', confidence);

      try {
        const detectResponse = await fetch(`${API_BASE_URL}/api/detect`, {
          method: 'POST',
          body: detectFormData,
        });

        if (detectResponse.ok) {
          detectionResult = await detectResponse.json();
          setDetectionResults(prev => ({
            ...prev,
            [image.id]: detectionResult
          }));
          console.log(`🎯 Detection 결과: ${detectionResult.detections?.length || 0}개 탐지`);
        }
      } catch (error) {
        console.error('Detection 실패:', error);
      }

      // 3단계: 4단계 추론 시스템 + FatSecret 검색 + 대시보드 업로드
      setProcessingStep(`3/4 - 4단계 추론 시스템 적용 중...`);
      
      const hasOcrText = ocrResult && ocrResult.text && ocrResult.text.trim().length > 0;
      const hasDetectionResults = detectionResult && detectionResult.detections && detectionResult.detections.length > 0;
      
      console.log(`📊 FatSecret 포함 4단계 추론 시스템:`);
      console.log(`  📄 OCR 텍스트 존재: ${hasOcrText ? 'YES' : 'NO'}`);
      console.log(`  🎯 Detection 결과 존재: ${hasDetectionResults ? 'YES' : 'NO'}`);
      console.log(`  🔍 FatSecret 검색 활성화: ${fatSecretSearchEnabled ? 'YES' : 'NO'}`);
      
      if (hasOcrText) {
        // OCR 텍스트가 있으면 4단계 추론 + FatSecret 적용
        console.log(`🚀 OCR 우선 모드 - 4단계 추론 + FatSecret 시스템 적용`);
        
        try {
          console.log(`📄 OCR 텍스트 분석: "${ocrResult.text}"`);
          
          // 4단계 추론 + FatSecret 검색 + 대시보드 업로드 통합 실행
          const comprehensiveResult = await performInferenceWithFatSecret(ocrResult.text, image.id);

          if (comprehensiveResult.foodName) {
            console.log(`✅ 종합 추론 성공: "${comprehensiveResult.foodName}"`);
            
            // Gemini 결과 저장 (FatSecret 정보 포함)
            setGeminiResults(prev => ({
              ...prev,
              [image.id]: {
                text: comprehensiveResult.foodName,
                extractedText: ocrResult.text,
                source: 'ocr_4stage_fatsecret',
                mode: 'OCR 4단계 + FatSecret',
                fatSecretFound: comprehensiveResult.fatSecretResult?.found || false,
                dashboardUploaded: comprehensiveResult.dashboardUploaded
              }
            }));

            // 냉장고에 추가 (FatSecret 영양정보 포함)
            const ingredientData = {
              name: comprehensiveResult.foodName,
              quantity: 1,
              confidence: 0.95,
              source: 'fatsecret_enhanced'
            };

            // FatSecret 영양정보가 있으면 추가
            if (comprehensiveResult.fatSecretResult?.found) {
              ingredientData.nutritionData = comprehensiveResult.fatSecretResult.nutritionData;
              ingredientData.fatSecretUrl = comprehensiveResult.fatSecretResult.fatSecretUrl;
            }

            finalIngredients.push(ingredientData);
            
            console.log(`🥬 OCR 4단계 + FatSecret - 냉장고 추가: "${comprehensiveResult.foodName}"`);
            
            // 대시보드 업로드 결과 메시지
            if (comprehensiveResult.dashboardUploaded) {
              console.log(`📤 대시보드 업로드 완료: "${comprehensiveResult.foodName}"`);
            }
          } else {
            console.log(`❌ OCR 기반 종합 추론 실패`);
          }
        } catch (error) {
          console.error('❌ OCR 기반 종합 분석 오류:', error);
        }
        
      } else if (hasDetectionResults) {
        // OCR 텍스트가 없을 때는 Detection만 사용 (FatSecret 제외)
        console.log(`🎯 Detection 전용 모드 - OCR 텍스트 없음 (FatSecret 제외)`);
        
        try {
          // Detection 결과 처리 (신뢰도 50% 이상으로 변경)
          for (let detection of detectionResult.detections.filter(d => d.confidence >= 0.5)) {
            // Detection 결과 번역을 위한 캐시 업데이트
            getOrTranslateDetection(detection.class);
            
            // Gemini를 활용한 식재료 판별 및 번역
            const translatedName = await translateDetectionResultWithGemini(detection.class);
            if (translatedName) {
              finalIngredients.push({
                name: translatedName,
                quantity: 1,
                confidence: detection.confidence,
                source: 'detection'
              });
              console.log(`🥬 Detection 전용 모드 - 냉장고 추가: "${translatedName}"`);
            }
          }
        } catch (error) {
          console.error('❌ Detection 처리 오류:', error);
        }
        
      } else {
        console.log(`❌ OCR, Detection 모두 결과 없음`);
      }

      // 4단계: 결과 처리 및 상태 메시지 업데이트
      setProcessingStep(`4/4 - 결과 처리 완료`);
      
      if (finalIngredients.length > 0) {
        addToFridge(finalIngredients);
        
        // 결과 타입에 따른 메시지
        const analysisMode = hasOcrText ? 'OCR 4단계 + FatSecret' : 'Detection 전용';
        const fatSecretStatus = hasOcrText && fatSecretSearchEnabled ? ' (FatSecret 검색 포함)' : '';
        
        setStatusMessage(`✅ 이미지 ${imageIndex + 1} ${analysisMode} 분석 완료: ${finalIngredients.length}개 식재료 추가${fatSecretStatus}`);
        console.log(`✅ ${analysisMode} 분석 완료: ${finalIngredients.map(item => item.name).join(', ')}`);
        
        setImages(prev => prev.map((img, idx) => 
          idx === imageIndex ? { ...img, processed: true } : img
        ));
      } else {
        const analysisMode = hasOcrText ? 'OCR 4단계 + FatSecret' : hasDetectionResults ? 'Detection' : '분석';
        setStatusMessage(`❌ 이미지 ${imageIndex + 1}: ${analysisMode} 결과에서 식재료를 찾을 수 없습니다.`);
        console.log(`❌ 이미지 ${imageIndex + 1}: ${analysisMode} 분석 결과 없음`);
      }

    } catch (error) {
      console.error('4단계 추론 + FatSecret 시스템 분석 오류:', error);
      setStatusMessage(`❌ 이미지 ${imageIndex + 1} 종합 분석 중 오류가 발생했습니다.`);
    } finally {
      setIsProcessing(false);
      setProcessingImageIndex(-1);
      setProcessingStep('');
    }
  };

  const analyzeAllImages = async () => {
    if (images.length === 0) {
      setStatusMessage('분석할 이미지가 없습니다.');
      return;
    }

    if (isProcessing) {
      return;
    }

    setIsProcessing(true);
    
    try {
      if (clearBeforeAnalysis) {
        setFridgeIngredients([]);
      }

      const analysisMode = fatSecretSearchEnabled ? '4단계 추론 + FatSecret' : '4단계 추론';
      setStatusMessage(`전체 ${images.length}개 이미지 ${analysisMode} 일괄 분석을 시작합니다...`);
      
      for (let i = 0; i < images.length; i++) {
        if (!images[i].processed) {
          await analyzeImageAdvanced(i);
          if (i < images.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      }
      
      const completionMessage = fatSecretSearchEnabled 
        ? `✅ 전체 4단계 추론 + FatSecret 일괄 분석 완료! (대시보드 확인)` 
        : `✅ 전체 4단계 추론 일괄 분석 완료!`;
      
      setStatusMessage(completionMessage);

    } catch (error) {
      console.error('종합 일괄 분석 오류:', error);
      setStatusMessage('❌ 종합 일괄 분석 중 오류가 발생했습니다.');
    } finally {
      setIsProcessing(false);
      setProcessingImageIndex(-1);
      setProcessingStep('');
    }
  };

  const testServerConnection = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        const result = await response.json();
        setStatusMessage('서버 연결 성공');
      } else {
        setStatusMessage(`서버 응답 오류: ${response.status}`);
      }
    } catch (error) {
      setStatusMessage(`서버 연결 실패: ${error.message}`);
    }
  };

  // 렌더링 - 바로 해먹기 모드 화면
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="w-full max-w-sm md:max-w-2xl lg:max-w-4xl xl:max-w-6xl mx-auto p-3 md:p-6 lg:p-8">
        
        {/* 헤더 */}
        <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6 mb-4 md:mb-6">
          <div className="flex items-center gap-3 md:gap-4 mb-3">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl p-2 md:p-3 text-white">
              <CookingIcon />
            </div>
            <div className="flex-1">
              <h1 className="text-lg md:text-xl lg:text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                스마트 푸드 매니저 v12 (4단계 + FatSecret)
              </h1>
              <p className="text-xs md:text-sm text-gray-600">
                4단계 추론 + FatSecret 검색 + 영양정보 대시보드
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
          {/* 왼쪽 컬럼 */}
          <div className="space-y-4 md:space-y-6">
            {/* 액션 버튼들 */}
            <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6">
              <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageLoad}
                  ref={fileInputRef}
                  className="hidden"
                  multiple
                />
                
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                >
                  <UploadIcon />
                  <span>업로드</span>
                </button>

                <button
                  onClick={analyzeAllImages}
                  disabled={images.length === 0 || isProcessing}
                  className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {isProcessing && processingImageIndex === -1 ? <LoadingSpinner /> : <AllIcon />}
                  <span>전체 분석</span>
                </button>
              </div>

              {/* 냉장고 저장 및 불러오기 버튼들 */}
              {showSaveButton && (
                <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6 p-3 md:p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl">
                  <button
                    onClick={saveToMongoDB}
                    disabled={isSaving || fridgeIngredients.length === 0}
                    className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {isSaving ? <LoadingSpinner /> : <SaveIcon />}
                    <span className="text-xs md:text-sm">
                      {isSaving ? '저장 중...' : `저장 (${fridgeIngredients.length})`}
                    </span>
                  </button>

                  <button
                    onClick={loadFromMongoDB}
                    className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                  >
                    <CheckIcon />
                    <span className="text-xs md:text-sm">불러오기</span>
                  </button>
                </div>
              )}

              {/* 버전3 데이터 불러오기 버튼들 */}
              <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6 p-3 md:p-4 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl">
                <div className="col-span-2 mb-2">
                  <div className="text-xs md:text-sm text-purple-700 font-medium text-center">
                    🔄 버전3에서 저장된 데이터 불러오기
                  </div>
                  <div className="text-xs text-purple-600 text-center mt-1">
                    이전 버전의 냉장고 데이터를 현재 형식으로 변환하여 불러옵니다
                  </div>
                </div>
                
                <button
                  onClick={loadFromV3Data}
                  className="flex items-center justify-center gap-2 py-2 md:py-3 px-3 md:px-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg font-semibold text-xs md:text-sm transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                >
                  <span className="text-xs">📦</span>
                  <span>V3 서버</span>
                </button>

                <button
                  onClick={loadFromV3LocalStorage}
                  className="flex items-center justify-center gap-2 py-2 md:py-3 px-3 md:px-4 bg-gradient-to-r from-pink-500 to-pink-600 text-white rounded-lg font-semibold text-xs md:text-sm transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                >
                  <span className="text-xs">💾</span>
                  <span>V3 로컬</span>
                </button>
              </div>

              {/* 분석 전 설정 옵션들 */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={clearBeforeAnalysis}
                      onChange={(e) => setClearBeforeAnalysis(e.target.checked)}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-xs md:text-sm text-gray-700 font-medium">분석 전 초기화</span>
                  </label>
                </div>
                
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={fatSecretSearchEnabled}
                      onChange={(e) => setFatSecretSearchEnabled(e.target.checked)}
                      className="w-4 h-4 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500"
                    />
                    <FatSecretIcon />
                    <span className="text-xs md:text-sm text-gray-700 font-medium">FatSecret 검색 활성화</span>
                  </label>
                </div>
                
                {fatSecretSearchEnabled && (
                  <div className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded font-medium">
                    ✅ 영양정보 자동 검색 및 대시보드 업로드 활성화
                  </div>
                )}
              </div>
            </div>

            {/* 이미지 갤러리 */}
            {images.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6">
                <div className="flex items-center justify-between mb-3 md:mb-4">
                  <h3 className="text-sm md:text-base font-bold text-gray-800">
                    업로드된 이미지 ({images.length}개)
                  </h3>
                  <button
                    onClick={() => setImages([])}
                    className="text-xs md:text-sm text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1 rounded-lg transition-all duration-200 font-medium"
                  >
                    전체 삭제
                  </button>
                </div>
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 gap-2 md:gap-3 max-h-32 md:max-h-40 overflow-y-auto bg-gray-50 p-2 md:p-3 rounded-xl">
                  {images.map((image, index) => (
                    <div
                      key={image.id}
                      className={`relative cursor-pointer rounded-lg border-2 overflow-hidden transition-all duration-300 ${
                        selectedImageIndex === index 
                          ? 'border-blue-500 ring-2 ring-blue-200 shadow-lg scale-105' 
                          : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
                      } ${
                        processingImageIndex === index ? 'ring-2 ring-green-300' : ''
                      }`}
                      onClick={() => setSelectedImageIndex(index)}
                    >
                      <img
                        src={image.dataUrl}
                        alt={`업로드 ${index + 1}`}
                        className="w-full h-16 md:h-20 object-cover"
                      />
                      <div className="absolute top-1 left-1 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-xs px-1 py-0.5 rounded font-bold">
                        {index + 1}
                      </div>
                      {image.processed && (
                        <div className="absolute top-1 right-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs px-1 py-0.5 rounded font-bold">
                          ✓
                        </div>
                      )}
                      {processingImageIndex === index && (
                        <div className="absolute inset-0 bg-green-500 bg-opacity-40 flex items-center justify-center backdrop-blur-sm">
                          <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        </div>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeImage(image.id);
                        }}
                        className="absolute bottom-1 right-1 bg-red-500 text-white text-xs w-4 h-4 rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 메인 이미지 표시 영역 */}
            <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6">
              <div 
                className={`border-2 border-dashed rounded-2xl min-h-[200px] md:min-h-[300px] lg:min-h-[400px] flex items-center justify-center transition-all duration-300 cursor-pointer ${
                  isDragOver 
                    ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg' 
                    : 'border-gray-300 hover:border-blue-400 hover:bg-gradient-to-br hover:from-blue-50 hover:to-indigo-50 hover:shadow-md'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                {images.length > 0 && selectedImageIndex >= 0 && images[selectedImageIndex] ? (
                  <div className="w-full h-full flex flex-col">
                    <div className="flex-1 flex items-center justify-center p-2 md:p-4">
                      <img
                        src={images[selectedImageIndex].dataUrl}
                        alt={`선택된 이미지 ${selectedImageIndex + 1}`}
                        className="max-w-full max-h-full rounded-xl object-contain shadow-lg"
                        style={{ maxHeight: '300px' }}
                      />
                    </div>
                    <div className="mt-2 md:mt-4 text-center bg-gradient-to-r from-blue-50 to-indigo-50 p-2 md:p-3 rounded-xl">
                      <p className="text-xs md:text-sm font-semibold text-gray-700">
                        이미지 {selectedImageIndex + 1} / {images.length}
                        {images[selectedImageIndex].processed && (
                          <span className="ml-2 text-green-600 font-bold">✓ 분석완료</span>
                        )}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 p-6 md:p-8">
                    <div className="text-4xl md:text-6xl mb-3 md:mb-4">🧊</div>
                    <p className="text-sm md:text-base font-bold mb-1 md:mb-2">
                      {isDragOver ? '파일을 놓아주세요' : '냉장고 사진 업로드'}
                    </p>
                    <p className="text-xs md:text-sm text-gray-400">
                      {isDragOver ? '' : '여러 이미지 선택 가능 - 4단계 추론 + FatSecret 영양정보'}
                    </p>
                  </div>
                )}
              </div>

              {/* 진행 상태 */}
              {isProcessing && (
                <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-3 md:p-4">
                  <div className="flex items-center gap-2">
                    <LoadingSpinner />
                    <span className="text-blue-800 text-xs md:text-sm font-bold">{processingStep}</span>
                  </div>
                  {processingImageIndex >= 0 && (
                    <div className="mt-1 text-xs md:text-sm text-blue-600 font-semibold">
                      처리 중: {processingImageIndex + 1} / {images.length}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 오른쪽 컬럼 */}
          <div className="space-y-4 md:space-y-6">
            {/* 냉장고 속 식재료 */}
            <div className="bg-white rounded-2xl shadow-lg border border-blue-100">
              <div className="p-4 md:p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-3 md:mb-4">
                  <div className="flex items-center gap-2 md:gap-3">
                    <div className="p-1 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-lg">
                      <FridgeIcon />
                    </div>
                    <h3 className="text-lg md:text-xl font-bold text-gray-800">냉장고 식재료</h3>
                  </div>
                  <div className="flex items-center gap-2 md:gap-3">
                    <button
                      onClick={() => setShowManualAdd(true)}
                      className="flex items-center gap-1 px-3 py-1.5 md:px-4 md:py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-xs md:text-sm rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg"
                    >
                      <EditIcon />
                      <span>추가</span>
                    </button>
                    <button
                      onClick={() => setFridgeIngredients([])}
                      className="text-xs md:text-sm text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1.5 rounded-lg transition-all duration-200 font-medium"
                    >
                      전체삭제
                    </button>
                  </div>
                </div>
                <div className="text-xs md:text-sm text-gray-500 font-medium bg-gray-50 px-2 py-1 rounded inline-block">
                  총 {fridgeIngredients.length}개 종류
                </div>
              </div>
              <div className="p-4 md:p-6" style={{ minHeight: '200px', maxHeight: '400px', overflowY: 'auto' }}>
                {fridgeIngredients.length > 0 ? (
                  <div className="space-y-3 md:space-y-4">
                    {fridgeIngredients.map((ingredient) => (
                      <div key={ingredient.id} className="bg-gradient-to-r from-blue-50 via-white to-indigo-50 border-2 border-gray-200 rounded-xl p-3 md:p-4 transition-all duration-300 hover:shadow-lg hover:scale-105 hover:border-blue-300">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-bold text-gray-800 text-sm md:text-base">{ingredient.name}</h4>
                          <button
                            onClick={() => removeIngredient(ingredient.id)}
                            className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded-full p-1 transition-all duration-200"
                          >
                            <DeleteIcon />
                          </button>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 md:gap-4">
                            <button
                              onClick={() => updateIngredientQuantity(ingredient.id, ingredient.quantity - 1)}
                              disabled={ingredient.quantity <= 1}
                              className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-r from-red-100 to-red-200 text-red-600 hover:from-red-200 hover:to-red-300 disabled:from-gray-100 disabled:to-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold text-sm"
                            >
                              <MinusIcon />
                            </button>
                            
                            <div className="flex flex-col items-center bg-white rounded-lg p-2 md:p-3 shadow-sm border border-gray-200">
                              <span className="text-lg md:text-xl font-bold text-blue-600">{ingredient.quantity}</span>
                              <span className="text-xs text-gray-500 font-medium">개</span>
                            </div>
                            
                            <button
                              onClick={() => updateIngredientQuantity(ingredient.id, ingredient.quantity + 1)}
                              className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-r from-green-100 to-green-200 text-green-600 hover:from-green-200 hover:to-green-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold text-sm"
                            >
                              <PlusIcon />
                            </button>
                          </div>
                          
                          <div className="text-xs text-gray-500 bg-white bg-opacity-80 px-2 py-1 rounded-lg font-semibold border border-gray-200">
                            {ingredient.source === 'manual' && '✏️'}
                            {ingredient.source === 'detection' && '🎯'}
                            {ingredient.source === '4stage_ocr' && '🚀'}
                            {ingredient.source === 'fatsecret_enhanced' && '🔍'}
                            {ingredient.source === 'gemini' && '🧠'}
                            {ingredient.confidence && (
                              <span className="ml-1 text-green-600 font-bold">
                                {(ingredient.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                            {ingredient.nutritionData && (
                              <span className="ml-1 text-blue-600 font-bold">🥗</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    <div className="text-4xl md:text-6xl mb-4">🥬</div>
                    <h4 className="text-lg md:text-xl font-bold mb-2">냉장고가 비어있습니다</h4>
                    <p className="text-xs md:text-sm mb-4">냉장고 사진을 분석하거나</p>
                    <button
                      onClick={() => setShowManualAdd(true)}
                      className="inline-flex items-center gap-2 px-4 py-2 md:px-6 md:py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-xs md:text-sm rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg"
                    >
                      <EditIcon />
                      <span>직접 추가하기</span>
                    </button>
                  </div>
                )}
              </div>
              
              {fridgeIngredients.length > 0 && (
                <div className="px-4 py-3 md:px-6 md:py-4 bg-gradient-to-r from-gray-50 to-blue-50 border-t border-gray-200 rounded-b-2xl">
                  <div className="flex items-center justify-between text-xs md:text-sm">
                    <span className="text-gray-600 font-medium">총 수량</span>
                    <span className="font-bold text-gray-800">
                      {fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0)}개
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* 분석 결과 표시 */}
            <div className="bg-white rounded-2xl shadow-lg border border-blue-100 overflow-hidden">
              <div className="p-4 md:p-6">
                {/* 탭 네비게이션 (FatSecret 및 대시보드 탭 추가) */}
                <div className="flex border-b border-gray-200 mb-4 md:mb-6 overflow-x-auto">
                  <button
                    onClick={() => setActiveTab('detection')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'detection'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <EyeIcon />
                    객체탐지
                  </button>
                  <button
                    onClick={() => setActiveTab('ocr')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'ocr'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <FileTextIcon />
                    텍스트추출
                  </button>
                  <button
                    onClick={() => setActiveTab('gemini')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'gemini'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <BrainIcon />
                    AI분석
                  </button>
                  <button
                    onClick={() => setActiveTab('fatsecret')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'fatsecret'
                        ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <FatSecretIcon />
                    FatSecret
                  </button>
                  <button
                    onClick={() => setActiveTab('dashboard')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'dashboard'
                        ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <DashboardIcon />
                    대시보드
                    {dashboardData.length > 0 && (
                      <span className="ml-1 px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-bold">
                        {dashboardData.length}
                      </span>
                    )}
                  </button>
                </div>

                {/* 탭 내용 */}
                <div className="min-h-[150px] md:min-h-[200px]">
                  {activeTab === 'detection' && (
                    <div>
                      <h3 className="text-sm md:text-base font-bold text-gray-800 mb-3 md:mb-4">객체 탐지 결과</h3>
                      {images.length > 0 && selectedImageIndex >= 0 && detectionResults[images[selectedImageIndex]?.id] ? (
                        (() => {
                          const allDetections = detectionResults[images[selectedImageIndex].id].detections || [];
                          const highConfidenceDetections = allDetections.filter(detection => detection.confidence >= 0.5);
                          
                          return (
                            <div className="space-y-2 md:space-y-3">
                              <div className="text-xs md:text-sm text-gray-600 mb-2 bg-blue-50 px-2 py-1 rounded font-medium">
                                이미지 {selectedImageIndex + 1}: 총 {allDetections.length}개 탐지 
                                <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-bold">
                                  신뢰도 50%+ : {highConfidenceDetections.length}개
                                </span>
                              </div>
                              {highConfidenceDetections.length > 0 ? (
                                highConfidenceDetections.map((detection, index) => (
                                  <div key={index} className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs md:text-sm font-bold text-blue-600">
                                        {detection.class}
                                        {detectionTranslations[detection.class] && ` (${detectionTranslations[detection.class]})`}
                                      </span>
                                      <span className="text-xs md:text-sm font-bold px-2 py-0.5 rounded-full bg-gradient-to-r from-green-100 to-emerald-100 text-green-700">
                                        {(detection.confidence * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                  </div>
                                ))
                              ) : allDetections.length > 0 ? (
                                <p className="text-xs md:text-sm text-gray-500 text-center py-6">
                                  신뢰도 50% 이상의 탐지 결과가 없습니다.<br/>
                                  <span className="text-xs text-gray-400">
                                    (전체 {allDetections.length}개 탐지됨, 최고 신뢰도: {Math.max(...allDetections.map(d => d.confidence * 100)).toFixed(1)}%)
                                  </span>
                                </p>
                              ) : (
                                <p className="text-xs md:text-sm text-gray-500 text-center py-6">탐지된 객체가 없습니다.</p>
                              )}
                            </div>
                          );
                        })()
                      ) : (
                        <p className="text-xs md:text-sm text-gray-500 text-center py-6">이미지를 선택하고 분석해주세요.</p>
                      )}
                    </div>
                  )}

                  {activeTab === 'ocr' && (
                    <div>
                      <h3 className="text-sm md:text-base font-bold text-gray-800 mb-3 md:mb-4">텍스트 추출 결과</h3>
                      {images.length > 0 && selectedImageIndex >= 0 && ocrResults[images[selectedImageIndex]?.id] ? (
                        <div className="space-y-3 md:space-y-4">
                          <div className="text-xs md:text-sm text-gray-600 mb-2 bg-blue-50 px-2 py-1 rounded font-medium">
                            이미지 {selectedImageIndex + 1}에서 추출된 텍스트:
                          </div>
                          <div className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                            <p className="text-xs md:text-sm text-gray-800 whitespace-pre-wrap font-medium">
                              {ocrResults[images[selectedImageIndex].id].text || '추출된 텍스트가 없습니다.'}
                            </p>
                          </div>
                          {ocrResults[images[selectedImageIndex].id].confidence && (
                            <div className="text-xs md:text-sm text-gray-600 font-semibold">
                              신뢰도: {(ocrResults[images[selectedImageIndex].id].confidence * 100).toFixed(1)}%
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs md:text-sm text-gray-500 text-center py-6">이미지를 선택하고 OCR 분석을 진행해주세요.</p>
                      )}
                    </div>
                  )}

                  {activeTab === 'gemini' && (
                    <div>
                      <h3 className="text-sm md:text-base font-bold text-gray-800 mb-3 md:mb-4">AI 분석 결과</h3>
                      {images.length > 0 && selectedImageIndex >= 0 && geminiResults[images[selectedImageIndex]?.id] ? (
                        <div className="space-y-3 md:space-y-4">
                          <div className="text-xs md:text-sm text-gray-600 mb-2 bg-blue-50 px-2 py-1 rounded font-medium">
                            이미지 {selectedImageIndex + 1} AI 분석 결과:
                            {geminiResults[images[selectedImageIndex].id].source === 'ocr_4stage_fatsecret' && (
                              <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-bold">
                                🚀 4단계 + FatSecret
                              </span>
                            )}
                            {geminiResults[images[selectedImageIndex].id].source === 'ocr_4stage_inference' && (
                              <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-bold">
                                🚀 4단계 추론
                              </span>
                            )}
                            {geminiResults[images[selectedImageIndex].id].source === 'direct_detection' && (
                              <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                🎯 직접탐지
                              </span>
                            )}
                            {geminiResults[images[selectedImageIndex].id].mode && (
                              <span className="ml-1 text-xs text-gray-500">
                                ({geminiResults[images[selectedImageIndex].id].mode})
                              </span>
                            )}
                          </div>
                          <div className="p-4 md:p-5 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border-2 border-purple-200">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="p-1 bg-purple-100 rounded">
                                <span className="text-sm">🚀</span>
                              </div>
                              <span className="text-xs md:text-sm font-bold text-purple-700">4단계 추론 결과</span>
                              {geminiResults[images[selectedImageIndex].id].fatSecretFound && (
                                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-bold">
                                  🔍 FatSecret 매칭
                                </span>
                              )}
                              {geminiResults[images[selectedImageIndex].id].dashboardUploaded && (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                  📊 대시보드 업로드됨
                                </span>
                              )}
                            </div>
                            <p className="text-sm md:text-base font-bold text-gray-800">
                              {geminiResults[images[selectedImageIndex].id].text}
                            </p>
                          </div>
                          {geminiResults[images[selectedImageIndex].id].extractedText && (
                            <div className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                              <div className="text-xs md:text-sm text-gray-600 mb-1 font-semibold">분석에 사용된 텍스트:</div>
                              <p className="text-xs md:text-sm text-gray-700 font-medium">
                                {geminiResults[images[selectedImageIndex].id].extractedText}
                              </p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs md:text-sm text-gray-500 text-center py-6">이미지를 선택하고 4단계 추론 + FatSecret 분석을 진행해주세요.</p>
                      )}
                    </div>
                  )}

                  {activeTab === 'fatsecret' && (
                    <div>
                      <h3 className="text-sm md:text-base font-bold text-gray-800 mb-3 md:mb-4">FatSecret 검색 결과</h3>
                      {images.length > 0 && selectedImageIndex >= 0 && fatSecretResults[images[selectedImageIndex]?.id] ? (
                        <div className="space-y-3 md:space-y-4">
                          <div className="text-xs md:text-sm text-gray-600 mb-2 bg-green-50 px-2 py-1 rounded font-medium">
                            이미지 {selectedImageIndex + 1} FatSecret 검색 결과:
                          </div>
                          {fatSecretResults[images[selectedImageIndex].id].found ? (
                            <div className="p-4 md:p-5 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border-2 border-green-200">
                              <div className="flex items-center gap-2 mb-3">
                                <div className="p-1 bg-green-100 rounded">
                                  <NutritionIcon />
                                </div>
                                <span className="text-xs md:text-sm font-bold text-green-700">영양정보 발견</span>
                                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-bold">
                                  ✅ 매칭됨
                                </span>
                              </div>
                              <div className="space-y-2">
                                <p className="text-sm md:text-base font-bold text-gray-800">
                                  {fatSecretResults[images[selectedImageIndex].id].nutritionData?.name || 
                                   fatSecretResults[images[selectedImageIndex].id].foodName}
                                </p>
                                {fatSecretResults[images[selectedImageIndex].id].nutritionData && (
                                  <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="bg-white p-2 rounded">
                                      <span className="text-gray-600">칼로리:</span>
                                      <span className="font-bold ml-1">
                                        {fatSecretResults[images[selectedImageIndex].id].nutritionData.calories || 'N/A'}
                                      </span>
                                    </div>
                                    <div className="bg-white p-2 rounded">
                                      <span className="text-gray-600">탄수화물:</span>
                                      <span className="font-bold ml-1">
                                        {fatSecretResults[images[selectedImageIndex].id].nutritionData.carbs || 'N/A'}
                                      </span>
                                    </div>
                                  </div>
                                )}
                                {fatSecretResults[images[selectedImageIndex].id].fatSecretUrl && (
                                  <a 
                                    href={fatSecretResults[images[selectedImageIndex].id].fatSecretUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                                  >
                                    <LinkIcon />
                                    FatSecret에서 보기
                                  </a>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                              <div className="flex items-center gap-2 mb-2">
                                <div className="p-1 bg-gray-100 rounded">
                                  <FatSecretIcon />
                                </div>
                                <span className="text-xs md:text-sm font-bold text-gray-700">검색 결과 없음</span>
                              </div>
                              <p className="text-xs md:text-sm text-gray-600">
                                {fatSecretResults[images[selectedImageIndex].id].message || 
                                 'FatSecret에서 매칭되는 영양정보를 찾을 수 없습니다.'}
                              </p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs md:text-sm text-gray-500 text-center py-6">
                          {fatSecretSearchEnabled 
                            ? '이미지를 선택하고 분석을 진행하면 FatSecret 검색 결과가 여기에 표시됩니다.' 
                            : 'FatSecret 검색이 비활성화되어 있습니다.'}
                        </p>
                      )}
                    </div>
                  )}

                  {activeTab === 'dashboard' && (
                    <div>
                      <div className="flex items-center justify-between mb-3 md:mb-4">
                        <h3 className="text-sm md:text-base font-bold text-gray-800">영양정보 대시보드</h3>
                        <button
                          onClick={loadDashboardData}
                          className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 transition-colors"
                        >
                          <AllIcon />
                          새로고침
                        </button>
                      </div>
                      
                      {dashboardData.length > 0 ? (
                        <div className="space-y-3 max-h-80 overflow-y-auto">
                          {dashboardData.map((entry, index) => (
                            <div key={entry.id} className="p-3 md:p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <div className="p-1 bg-purple-100 rounded">
                                    <NutritionIcon />
                                  </div>
                                  <span className="text-sm font-bold text-gray-800">{entry.foodName}</span>
                                </div>
                                <button
                                  onClick={() => removeDashboardEntry(entry.id)}
                                  className="text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded transition-colors"
                                >
                                  <DeleteIcon />
                                </button>
                              </div>
                              
                              {entry.nutritionData && (
                                <div className="grid grid-cols-3 gap-2 text-xs mb-2">
                                  <div className="bg-white p-2 rounded">
                                    <span className="text-gray-600">칼로리</span>
                                    <div className="font-bold">{entry.nutritionData.calories || 'N/A'}</div>
                                  </div>
                                  <div className="bg-white p-2 rounded">
                                    <span className="text-gray-600">탄수화물</span>
                                    <div className="font-bold">{entry.nutritionData.carbs || 'N/A'}</div>
                                  </div>
                                  <div className="bg-white p-2 rounded">
                                    <span className="text-gray-600">단백질</span>
                                    <div className="font-bold">{entry.nutritionData.protein || 'N/A'}</div>
                                  </div>
                                </div>
                              )}
                              
                              <div className="flex items-center justify-between text-xs text-gray-500">
                                <span>{new Date(entry.uploadedAt).toLocaleString()}</span>
                                {entry.fatSecretUrl && (
                                  <a 
                                    href={entry.fatSecretUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
                                  >
                                    <LinkIcon />
                                    상세보기
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center text-gray-500 py-12">
                          <div className="text-4xl md:text-6xl mb-4">📊</div>
                          <h4 className="text-lg md:text-xl font-bold mb-2">대시보드가 비어있습니다</h4>
                          <p className="text-xs md:text-sm mb-4">
                            FatSecret 검색을 활성화하고 이미지를 분석하면<br/>
                            영양정보가 자동으로 대시보드에 추가됩니다.
                          </p>
                          {!fatSecretSearchEnabled && (
                            <button
                              onClick={() => setFatSecretSearchEnabled(true)}
                              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs md:text-sm rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg"
                            >
                              <FatSecretIcon />
                              <span>FatSecret 검색 활성화</span>
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 상태바 */}
        <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-3 md:p-4 mt-4 md:mt-6">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full animate-pulse"></div>
            <span className="text-xs md:text-sm text-gray-700 font-medium flex-1">
              {statusMessage}
            </span>
          </div>
        </div>
      </div>

      {/* 직접 추가 모달 */}
      {showManualAdd && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm md:max-w-md border border-blue-200">
            <div className="p-6 md:p-8">
              <div className="flex items-center justify-between mb-4 md:mb-6">
                <h2 className="text-lg md:text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">식재료 직접 추가</h2>
                <button
                  onClick={closeManualAdd}
                  className="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-lg transition-all duration-200"
                >
                  <CloseIcon />
                </button>
              </div>
              
              <div className="space-y-4 md:space-y-6">
                <div>
                  <label className="block text-sm md:text-base font-bold text-gray-700 mb-2">
                    식재료 이름
                  </label>
                  <input
                    ref={manualInputRef}
                    type="text"
                    value={manualIngredientName}
                    onChange={(e) => setManualIngredientName(e.target.value)}
                    onKeyPress={handleManualInputKeyPress}
                    placeholder="예: 사과, 우유, 당근..."
                    className="w-full px-3 py-2 md:px-4 md:py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200 text-gray-800 font-medium text-sm md:text-base"
                  />
                </div>
                
                <div>
                  <label className="block text-sm md:text-base font-bold text-gray-700 mb-2">
                    수량
                  </label>
                  <div className="flex items-center justify-center gap-3 md:gap-4">
                    <button
                      onClick={() => setManualIngredientQuantity(Math.max(1, manualIngredientQuantity - 1))}
                      className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-gradient-to-r from-red-100 to-red-200 text-red-600 hover:from-red-200 hover:to-red-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold"
                    >
                      <MinusIcon />
                    </button>
                    
                    <div className="flex flex-col items-center min-w-[60px] md:min-w-[80px] bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 md:p-4 border-2 border-blue-200">
                      <span className="text-2xl md:text-3xl font-bold text-blue-600">{manualIngredientQuantity}</span>
                      <span className="text-xs md:text-sm text-gray-500 font-medium">개</span>
                    </div>
                    
                    <button
                      onClick={() => setManualIngredientQuantity(manualIngredientQuantity + 1)}
                      className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-gradient-to-r from-green-100 to-green-200 text-green-600 hover:from-green-200 hover:to-green-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold"
                    >
                      <PlusIcon />
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 md:gap-4 mt-6 md:mt-8">
                <button
                  onClick={closeManualAdd}
                  className="flex-1 py-3 md:py-4 px-4 md:px-6 bg-gray-200 text-gray-800 rounded-lg font-bold hover:bg-gray-300 transition-all duration-200 transform hover:scale-105 text-sm md:text-base"
                >
                  취소
                </button>
                <button
                  onClick={addManualIngredient}
                  disabled={isAddingManual || !manualIngredientName.trim()}
                  className="flex-1 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-lg font-bold hover:from-blue-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 disabled:transform-none flex items-center justify-center gap-2 shadow-lg text-sm md:text-base"
                >
                  {isAddingManual ? <LoadingSpinner /> : <PlusIcon />}
                  <span>{isAddingManual ? '추가 중...' : '추가하기'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FoodDetectionApp;