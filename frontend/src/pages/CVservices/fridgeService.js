// frontend/src/components/Diet/services/fridgeService.js
const API_BASE_URL = process.env.REACT_APP_CV_SERVICE_URL || 'http://localhost:8080';

export const fridgeService = {
  // 냉장고 데이터 저장
  saveFridgeData: async (fridgeData) => {
    const response = await fetch(`${API_BASE_URL}/api/fridge/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(fridgeData),
    });
    
    if (!response.ok) {
      throw new Error(`Save failed: ${response.status}`);
    }
    return response.json();
  },

  // 냉장고 데이터 불러오기
  loadFridgeData: async (userId) => {
    const response = await fetch(`${API_BASE_URL}/api/fridge/load/${userId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        return { success: false, ingredients: [] };
      }
      throw new Error(`Load failed: ${response.status}`);
    }
    return response.json();
  },

  // V3 데이터 불러오기 (로컬 스토리지 백업)
  loadV3Data: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/fridge/load-v3/${userId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return { success: false, data: [] };
        }
        throw new Error(`V3 load failed: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      // 서버에서 실패하면 로컬 스토리지 확인
      console.log('서버 V3 데이터 불러오기 실패, 로컬 스토리지 확인 중...');
      return loadV3FromLocalStorage();
    }
  },

  // 간단한 저장
  saveSimple: async (userId, ingredients) => {
    const response = await fetch(`${API_BASE_URL}/api/fridge/save-simple`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId: userId,
        ingredients: ingredients
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Simple save failed: ${response.status}`);
    }
    return response.json();
  },

  // 간단한 불러오기
  loadSimple: async (userId) => {
    const response = await fetch(`${API_BASE_URL}/api/fridge/load-simple/${userId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        return { success: false, ingredients: [] };
      }
      throw new Error(`Simple load failed: ${response.status}`);
    }
    return response.json();
  }
};

// 로컬 스토리지에서 V3 데이터 불러오기 함수
const loadV3FromLocalStorage = () => {
  try {
    const possibleKeys = [
      'foodDetectionData',
      'fridgeIngredients',
      'savedIngredients',
      'fridge_data_v3',
      'ingredients',
      'food_list',
      'detected_foods',
      'analyzed_results'
    ];

    for (const key of possibleKeys) {
      const stored = localStorage.getItem(key);
      
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          
          // 배열인 경우
          if (Array.isArray(parsed) && parsed.length > 0) {
            return { success: true, data: parsed, source: key };
          }
          
          // 객체에 ingredients 속성이 있는 경우
          if (parsed && typeof parsed === 'object') {
            if (parsed.ingredients && Array.isArray(parsed.ingredients)) {
              return { success: true, data: parsed.ingredients, source: key + '.ingredients' };
            }
            if (parsed.data && Array.isArray(parsed.data)) {
              return { success: true, data: parsed.data, source: key + '.data' };
            }
            if (parsed.items && Array.isArray(parsed.items)) {
              return { success: true, data: parsed.items, source: key + '.items' };
            }
          }
        } catch (parseError) {
          console.warn(`로컬 스토리지 키 "${key}" 파싱 실패:`, parseError);
        }
      }
    }

    return { success: false, data: [], message: '로컬 V3 데이터를 찾을 수 없습니다.' };
  } catch (error) {
    console.error('로컬 V3 데이터 로드 실패:', error);
    return { success: false, data: [], error: error.message };
  }
};