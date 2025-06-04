const GEMINI_API_KEY = process.env.REACT_APP_GEMINI_API_KEY;
const GEMINI_API_URL = process.env.REACT_APP_GEMINI_API_URL || 
  'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent';

export const callGeminiDirect = async (prompt, text, detectionResults = null) => {
  try {
    const enhancedPrompt = buildEnhancedPrompt(prompt, text, detectionResults);
    
    const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: enhancedPrompt
          }]
        }],
        generationConfig: {
          temperature: 0.05,
          topK: 20,
          topP: 0.7,
          maxOutputTokens: 100,
        }
      }),
    });

    if (response.ok) {
      const data = await response.json();
      return data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    } else {
      throw new Error(`Gemini API Error: ${response.status}`);
    }
  } catch (error) {
    console.error('Gemini API 호출 실패:', error);
    throw error;
  }
};

const buildEnhancedPrompt = (prompt, text, detectionResults) => {
  // 브랜드 탐지 및 컨텍스트 빌딩 로직
  // (기존 코드의 브랜드 탐지 로직을 여기로 이동)
  return enhancedPrompt;
};