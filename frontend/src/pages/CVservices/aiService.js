// frontend/src/components/Diet/services/aiService.js
const GEMINI_API_KEY = process.env.REACT_APP_GEMINI_API_KEY;
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent';

export const aiService = {
  // Gemini 직접 호출 (필요시)
  callGeminiDirect: async (prompt) => {
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
          maxOutputTokens: 200,
          topP: 0.7,
          topK: 20
        }
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Gemini API failed: ${response.status}`);
    }
    
    const result = await response.json();
    return result.candidates?.[0]?.content?.parts?.[0]?.text || null;
  },

  // 식품명 추론
  inferFoodName: async (ocrText, detectionResults = null) => {
    let prompt = `식품의 포장지를 OCR로 추출한 텍스트를 분석해서 어떤 식품인지 추론해주세요.

추출된 텍스트: ${ocrText}`;

    if (detectionResults && detectionResults.length > 0) {
      const detectedClasses = detectionResults.map(det => det.class).join(', ');
      prompt += `\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: ${detectedClasses}`;
    }

    prompt += `\n\n분석 결과를 간단하고 명확하게 답변해주세요.`;

    return aiService.callGeminiDirect(prompt);
  },

  // 레시피 추천
  suggestRecipes: async (ingredients) => {
    const ingredientList = ingredients.map(ing => ing.name).join(', ');
    
    const prompt = `다음 식재료들로 만들 수 있는 한국 요리 레시피 3개를 추천해주세요.

식재료: ${ingredientList}

각 레시피는 다음 형식으로 작성해주세요:
1. 요리명
2. 필요한 재료
3. 간단한 조리법 (3-4단계)`;

    return aiService.callGeminiDirect(prompt);
  }
};