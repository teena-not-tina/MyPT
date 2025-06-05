// services/apiService.js
// 향상된 OCR 추론 시스템과 호환되는 API 서비스

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';

// 파일 검증 함수
const validateFile = (file) => {
  if (!file) {
    throw new Error('파일이 제공되지 않았습니다.');
  }
  
  if (typeof file === 'string') {
    throw new Error('파일이 올바른 객체 형태가 아닙니다.');
  }
  
  if (!(file instanceof File) && !(file instanceof Blob)) {
    throw new Error('올바른 파일 객체가 아닙니다.');
  }
  
  // 파일 크기 검증 (최대 10MB)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    throw new Error('파일 크기가 너무 큽니다. (최대 10MB)');
  }
  
  // 파일 타입 검증
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    throw new Error('지원하지 않는 파일 형식입니다.');
  }
};

// 에러 응답 처리 헬퍼 함수
const handleErrorResponse = async (response, apiName) => {
  let errorMessage = `${apiName} API 오류: ${response.status}`;
  let errorDetails = null;
  
  try {
    // 응답 본문을 텍스트로 먼저 읽기
    const responseText = await response.text();
    
    // JSON 파싱 시도
    try {
      const errorData = JSON.parse(responseText);
      errorDetails = errorData;
      errorMessage = errorData.message || errorData.error || errorMessage;
    } catch (e) {
      // JSON이 아닌 경우 텍스트 그대로 사용
      errorMessage = responseText || errorMessage;
    }
  } catch (e) {
    console.error('에러 응답 읽기 실패:', e);
  }
  
  const error = new Error(errorMessage);
  error.status = response.status;
  error.details = errorDetails;
  
  console.error(`❌ ${apiName} 상세 에러:`, {
    status: response.status,
    statusText: response.statusText,
    message: errorMessage,
    details: errorDetails
  });
  
  return error;
};

const apiService = {
  // 서버 연결 테스트
  async testConnection() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`서버 응답 오류: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('서버 연결 실패:', error);
      throw error;
    }
  },

  // OCR 수행 (향상된 추론 지원)
  async performOCR(file) {
    validateFile(file);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('📤 OCR 요청 시작:', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      });
      
      const response = await fetch(`${API_BASE_URL}/api/ocr`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, 'OCR');
      }
      
      const result = await response.json();
      console.log('✅ OCR 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ OCR 실패:', error);
      throw error;
    }
  },

  // 향상된 OCR 추론 수행
  async performEnhancedOCR(file) {
    validateFile(file);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('📤 향상된 OCR 요청 시작:', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      });
      
      const response = await fetch(`${API_BASE_URL}/api/ocr/enhanced`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '향상된 OCR');
      }
      
      const result = await response.json();
      console.log('✅ 향상된 OCR 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 향상된 OCR 실패:', error);
      throw error;
    }
  },

  // 객체 탐지 수행
  async performDetection(file, confidence = 0.8) {
    validateFile(file);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('confidence', confidence.toString());
      formData.append('use_ensemble', 'true');
      
      console.log('📤 Detection 요청 시작:', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        confidence: confidence,
        useEnsemble: true,
        endpoint: `${API_BASE_URL}/api/detect`
      });
      
      const response = await fetch(`${API_BASE_URL}/api/detect`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, 'Detection');
      }
      
      const result = await response.json();
      console.log('✅ Detection 성공:', result);
      return result;
    } catch (error) {
      // 네트워크 에러인지 확인
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        console.error('❌ 네트워크 에러: 서버에 연결할 수 없습니다.');
        error.message = '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.';
      }
      
      console.error('❌ Detection 실패:', {
        message: error.message,
        status: error.status,
        details: error.details,
        stack: error.stack
      });
      
      throw error;
    }
  },

  // 웹 검색 수행
  async performWebSearch(query) {
    try {
      console.log('📤 웹 검색 요청:', { query });
      
      const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: query,
          max_results: 10,
          include_images: false,
          safe_search: 'moderate'
        }),
      });
      
      if (!response.ok) {
        const error = await handleErrorResponse(response, '웹 검색');
        console.warn('웹 검색 실패, 빈 배열 반환:', error.message);
        return [];
      }
      
      const result = await response.json();
      console.log('✅ 웹 검색 성공:', result);
      
      // 검색 결과를 표준 형식으로 변환
      return result.results?.map(item => ({
        title: item.title || '',
        snippet: item.snippet || '',
        url: item.url || '',
        source: item.source || 'web'
      })) || [];
    } catch (error) {
      console.error('❌ 웹 검색 실패:', error);
      // 웹 검색 실패 시 빈 배열 반환 (앱이 계속 작동하도록)
      return [];
    }
  },

  // 식재료명 검증 및 정제
  async validateIngredientName(name, ocrText = '') {
    try {
      console.log('📤 식재료 검증 요청:', { name, hasOcrText: !!ocrText });
      
      const response = await fetch(`${API_BASE_URL}/api/ingredient/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          name: name,
          ocr_context: ocrText,
          use_web_search: true
        }),
      });
      
      if (!response.ok) {
        const error = await handleErrorResponse(response, '식재료 검증');
        console.warn('식재료 검증 실패, 원본 반환:', error.message);
        return { validated_name: name, confidence: 0.5 };
      }
      
      const result = await response.json();
      console.log('✅ 식재료 검증 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 식재료 검증 실패:', error);
      // 검증 실패 시 원본 이름 반환
      return { validated_name: name, confidence: 0.5 };
    }
  },

  // 냉장고 데이터 저장
  async saveFridgeData(data) {
    try {
      console.log('📤 냉장고 데이터 저장 요청:', { dataSize: JSON.stringify(data).length });
      
      const response = await fetch(`${API_BASE_URL}/api/fridge/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '데이터 저장');
      }
      
      const result = await response.json();
      console.log('✅ 데이터 저장 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 데이터 저장 실패:', error);
      throw error;
    }
  },

  // 간소화된 냉장고 데이터 저장
  async saveSimpleFridgeData(data) {
    try {
      console.log('📤 간소화된 냉장고 데이터 저장 요청:', { dataSize: JSON.stringify(data).length });
      
      const response = await fetch(`${API_BASE_URL}/api/fridge/save-simple`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '간소화된 저장');
      }
      
      const result = await response.json();
      console.log('✅ 간소화된 저장 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 간소화된 저장 실패:', error);
      throw error;
    }
  },

  // 냉장고 데이터 불러오기
  async loadFridgeData(userId) {
    try {
      console.log('📤 냉장고 데이터 로드 요청:', { userId });
      
      const response = await fetch(`${API_BASE_URL}/api/fridge/load/${userId}`);
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '데이터 로드');
      }
      
      const result = await response.json();
      console.log('✅ 데이터 로드 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 데이터 로드 실패:', error);
      throw error;
    }
  },

  // 간소화된 냉장고 데이터 불러오기
  async loadSimpleFridgeData(userId) {
    try {
      console.log('📤 간소화된 냉장고 데이터 로드 요청:', { userId });
      
      const response = await fetch(`${API_BASE_URL}/api/fridge/load-simple/${userId}`);
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '간소화된 로드');
      }
      
      const result = await response.json();
      console.log('✅ 간소화된 로드 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 간소화된 로드 실패:', error);
      throw error;
    }
  },

  // 버전3 데이터 불러오기
  async loadV3FridgeData(userId) {
    try {
      console.log('📤 V3 냉장고 데이터 로드 요청:', { userId });
      
      const response = await fetch(`${API_BASE_URL}/api/fridge/load-v3/${userId}`);
      
      if (!response.ok) {
        throw await handleErrorResponse(response, 'V3 데이터 로드');
      }
      
      const result = await response.json();
      console.log('✅ V3 데이터 로드 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ V3 데이터 로드 실패:', error);
      throw error;
    }
  },

  // 버전3 데이터 마이그레이션
  async migrateV3Data(userId) {
    try {
      console.log('📤 V3 데이터 마이그레이션 요청:', { userId });
      
      const response = await fetch(`${API_BASE_URL}/api/fridge/migrate-v3/${userId}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, 'V3 마이그레이션');
      }
      
      const result = await response.json();
      console.log('✅ V3 마이그레이션 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ V3 마이그레이션 실패:', error);
      throw error;
    }
  },

  // Gemini 분석
  async analyzeWithGemini(text, detectionResults = null) {
    try {
      console.log('📤 Gemini 분석 요청:', { 
        textLength: text?.length || 0, 
        hasDetectionResults: !!detectionResults 
      });
      
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          text: text,
          detection_results: detectionResults
        }),
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, 'Gemini 분석');
      }
      
      const result = await response.json();
      console.log('✅ Gemini 분석 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ Gemini 분석 실패:', error);
      throw error;
    }
  },

  // 모델 정보 조회
  async getModelsInfo() {
    try {
      console.log('📤 모델 정보 조회 요청');
      
      const response = await fetch(`${API_BASE_URL}/api/models/info`);
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '모델 정보 조회');
      }
      
      const result = await response.json();
      console.log('✅ 모델 정보 조회 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 모델 정보 조회 실패:', error);
      throw error;
    }
  },

  // 단일 모델로 탐지
  async performSingleModelDetection(modelName, file, confidence = 0.5) {
    validateFile(file);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('confidence', confidence.toString());
      
      console.log(`📤 ${modelName} 모델 Detection 요청:`, {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        confidence: confidence,
        modelName: modelName
      });
      
      const response = await fetch(`${API_BASE_URL}/api/detect/single/${modelName}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, `${modelName} 모델 Detection`);
      }
      
      const result = await response.json();
      console.log(`✅ ${modelName} 모델 Detection 성공:`, result);
      return result;
    } catch (error) {
      console.error(`❌ ${modelName} 모델 Detection 실패:`, error);
      throw error;
    }
  },

  // 커스텀 앙상블 탐지
  async performCustomEnsembleDetection(file, options = {}) {
    validateFile(file);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('confidence', (options.confidence || 0.5).toString());
      formData.append('yolo11s_weight', (options.yolo11s_weight || 1.0).toString());
      formData.append('best_weight', (options.best_weight || 1.2).toString());
      formData.append('best_friged_weight', (options.best_friged_weight || 1.1).toString());
      formData.append('iou_threshold', (options.iou_threshold || 0.5).toString());
      
      console.log('📤 커스텀 앙상블 Detection 요청:', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        options: options
      });
      
      const response = await fetch(`${API_BASE_URL}/api/detect/ensemble/custom`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw await handleErrorResponse(response, '커스텀 앙상블 Detection');
      }
      
      const result = await response.json();
      console.log('✅ 커스텀 앙상블 Detection 성공:', result);
      return result;
    } catch (error) {
      console.error('❌ 커스텀 앙상블 Detection 실패:', error);
      throw error;
    }
  }
};

export default apiService;