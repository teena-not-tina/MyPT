const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://192.168.0.19:8000';

export const detectFood = async (file, confidence = 0.5, useEnsemble = true) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('confidence', confidence);
  formData.append('use_ensemble', useEnsemble);

  const response = await fetch(`${API_BASE_URL}/api/detect`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Detection API Error: ${response.status}`);
  }

  return await response.json();
};

export const extractOCR = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/ocr`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`OCR API Error: ${response.status}`);
  }

  return await response.json();
};

export const analyzeWithGemini = async (text, detectionResults = null) => {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      detection_results: detectionResults,
    }),
  });

  if (!response.ok) {
    throw new Error(`Gemini API Error: ${response.status}`);
  }

  return await response.json();
};

export const saveFridgeData = async (fridgeData) => {
  const response = await fetch(`${API_BASE_URL}/api/fridge/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(fridgeData),
  });

  if (!response.ok) {
    throw new Error(`Save API Error: ${response.status}`);
  }

  return await response.json();
};

export const loadFridgeData = async (userId) => {
  const response = await fetch(`${API_BASE_URL}/api/fridge/load/${userId}`);

  if (!response.ok) {
    throw new Error(`Load API Error: ${response.status}`);
  }

  return await response.json();
};

export const testServerConnection = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const result = await response.json();
      console.log('서버 연결 성공:', result);
      return { success: true, data: result };
    } else {
      throw new Error(`Server Error: ${response.status}`);
    }
  } catch (error) {
    console.error('서버 연결 실패:', error);
    return { success: false, error: error.message };
  }
};