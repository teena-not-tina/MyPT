// utils/legacyDataMigration.js

// 버전3 데이터를 현재 형식으로 변환하는 함수
export const convertV3DataToCurrentFormat = (v3Data) => {
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

// 로컬 스토리지에서 버전3 데이터 찾기
export const findV3DataInLocalStorage = () => {
  // 버전3에서 사용했을 가능성이 있는 로컬 스토리지 키들
  const possibleKeys = [
    'foodDetectionData',
    'fridgeIngredients',
    'savedIngredients',
    'fridge_data_v3',
    'ingredients',
    'food_list',
    'detected_foods',
    'analyzed_results',
    // 날짜별로 저장되었을 수도 있음
    `fridge_data_${new Date().getFullYear()}`,
    `ingredients_${new Date().getFullYear()}`
  ];

  const foundData = [];
  const checkedKeys = [];

  for (const key of possibleKeys) {
    const stored = localStorage.getItem(key);
    checkedKeys.push(key);
    
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        
        // 배열인 경우
        if (Array.isArray(parsed) && parsed.length > 0) {
          foundData.push({
            key: key,
            data: parsed,
            type: 'array'
          });
        }
        
        // 객체에 ingredients 속성이 있는 경우
        if (parsed && typeof parsed === 'object') {
          if (parsed.ingredients && Array.isArray(parsed.ingredients)) {
            foundData.push({
              key: key + '.ingredients',
              data: parsed.ingredients,
              type: 'object.ingredients'
            });
          }
          if (parsed.data && Array.isArray(parsed.data)) {
            foundData.push({
              key: key + '.data',
              data: parsed.data,
              type: 'object.data'
            });
          }
          if (parsed.items && Array.isArray(parsed.items)) {
            foundData.push({
              key: key + '.items',
              data: parsed.items,
              type: 'object.items'
            });
          }
        }
      } catch (parseError) {
        console.warn(`로컬 스토리지 키 "${key}" 파싱 실패:`, parseError);
      }
    }
  }

  return {
    foundData,
    checkedKeys,
    totalChecked: checkedKeys.length
  };
};

// 로컬 스토리지에서 특정 사용자의 버전3 데이터 찾기
export const findV3DataForUser = (userId) => {
  const possibleKeys = [
    `fridge_${userId}`,
    `fridge_data_${userId}`,
    `ingredients_${userId}`,
    `food_list_${userId}`,
    `foodDetectionData_${userId}`
  ];

  for (const key of possibleKeys) {
    const stored = localStorage.getItem(key);
    
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        return {
          found: true,
          key: key,
          data: parsed
        };
      } catch (error) {
        console.warn(`파싱 실패: ${key}`, error);
      }
    }
  }

  return {
    found: false,
    data: null
  };
};

// 중복 제거하면서 데이터 병합
export const mergeIngredientData = (existingData, newData) => {
  const mergedData = [...existingData];
  let addedCount = 0;
  
  newData.forEach(newItem => {
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
  
  return {
    mergedData,
    addedCount
  };
};