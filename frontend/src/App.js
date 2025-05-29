import React, { useState, useRef } from 'react';

const FoodDetectionApp = () => {
  const [currentMode, setCurrentMode] = useState('home');
  const [currentImage, setCurrentImage] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [detectionResults, setDetectionResults] = useState(null);
  const [ocrResults, setOcrResults] = useState('');
  const [geminiResults, setGeminiResults] = useState('');
  const [fridgeIngredients, setFridgeIngredients] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [confidence, setConfidence] = useState(0.5);
  const [statusMessage, setStatusMessage] = useState('해먹기 또는 사먹기를 선택하세요.');
  const [isDragOver, setIsDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState('detection');
  
  const fileInputRef = useRef(null);
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://192.168.0.19:8000';

  // 기본 아이콘 컴포넌트들
  const CookingIcon = () => <span className="text-2xl">👨‍🍳</span>;
  const EatingIcon = () => <span className="text-2xl">🍽️</span>;
  const UploadIcon = () => <span className="text-sm">📁</span>;
  const EyeIcon = () => <span className="text-sm">👁️</span>;
  const BrainIcon = () => <span className="text-sm">🧠</span>;
  const FileTextIcon = () => <span className="text-sm">📄</span>;
  const SettingsIcon = () => <span className="text-sm">⚙️</span>;
  const FridgeIcon = () => <span className="text-lg">🧊</span>;
  const BackIcon = () => <span className="text-sm">←</span>;
  const PlusIcon = () => <span className="text-sm">+</span>;
  const MinusIcon = () => <span className="text-sm">-</span>;
  const DeleteIcon = () => <span className="text-sm">🗑️</span>;
  const LoadingSpinner = () => (
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
  );

  // 식재료 수량 업데이트
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

  // 식재료 삭제
  const removeIngredient = (id) => {
    setFridgeIngredients(prev => 
      prev.filter(ingredient => ingredient.id !== id)
    );
  };

  // 냉장고에 식재료 추가 (간단 버전)
  const addToFridge = (newIngredients) => {
    console.log('냉장고에 추가할 식재료:', newIngredients);
    
    setFridgeIngredients(prev => {
      const updated = [...prev];
      let maxId = updated.length > 0 ? Math.max(...updated.map(item => item.id)) : 0;

      newIngredients.forEach(newItem => {
        const existingIndex = updated.findIndex(item => 
          item.name === newItem.name
        );

        if (existingIndex >= 0) {
          // 기존 식재료가 있으면 수량 증가
          updated[existingIndex].quantity += newItem.quantity;
        } else {
          // 새로운 식재료 추가
          updated.push({
            id: ++maxId,
            name: newItem.name,
            quantity: newItem.quantity,
            confidence: newItem.confidence || 0.8,
            source: newItem.source || 'analysis'
          });
        }
      });

      console.log('업데이트된 냉장고:', updated);
      return updated;
    });
  };

  // 홈으로 돌아가기
  const goToHome = () => {
    setCurrentMode('home');
    setCurrentImage(null);
    setImageFile(null);
    setDetectionResults(null);
    setOcrResults('');
    setGeminiResults('');
    setStatusMessage('해먹기 또는 사먹기를 선택하세요.');
    setActiveTab('detection');
  };

  // 해먹기 모드 시작
  const startHomeCooking = () => {
    setCurrentMode('homeCooking');
    setStatusMessage('냉장고 속 식재료 이미지를 업로드하세요.');
  };

  // 사먹기 모드 시작
  const startEating = () => {
    setCurrentMode('eating');
    setStatusMessage('사먹기 기능은 개발 중입니다.');
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
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        processImageFile(file);
      } else {
        setStatusMessage('이미지 파일만 업로드 가능합니다.');
      }
    }
  };

  // 이미지 파일 처리
  const processImageFile = (file) => {
    setImageFile(file);
    
    if (!file.type.startsWith('image/')) {
      setStatusMessage('이미지 파일만 업로드 가능합니다.');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setCurrentImage(e.target.result);
      setDetectionResults(null);
      setOcrResults('');
      setGeminiResults('');
      setStatusMessage(`이미지 준비 완료: ${file.name} - "식재료 분석" 버튼을 클릭하세요`);
    };
    
    reader.onerror = () => {
      setStatusMessage('이미지 로드 실패');
    };
    
    reader.readAsDataURL(file);
  };

  // 이미지 로드 함수
  const handleImageLoad = (event) => {
    const file = event.target.files[0];
    if (file) {
      processImageFile(file);
    }
  };

  // 영어 → 한글 번역
  const translateToKorean = (englishName) => {
    const translations = {
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
      'pepper': '피망',
      'garlic': '마늘',
      'mushroom': '버섯',
      'corn': '옥수수',
      'grape': '포도',
      'strawberry': '딸기',
      'lemon': '레몬',
      'cabbage': '양배추',
      'spinach': '시금치',
      'eggplant': '가지'
    };
    return translations[englishName.toLowerCase()] || englishName;
  };

  // Detection 결과 처리 (수량 합산 없이)
  const processDetectionResults = (detections) => {
    console.log('Detection 처리:', detections);
    
    const ingredients = detections.map((detection, index) => ({
      name: translateToKorean(detection.class),
      quantity: 1, // 각각 1개씩
      confidence: detection.confidence,
      source: 'detection'
    }));

    console.log('변환된 식재료:', ingredients);
    return ingredients;
  };

  // 스마트 분석 함수 - 개선된 버전 (실제 OCR 패턴 대응)
  const performSmartAnalysis = (text) => {
    console.log('🧠 스마트 분석 시작:', text);
    const results = [];
    
    // 분석 규칙들 (실제 OCR 패턴에 맞게 개선)
    const smartRules = [
      // 오렌지 관련 주스 패턴들
      {
        pattern: /오렌지.*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '오렌지주스',
        originalKeyword: 'orange',
        description: '오렌지 + 주스관련키워드 → 오렌지주스'
      },
      
      // 사과 관련 주스 패턴들  
      {
        pattern: /사과.*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '사과주스',
        originalKeyword: 'apple',
        description: '사과 + 주스관련키워드 → 사과주스'
      },
      
      // 토마토 관련 주스 패턴들
      {
        pattern: /토마토.*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '토마토주스',
        originalKeyword: 'tomato', 
        description: '토마토 + 주스관련키워드 → 토마토주스'
      },
      
      // 포도 관련 주스 패턴들
      {
        pattern: /포도.*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '포도주스',
        originalKeyword: 'grape',
        description: '포도 + 주스관련키워드 → 포도주스'
      },
      
      // 바나나 우유 패턴들
      {
        pattern: /바나나.*?(우유|milk|MILK)/i,
        result: '바나나우유',
        originalKeyword: 'banana',
        description: '바나나 + 우유 → 바나나우유'
      },
      
      // 딸기 우유 패턴들
      {
        pattern: /딸기.*?(우유|milk|MILK)/i,
        result: '딸기우유',
        originalKeyword: 'strawberry',
        description: '딸기 + 우유 → 딸기우유'
      },
      
      // 초콜릿 우유 패턴들
      {
        pattern: /초콜릿.*?(우유|milk|MILK)/i,
        result: '초콜릿우유',
        originalKeyword: 'chocolate',
        description: '초콜릿 + 우유 → 초콜릿우유'
      },
      
      // 복숭아 관련 주스 패턴들
      {
        pattern: /복숭아.*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '복숭아주스',
        originalKeyword: 'peach',
        description: '복숭아 + 주스관련키워드 → 복숭아주스'
      }
    ];
    
    console.log('🔍 텍스트 분석 대상:', `"${text}"`);
    
    // 각 규칙 적용
    smartRules.forEach((rule, index) => {
      const match = text.match(rule.pattern);
      if (match) {
        console.log(`✅ 규칙 ${index + 1} 적용: ${rule.description}`);
        console.log(`   매칭된 패턴: ${rule.pattern}`);
        console.log(`   매칭된 텍스트: "${match[0]}"`);
        
        // 수량 추출 (ml 숫자가 있으면 용량 기반, 없으면 1개)
        let quantity = 1;
        const mlMatch = match[0].match(/(\d+)\s*(ml|mL|ML)/i);
        if (mlMatch) {
          const ml = parseInt(mlMatch[1]);
          quantity = Math.max(1, Math.ceil(ml / 200)); // 200ml 기준으로 개수 계산
          console.log(`   용량 발견: ${ml}ml → ${quantity}개`);
        }
        
        results.push({
          result: rule.result,
          quantity: quantity,
          originalKeyword: rule.originalKeyword,
          matchedText: match[0],
          fullLine: text
        });
      }
    });
    
    console.log('🧠 스마트 분석 최종 결과:', results);
    return results;
  };

  // OCR 결과 처리 - 스마트 분석 우선 적용
  const processOCRResults = (text) => {
    console.log('📄 OCR 처리 시작:', text);
    
    const ingredients = [];
    const lines = text.split('\n').filter(line => line.trim());
    
    // 전체 텍스트와 각 줄에 대해 스마트 분석 수행
    const allText = lines.join(' ');
    const smartAnalyzedIngredients = performSmartAnalysis(allText);
    
    console.log('🔍 줄별 분석 시작...');
    
    lines.forEach((line, lineIndex) => {
      const cleanLine = line.trim();
      console.log(`\n📝 줄 ${lineIndex + 1} 분석: "${cleanLine}"`);
      
      // 이 줄이 스마트 분석에 매칭되는지 확인
      const smartMatch = smartAnalyzedIngredients.find(smart => {
        const lineWords = cleanLine.toLowerCase().split(/\s+/);
        const smartWords = smart.matchedText.toLowerCase().split(/\s+/);
        
        // 스마트 매치된 단어들이 현재 줄에 포함되어 있는지 확인
        const hasKeyWords = smartWords.some(word => 
          lineWords.some(lineWord => lineWord.includes(word) || word.includes(lineWord))
        );
        
        console.log(`   🧠 스마트 매치 확인: "${smart.matchedText}" vs "${cleanLine}" = ${hasKeyWords}`);
        return hasKeyWords;
      });
      
      if (smartMatch) {
        // 스마트 분석 결과 사용
        console.log(`✅ 스마트 분석 적용: "${cleanLine}" → "${smartMatch.result} ${smartMatch.quantity}개"`);
        ingredients.push({
          name: smartMatch.result,
          quantity: smartMatch.quantity,
          source: 'ocr_smart'
        });
        return;
      }
      
      // 스마트 분석이 안되면 기존 로직 적용
      console.log('   📋 기존 패턴 매칭 시도...');
      
      // "식재료명 개수개" 패턴 매칭
      let match = cleanLine.match(/(.+?)\s*(\d+)\s*개/);
      if (match) {
        const [, name, quantity] = match;
        const cleanName = name.trim()
          .replace(/입니다$|예요$|이에요$|이다$|다$|네요$|요$/, '')
          .replace(/은$|는$|이$|가$|을$|를$|의$|에$|에서$|로$|으로$/, '')
          .replace(/[-•*\d\.%()]+/g, '')
          .trim();
        
        if (cleanName && cleanName.length > 0) {
          console.log(`   ✅ 패턴 매칭: "${cleanLine}" → "${cleanName} ${quantity}개"`);
          ingredients.push({
            name: cleanName,
            quantity: parseInt(quantity) || 1,
            source: 'ocr'
          });
          return;
        }
      }
      
      // 단순 식재료명만 있는 경우
      const nameMatch = cleanLine.match(/([가-힣a-zA-Z\s]+)/);
      if (nameMatch && cleanLine.length < 50) {
        let name = nameMatch[1].trim();
        
        // 불필요한 문자 제거
        name = name
          .replace(/입니다$|예요$|이에요$|이다$|다$|네요$|요$/, '')
          .replace(/은$|는$|이$|가$|을$|를$|의$|에$|에서$|로$|으로$/, '')
          .replace(/\d+%|\d+ml|\d+ML|100%/gi, '')
          .replace(/[()[\]{}]/g, '')
          .trim();
        
        // 식재료 키워드 확인
        const foodKeywords = [
          '주스', '우유', '물', '차', '커피', '음료', '요거트', '치즈', '버터',
          '사과', '바나나', '오렌지', '당근', '양파', '감자', '토마토', '오이',
          '브로콜리', '상추', '배추', '시금치', '고추', '마늘', '생강',
          '달걀', '계란', '빵', '쌀', '면', '라면', '파스타',
          '닭고기', '소고기', '돼지고기', '생선', '새우', '햄', '소시지',
          '김치', '된장', '고추장', '간장', '설탕', '소금', '기름',
          '버섯', '콩', '견과', '딸기', '포도', '수박', '멜론', '아몬드'
        ];

        if (foodKeywords.some(keyword => name.includes(keyword)) || 
            (name.match(/[가-힣]+/) && name.length >= 2 && name.length <= 15)) {
          console.log(`   ✅ 키워드 매칭: "${cleanLine}" → "${name} 1개"`);
          ingredients.push({
            name: name,
            quantity: 1,
            source: 'ocr'
          });
        } else {
          console.log(`   ❌ 매칭 실패: "${cleanLine}" (키워드 없음)`);
        }
      }
    });

    console.log('📄 OCR 최종 추출 식재료:', ingredients);
    return ingredients;
  };

  // 식재료 분석 실행 - 버전 10 (OCR 결과도 대시보드 추가)
  const runIngredientAnalysis = async () => {
    if (!imageFile) {
      setStatusMessage('먼저 이미지를 로드하세요.');
      return;
    }

    if (isProcessing) return;

    console.log('=== 버전 10: 분석 시작 ===');
    setIsProcessing(true);
    
    try {
      // 1단계: Detection 시도
      setProcessingStep('식품 탐지 중...');
      setStatusMessage('식품 탐지 중...');

      let detections = [];
      let ocrText = '';
      
      try {
        // Detection API 호출
        const detectFormData = new FormData();
        detectFormData.append('file', imageFile);
        detectFormData.append('confidence', confidence);

        const detectResponse = await fetch(`${API_BASE_URL}/api/detect`, {
          method: 'POST',
          body: detectFormData,
        });

        if (detectResponse.ok) {
          const result = await detectResponse.json();
          console.log('Detection 성공:', result);
          setDetectionResults(result);
          detections = result.detections || [];
        } else {
          console.log('Detection 실패, Mock 데이터 사용');
          // Mock Detection 데이터
          detections = [
            { class: 'apple', confidence: 0.85 },
            { class: 'apple', confidence: 0.78 },
            { class: 'banana', confidence: 0.92 },
            { class: 'carrot', confidence: 0.81 }
          ];
          setDetectionResults({ detections });
        }
      } catch (error) {
        console.log('Detection API 오류, Mock 데이터 사용');
        detections = [
          { class: 'apple', confidence: 0.85 },
          { class: 'banana', confidence: 0.92 },
          { class: 'carrot', confidence: 0.81 }
        ];
        setDetectionResults({ detections });
      }

      // 2단계: OCR 시도
      setProcessingStep('텍스트 추출 중...');
      
      try {
        const ocrFormData = new FormData();
        ocrFormData.append('file', imageFile);

        const ocrResponse = await fetch(`${API_BASE_URL}/api/ocr`, {
          method: 'POST',
          body: ocrFormData,
        });

        if (ocrResponse.ok) {
          const result = await ocrResponse.json();
          console.log('OCR 성공:', result);
          ocrText = result.text || '';
          setOcrResults(ocrText);
        } else {
          console.log('OCR 실패');
          // Mock OCR 데이터 (테스트용)
          ocrText = '사과 2개\n바나나우유 1개\n오렌지주스';
          setOcrResults(ocrText);
        }
      } catch (error) {
        console.log('OCR API 오류');
        // Mock OCR 데이터 (테스트용)
        ocrText = '토마토 3개\n양파 1개';
        setOcrResults(ocrText);
      }

      // 3단계: 결과 처리
      setProcessingStep('결과 처리 중...');
      
      let finalIngredients = [];

      // OCR 텍스트가 있으면 OCR 우선 처리
      if (ocrText && ocrText.trim().length > 2) {
        console.log('OCR 우선 처리');
        
        try {
          // Gemini 분석 시도
          const geminiResponse = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: ocrText,
              analysis_type: 'ocr_ingredient_analysis',
              prompt: `다음 OCR 텍스트에서 식재료를 추출하고 "식재료명 개수개" 형식으로 출력해주세요.

OCR 텍스트: "${ocrText}"

🧠 스마트 분석 규칙:
1. 과일 + 용량단위 = 주스
   - "오렌지 + ml/L" = 오렌지주스
   - "사과 + 200ml" = 사과주스
   - "토마토 + juice" = 토마토주스

2. 과일 + 우유 = 우유음료
   - "바나나 + 우유/MILK" = 바나나우유
   - "딸기 + 우유" = 딸기우유

3. 용량 → 개수 변환
   - 200ml 기준 1개로 계산
   - 500ml = 3개, 1L = 5개

4. 정확한 제품명 구분
   - 단독 과일명 = 과일 (사과 = 과일 사과)
   - 과일 + 가공키워드 = 가공품 (오렌지주스)

예시:
입력: "오렌지 500ml 바나나 우유"
출력: 
오렌지주스 3개
바나나우유 1개

분석해주세요:`
            }),
          });

          if (geminiResponse.ok) {
            const geminiResult = await geminiResponse.json();
            console.log('Gemini OCR 분석 성공:', geminiResult);
            setGeminiResults(geminiResult.analysis || '');
            
            // Gemini 분석 결과를 파싱하여 식재료 추출
            finalIngredients = processOCRResults(geminiResult.analysis || '');
            setActiveTab('ocr');
            console.log('Gemini 분석으로 추출된 식재료:', finalIngredients);
          } else {
            throw new Error('Gemini 실패');
          }
        } catch (error) {
          console.log('Gemini 실패, OCR 직접 처리');
          // Gemini 실패시 OCR 텍스트 직접 처리
          finalIngredients = processOCRResults(ocrText);
          setGeminiResults('OCR 직접 처리 결과:\n' + finalIngredients.map(item => `${item.name} ${item.quantity}개`).join('\n'));
          setActiveTab('ocr');
          console.log('OCR 직접 처리로 추출된 식재료:', finalIngredients);
        }
      } 
      // OCR이 없으면 Detection 처리
      else if (detections.length > 0) {
        console.log('Detection 처리');
        finalIngredients = processDetectionResults(detections);
        setGeminiResults('Detection 한글 변환:\n' + finalIngredients.map(item => `${item.name} ${item.quantity}개`).join('\n'));
        setActiveTab('detection');
        console.log('Detection으로 추출된 식재료:', finalIngredients);
      }

      // 4단계: 냉장고에 추가
      if (finalIngredients.length > 0) {
        console.log('냉장고에 추가:', finalIngredients);
        addToFridge(finalIngredients);
        
        // 소스별 개수 계산
        const ocrCount = finalIngredients.filter(item => item.source === 'ocr').length;
        const detectionCount = finalIngredients.filter(item => item.source === 'detection').length;
        
        let sourceText = '';
        if (ocrCount > 0 && detectionCount > 0) {
          sourceText = ` (OCR: ${ocrCount}개, 탐지: ${detectionCount}개)`;
        } else if (ocrCount > 0) {
          sourceText = ` (OCR 분석)`;
        } else if (detectionCount > 0) {
          sourceText = ` (탐지 분석)`;
        }
        
        setStatusMessage(`✅ 분석 완료: ${finalIngredients.length}개 식재료 추가됨${sourceText}`);
      } else {
        setStatusMessage('분석된 식재료가 없습니다');
      }

    } catch (error) {
      console.error('분석 오류:', error);
      setStatusMessage('분석 중 오류가 발생했습니다');
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
      console.log('=== 버전 10: 분석 완료 ===');
    }
  };

  // 서버 연결 테스트
  const testServerConnection = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        const result = await response.json();
        console.log('서버 연결 성공:', result);
        setStatusMessage('서버 연결 성공');
      } else {
        setStatusMessage(`서버 응답 오류: ${response.status}`);
      }
    } catch (error) {
      console.error('서버 연결 실패:', error);
      setStatusMessage(`서버 연결 실패: ${error.message}`);
    }
  };

  // 홈 화면
  if (currentMode === 'home') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🍽️</div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">
              스마트 푸드 매니저
            </h1>
            <p className="text-gray-600 text-sm">
              AI로 똑똑하게 식사 계획하기
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={startHomeCooking}
              className="w-full bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl hover:scale-105 active:scale-95"
            >
              <div className="flex items-center gap-4">
                <div className="bg-green-100 rounded-full p-3">
                  <CookingIcon />
                </div>
                <div className="text-left flex-1">
                  <h3 className="text-lg font-semibold text-gray-800">해먹기</h3>
                  <p className="text-sm text-gray-600">냉장고 식재료로 요리하기</p>
                </div>
                <div className="text-gray-400">→</div>
              </div>
            </button>

            <button
              onClick={startEating}
              className="w-full bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl hover:scale-105 active:scale-95"
            >
              <div className="flex items-center gap-4">
                <div className="bg-orange-100 rounded-full p-3">
                  <EatingIcon />
                </div>
                <div className="text-left flex-1">
                  <h3 className="text-lg font-semibold text-gray-800">사먹기</h3>
                  <p className="text-sm text-gray-600">맛집 추천 및 주문하기</p>
                </div>
                <div className="text-gray-400">→</div>
              </div>
            </button>
          </div>

          <div className="mt-8 text-center">
            <button
              onClick={testServerConnection}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              서버 연결 테스트
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 사먹기 모드
  if (currentMode === 'eating') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-6xl mb-4">🚧</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-4">사먹기 기능 개발 중</h2>
          <p className="text-gray-600 mb-6">곧 멋진 기능으로 찾아뵙겠습니다!</p>
          <button
            onClick={goToHome}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 해먹기 모드 메인 화면
  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
      <div className="w-full max-w-md sm:max-w-2xl lg:max-w-6xl mx-auto p-3 sm:p-4 lg:p-6">
        
        {/* 헤더 */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={goToHome}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <BackIcon />
            </button>
            <CookingIcon />
            <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-800 truncate">
              해먹기 - 냉장고 식재료 분석
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-gray-600 hidden sm:block ml-12">
            냉장고 사진을 찍어서 식재료를 자동으로 인식해보세요
          </p>
        </div>

        {/* 액션 버튼들 */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
            <input
              type="file"
              accept="image/*"
              onChange={handleImageLoad}
              ref={fileInputRef}
              className="hidden"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center gap-2 py-3 px-4 bg-blue-600 text-white rounded-lg font-medium transition-all duration-200 active:scale-95 hover:bg-blue-700"
            >
              <UploadIcon />
              <span className="text-sm">이미지 업로드</span>
            </button>

            <button
              onClick={runIngredientAnalysis}
              disabled={!currentImage || isProcessing}
              className="flex items-center justify-center gap-2 py-3 px-4 bg-green-600 text-white rounded-lg font-medium transition-all duration-200 active:scale-95 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isProcessing ? <LoadingSpinner /> : <BrainIcon />}
              <span className="text-sm">식재료 분석</span>
            </button>
          </div>

          {/* 신뢰도 설정 */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 min-w-fit">
              <SettingsIcon />
              <span className="text-sm font-medium text-gray-700 whitespace-nowrap">신뢰도</span>
            </div>
            <div className="flex-1 px-2">
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.1"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <span className="text-sm font-medium text-gray-600 min-w-[2.5rem] text-center">
              {confidence.toFixed(1)}
            </span>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          
          {/* 이미지 표시 영역 */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-sm p-4">
              <div 
                className={`border-2 border-dashed rounded-xl min-h-[200px] sm:min-h-[300px] lg:min-h-[400px] flex items-center justify-center transition-all duration-300 cursor-pointer ${
                  isDragOver 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                {currentImage ? (
                  <img
                    src={currentImage}
                    alt="Uploaded"
                    className="max-w-full max-h-full rounded-lg object-contain"
                    style={{ maxHeight: '60vh' }}
                  />
                ) : (
                  <div className="text-center text-gray-500 p-6">
                    <div className="text-4xl sm:text-5xl mb-3">🧊</div>
                    <p className="text-sm sm:text-base font-medium mb-1">
                      {isDragOver ? '파일을 놓아주세요' : '냉장고 사진을 업로드하세요'}
                    </p>
                    <p className="text-xs sm:text-sm text-gray-400">
                      {isDragOver ? '' : '업로드 후 "식재료 분석" 버튼 클릭'}
                    </p>
                  </div>
                )}
              </div>

              {/* 진행 상태 */}
              {isProcessing && (
                <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <LoadingSpinner />
                    <span className="text-blue-800 text-sm font-medium">{processingStep}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 결과 표시 영역 */}
          <div className="lg:col-span-2">
            {/* 냉장고 속 식재료 대시보드 */}
            <div className="bg-white rounded-xl shadow-sm mb-4">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FridgeIcon />
                    <h3 className="text-lg font-semibold text-gray-800">냉장고 속 식재료</h3>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setFridgeIngredients([])}
                      className="text-xs text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1 rounded transition-colors"
                    >
                      전체 삭제
                    </button>
                    <div className="text-sm text-gray-500">
                      총 {fridgeIngredients.length}개
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-4" style={{ minHeight: '250px', maxHeight: '400px', overflowY: 'auto' }}>
                {fridgeIngredients.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {fridgeIngredients.map((ingredient) => (
                      <div key={ingredient.id} className="bg-gradient-to-r from-blue-50 to-green-50 border border-gray-200 rounded-lg p-4 transition-all duration-200 hover:shadow-md">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-gray-800 text-lg">{ingredient.name}</h4>
                          <button
                            onClick={() => removeIngredient(ingredient.id)}
                            className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded-full p-1 transition-colors"
                          >
                            <DeleteIcon />
                          </button>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => updateIngredientQuantity(ingredient.id, ingredient.quantity - 1)}
                              disabled={ingredient.quantity <= 1}
                              className="w-8 h-8 rounded-full bg-red-100 text-red-600 hover:bg-red-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
                            >
                              <MinusIcon />
                            </button>
                            
                            <div className="flex flex-col items-center">
                              <span className="text-2xl font-bold text-blue-600">{ingredient.quantity}</span>
                              <span className="text-xs text-gray-500">개</span>
                            </div>
                            
                            <button
                              onClick={() => updateIngredientQuantity(ingredient.id, ingredient.quantity + 1)}
                              className="w-8 h-8 rounded-full bg-green-100 text-green-600 hover:bg-green-200 flex items-center justify-center transition-colors"
                            >
                              <PlusIcon />
                            </button>
                          </div>
                          
                          <div className="text-xs text-gray-500 bg-white bg-opacity-70 px-2 py-1 rounded-full">
                            {ingredient.source === 'ocr' && '📄 OCR'}
                            {ingredient.source === 'detection' && '🎯 탐지'}
                            {ingredient.source === 'analysis' && '🧠 AI'}
                            {ingredient.confidence && (
                              <span className="ml-1 text-green-600 font-semibold">
                                {(ingredient.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    <div className="text-4xl mb-4">🥬</div>
                    <h4 className="text-lg font-medium mb-2">냉장고가 비어있습니다</h4>
                    <p className="text-sm">냉장고 사진을 업로드하고 "식재료 분석" 버튼을 클릭하세요</p>
                  </div>
                )}
              </div>
              
              {fridgeIngredients.length > 0 && (
                <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-xl">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">총 수량</span>
                    <span className="font-semibold text-gray-800">
                      {fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0)}개
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* 탭 네비게이션 */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="flex border-b border-gray-200">
                <button
                  onClick={() => setActiveTab('detection')}
                  className={`flex-1 py-3 px-2 text-xs sm:text-sm font-medium transition-colors ${
                    activeTab === 'detection' 
                      ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1">
                    <EyeIcon />
                    <span>탐지</span>
                  </div>
                </button>
                
                <button
                  onClick={() => setActiveTab('ocr')}
                  className={`flex-1 py-3 px-2 text-xs sm:text-sm font-medium transition-colors ${
                    activeTab === 'ocr' 
                      ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-600' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1">
                    <FileTextIcon />
                    <span>OCR</span>
                  </div>
                </button>
                
                <button
                  onClick={() => setActiveTab('gemini')}
                  className={`flex-1 py-3 px-2 text-xs sm:text-sm font-medium transition-colors ${
                    activeTab === 'gemini' 
                      ? 'bg-green-50 text-green-600 border-b-2 border-green-600' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-center gap-1">
                    <BrainIcon />
                    <span>분석</span>
                  </div>
                </button>
              </div>

              {/* 탭 콘텐츠 */}
              <div className="p-4" style={{ minHeight: '150px', maxHeight: '250px' }}>
                {activeTab === 'detection' && (
                  <div className="h-full overflow-y-auto">
                    <h3 className="text-sm font-semibold text-gray-800 mb-3">식품 탐지 결과</h3>
                    {detectionResults ? (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-600 mb-2">
                          총 {detectionResults.detections?.length || 0}개 탐지
                        </div>
                        {detectionResults.detections?.map((detection, index) => (
                          <div key={index} className="p-2 bg-gray-50 rounded-lg">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-blue-600">
                                {detection.class} → {translateToKorean(detection.class)}
                              </span>
                              <span className="text-xs font-semibold px-2 py-1 rounded-full bg-green-100 text-green-700">
                                {(detection.confidence * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        )) || <p className="text-sm text-gray-500">탐지된 객체가 없습니다.</p>}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">탐지 결과가 없습니다.</p>
                    )}
                  </div>
                )}

                {activeTab === 'ocr' && (
                  <div className="h-full overflow-y-auto">
                    <h3 className="text-sm font-semibold text-gray-800 mb-3">OCR 텍스트</h3>
                    <div className="bg-gray-50 rounded-lg p-3 min-h-[100px]">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap break-words leading-relaxed">
                        {ocrResults || '추출된 텍스트가 없습니다.'}
                      </p>
                    </div>
                  </div>
                )}

                {activeTab === 'gemini' && (
                  <div className="h-full overflow-y-auto">
                    <h3 className="text-sm font-semibold text-gray-800 mb-3">AI 분석 결과</h3>
                    <div className="bg-gray-50 rounded-lg p-3 min-h-[100px]">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap break-words leading-relaxed">
                        {geminiResults || '분석 결과가 없습니다.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 상태바 */}
        <div className="mt-4 bg-white rounded-xl shadow-sm p-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs sm:text-sm text-gray-700 truncate flex-1">
              {statusMessage}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FoodDetectionApp;