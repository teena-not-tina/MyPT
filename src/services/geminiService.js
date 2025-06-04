// services/geminiService.js
const GEMINI_API_KEY = process.env.REACT_APP_GEMINI_API_KEY || 'AIzaSyBBHRss0KLaEeeAgggsVOIGQ_zhS5ssDGw';
const GEMINI_API_URL = process.env.REACT_APP_GEMINI_API_URL || 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent';

export const geminiService = {
  // Gemini API를 사용한 식품 추론
  callGeminiAPI: async (text, detectionResults = null) => {
    if (!text || text.trim() === "") {
      console.log("분석할 텍스트가 없습니다.");
      return null;
    }
    
    try {
      console.log(`🤖 Gemini API 호출 진행`);
      
      // 탐지 결과가 있으면 컨텍스트에 포함
      let detectionContext = "";
      if (detectionResults && detectionResults.length > 0) {
        const detectedClasses = detectionResults.filter(det => det.class !== 'other').map(det => det.class);
        if (detectedClasses.length > 0) {
          detectionContext = `\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: ${detectedClasses.join(', ')}`;
        }
      }

      const prompt = `식품의 포장지를 OCR로 추출한 텍스트를 분석해서 어떤 식품인지 추론해주세요.

추출된 텍스트: ${text}${detectionContext}

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
              return inferenceResult;
            }
          }
        }
      } else if (response.status === 429) {
        console.log(`⚠️ Gemini API 할당량 초과 (429)`);
        throw new Error('API_QUOTA_EXCEEDED');
      }
      
      console.log(`❌ Gemini API 오류 - 상태 코드: ${response.status}`);
      throw new Error(`API_ERROR_${response.status}`);
      
    } catch (error) {
      console.error(`❌ Gemini API 분석 중 오류 발생: ${error}`);
      throw error;
    }
  },

  // Detection 결과 번역
  translateDetectionResult: async (englishName) => {
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
        
        return null;
      } else {
        console.error(`❌ Detection 번역 API 오류: ${response.status}`);
        return null;
      }
    } catch (error) {
      console.error(`❌ Detection 번역 중 오류: ${error}`);
      return null;
    }
  }
};

export default geminiService;