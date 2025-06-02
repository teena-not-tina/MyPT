import React, { useState, useRef, useEffect } from 'react';

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
  const [showSaveButton, setShowSaveButton] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [userId, setUserId] = useState('user_' + Date.now()); // 임시 사용자 ID
  const [clearBeforeAnalysis, setClearBeforeAnalysis] = useState(false);
  
  const fileInputRef = useRef(null);
  const analysisTimeoutRef = useRef(null); // 중복 실행 방지용
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://192.168.0.19:8000';

  // 컴포넌트 언마운트 시 timeout 정리
  useEffect(() => {
    return () => {
      if (analysisTimeoutRef.current) {
        clearTimeout(analysisTimeoutRef.current);
      }
    };
  }, []);
  
  // Gemini API 설정
  const GEMINI_API_KEY = process.env.REACT_APP_GEMINI_API_KEY || 'AIzaSyBBHRss0KLaEeeAgggsVOIGQ_zhS5ssDGw';
  const GEMINI_API_URL = process.env.REACT_APP_GEMINI_API_URL || 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent';

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
  const SaveIcon = () => <span className="text-sm">💾</span>;
  const CheckIcon = () => <span className="text-sm">✅</span>;
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

  // MongoDB에 냉장고 데이터 저장 - 현재 상태 기준 저장으로 수정
  const saveToMongoDB = async () => {
    if (fridgeIngredients.length === 0) {
      setStatusMessage('저장할 식재료가 없습니다.');
      return;
    }

    setIsSaving(true);
    console.log('💾 MongoDB 현재 상태 저장 시작:', fridgeIngredients);

    try {
      // 현재 fridgeIngredients 상태를 그대로 저장 (중복 합산 방지)
      const saveData = {
        userId: userId,
        ingredients: fridgeIngredients, // 현재 상태 그대로 저장
        timestamp: new Date().toISOString(),
        totalCount: fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0),
        totalTypes: fridgeIngredients.length
      };

      console.log('💾 저장할 데이터:', saveData);

      // MongoDB 저장 API 호출
      const saveResponse = await fetch(`${API_BASE_URL}/api/fridge/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveData),
      });

      if (saveResponse.ok) {
        const result = await saveResponse.json();
        console.log('✅ MongoDB 저장 성공:', result);
        
        setStatusMessage(`✅ 냉장고 데이터가 성공적으로 저장되었습니다! (총 ${fridgeIngredients.length}종류, ${fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0)}개)`);
        setShowSaveButton(false);
        
        // 성공 후 3초 뒤에 메시지 초기화
        setTimeout(() => {
          setStatusMessage('저장 완료');
        }, 3000);
      } else {
        const errorData = await saveResponse.json();
        throw new Error(errorData.message || '저장 실패');
      }
    } catch (error) {
      console.error('❌ MongoDB 저장 실패:', error);
      
      // 실제 서버가 없을 경우 로컬 저장으로 대체
      try {
        const localData = {
          userId: userId,
          ingredients: fridgeIngredients, // 현재 상태 그대로 저장
          timestamp: new Date().toISOString(),
          totalCount: fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0),
          totalTypes: fridgeIngredients.length
        };
        
        localStorage.setItem(`fridge_${userId}`, JSON.stringify(localData));
        console.log('💾 로컬 저장 완료:', localData);
        setStatusMessage(`📱 로컬에 저장되었습니다 (총 ${fridgeIngredients.length}종류) - 서버 연결 실패`);
        setShowSaveButton(false);
      } catch (localError) {
        console.error('❌ 로컬 저장도 실패:', localError);
        setStatusMessage(`❌ 저장 실패: ${error.message}`);
      }
    } finally {
      setIsSaving(false);
    }
  };

  // MongoDB에서 냉장고 데이터 불러오기 - 기존 데이터 교체 방식
  const loadFromMongoDB = async () => {
    console.log('📥 MongoDB 데이터 로드 시작');

    try {
      const loadResponse = await fetch(`${API_BASE_URL}/api/fridge/load/${userId}`);

      if (loadResponse.ok) {
        const result = await loadResponse.json();
        console.log('✅ MongoDB 로드 성공:', result);
        
        if (result.ingredients && result.ingredients.length > 0) {
          // 기존 데이터를 완전히 교체 (중복 합산 방지)
          setFridgeIngredients(result.ingredients);
          setStatusMessage(`📥 저장된 데이터를 불러왔습니다 (${result.totalTypes}종류, ${result.totalCount}개)`);
          setShowSaveButton(false); // 불러온 후 저장 버튼 숨김
          console.log('🔄 냉장고 데이터 교체 완료:', result.ingredients);
        } else {
          setStatusMessage('저장된 데이터가 없습니다.');
        }
      } else {
        throw new Error('데이터 로드 실패');
      }
    } catch (error) {
      console.error('❌ MongoDB 로드 실패:', error);
      
      // 로컬 저장소에서 시도
      try {
        const localData = localStorage.getItem(`fridge_${userId}`);
        if (localData) {
          const parsed = JSON.parse(localData);
          // 기존 데이터를 완전히 교체 (중복 합산 방지)
          setFridgeIngredients(parsed.ingredients || []);
          setStatusMessage(`📱 로컬 데이터를 불러왔습니다 (${parsed.totalTypes || 0}종류)`);
          setShowSaveButton(false); // 불러온 후 저장 버튼 숨김
          console.log('🔄 로컬 냉장고 데이터 교체 완료:', parsed.ingredients);
        } else {
          setStatusMessage('저장된 데이터가 없습니다.');
        }
      } catch (localError) {
        setStatusMessage('데이터 로드 실패');
      }
    }
  };

  // 냉장고에 식재료 추가 - 완전한 중복 방지 로직
  const addToFridge = (newIngredients) => {
    console.log('🧊 냉장고에 추가 요청:', newIngredients);
    
    setFridgeIngredients(prevIngredients => {
      console.log('🔍 현재 냉장고 상태:', prevIngredients);
      
      // 새로운 배열 생성 (불변성 유지)
      const updatedIngredients = [...prevIngredients];
      let maxId = updatedIngredients.length > 0 ? Math.max(...updatedIngredients.map(item => item.id)) : 0;
      let addedCount = 0;
      let updatedCount = 0;

      newIngredients.forEach(newItem => {
        // 동일한 이름의 식재료가 이미 있는지 확인
        const existingItemIndex = updatedIngredients.findIndex(item => 
          item.name.trim().toLowerCase() === newItem.name.trim().toLowerCase()
        );

        if (existingItemIndex !== -1) {
          // 🔄 기존 식재료 수량 증가
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
          updatedCount++;
          console.log(`🔄 수량 업데이트: ${newItem.name} (${oldQuantity} → ${oldQuantity + newItem.quantity})`);
        } else {
          // ➕ 새로운 식재료 추가
          const newIngredient = {
            id: ++maxId,
            name: newItem.name.trim(),
            quantity: newItem.quantity,
            confidence: newItem.confidence || 0.8,
            source: newItem.source || 'analysis'
          };
          updatedIngredients.push(newIngredient);
          addedCount++;
          console.log(`➕ 새 식재료 추가: ${newItem.name} ${newItem.quantity}개`);
        }
      });

      console.log(`📊 변경 요약: 신규 ${addedCount}개, 업데이트 ${updatedCount}개`);
      console.log('🧊 최종 냉장고 상태:', updatedIngredients);
      
      // 식재료가 있으면 저장 버튼 표시
      if (updatedIngredients.length > 0) {
        setShowSaveButton(true);
      }
      
      return updatedIngredients;
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

  // Gemini API 직접 호출 함수
  const callGeminiAPI = async (prompt) => {
    try {
      console.log('🤖 Gemini API 호출:', prompt);
      
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
            temperature: 0.1,
            topK: 1,
            topP: 1,
            maxOutputTokens: 50,
          }
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
        console.log('✅ Gemini 응답:', text);
        return text.trim();
      } else {
        throw new Error(`Gemini API 오류: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ Gemini API 호출 실패:', error);
      throw error;
    }
  };

  // Gemini를 통한 영어 → 한글 번역
  const translateToKoreanWithGemini = async (englishName) => {
    try {
      console.log(`🌐 Gemini 번역 요청: "${englishName}"`);
      
      const prompt = `다음 영어 식재료명을 정확한 한국어로 번역해주세요. 한 단어로만 답해주세요.

영어 식재료: "${englishName}"

번역 규칙:
- 식재료/음식 이름만 번역
- 한국어 한 단어로만 답변
- 불필요한 설명이나 문장 금지
- 예시: apple → 사과, banana → 바나나, strawberry → 딸기

한국어 번역:`;

      const translatedText = await callGeminiAPI(prompt);
      const cleanTranslation = translatedText.replace(/[^\가-힣]/g, '').trim();
      
      if (cleanTranslation && cleanTranslation.length > 0) {
        console.log(`✅ Gemini 번역 성공: "${englishName}" → "${cleanTranslation}"`);
        return cleanTranslation;
      } else {
        throw new Error('번역 결과가 비어있음');
      }
    } catch (error) {
      console.warn(`❌ Gemini 번역 실패: "${englishName}"`, error);
      // Gemini 실패시 기본 번역 테이블 사용
      return translateToKoreanFallback(englishName);
    }
  };

  // Gemini 실패시 대체 번역 테이블 (최소한의 기본 번역)
  const translateToKoreanFallback = (englishName) => {
    const basicTranslations = {
      'apple': '사과',
      'banana': '바나나', 
      'carrot': '당근',
      'tomato': '토마토',
      'orange': '오렌지',
      'onion': '양파',
      'potato': '감자',
      'cucumber': '오이',
      'lettuce': '상추',
      'broccoli': '브로콜리'
    };
    
    const translated = basicTranslations[englishName.toLowerCase()];
    console.log(`🔄 기본 번역 사용: "${englishName}" → "${translated || englishName}"`);
    return translated || englishName;
  };

  // Detection된 영역을 잘라서 개별 이미지 생성
  const extractIngredientImages = async (detections, originalImage) => {
    if (!detections || detections.length === 0 || !originalImage) {
      console.log('이미지 추출 불가: Detection 결과나 원본 이미지가 없음');
      return [];
    }

    console.log('🖼️ === 식재료 이미지 추출 시작 ===');
    console.log('추출할 Detection 수:', detections.length);

    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const extractedImages = [];
        
        detections.forEach((detection, index) => {
          if (detection.bbox && detection.bbox.length === 4) {
            const [x1, y1, x2, y2] = detection.bbox;
            const width = x2 - x1;
            const height = y2 - y1;
            
            // 유효한 bbox인지 확인
            if (width > 0 && height > 0) {
              // Canvas 크기 설정
              canvas.width = width;
              canvas.height = height;
              
              // 해당 영역만 캔버스에 그리기
              ctx.drawImage(
                img,
                x1, y1, width, height,  // 원본에서 자를 영역
                0, 0, width, height     // 캔버스에 그릴 영역
              );
              
              // Canvas를 base64로 변환
              const croppedImageData = canvas.toDataURL('image/jpeg', 0.8);
              
              extractedImages.push({
                index: index,
                class: detection.class,
                confidence: detection.confidence,
                bbox: detection.bbox,
                imageData: croppedImageData
              });
              
              console.log(`✅ 이미지 추출 ${index + 1}: ${detection.class} (${width}x${height})`);
            } else {
              console.log(`❌ 유효하지 않은 bbox ${index + 1}: ${detection.class}`);
            }
          } else {
            console.log(`❌ bbox 정보 없음 ${index + 1}: ${detection.class}`);
          }
        });
        
        console.log('🖼️ === 이미지 추출 완료 ===');
        console.log('성공적으로 추출된 이미지 수:', extractedImages.length);
        resolve(extractedImages);
      };
      
      img.onerror = () => {
        console.error('❌ 이미지 로드 실패');
        resolve([]);
      };
      
      img.src = originalImage;
    });
  };

  // Detection 결과 처리 - 이미지 포함 버전 (표시 전용)
  const processDetectionResults = async (detections, originalImage) => {
    console.log('🎯 Detection 처리 시작 (표시 전용):', detections);
    
    // 1단계: 개별 이미지 추출
    const extractedImages = await extractIngredientImages(detections, originalImage);
    
    const ingredients = [];
    
    // 2단계: 각 탐지 결과를 Gemini로 번역하고 이미지 포함 (표시만, 대시보드 추가 안함)
    for (let i = 0; i < detections.length; i++) {
      const detection = detections[i];
      const koreanName = await translateToKoreanWithGemini(detection.class);
      
      // 해당하는 추출된 이미지 찾기
      const extractedImage = extractedImages.find(img => img.index === i);
      
      ingredients.push({
        name: koreanName,
        quantity: 1, // 각각 1개씩
        confidence: detection.confidence,
        source: 'detection',
        bbox: detection.bbox,
        originalClass: detection.class,
        imageData: extractedImage ? extractedImage.imageData : null,
        hasImage: !!extractedImage
      });
    }

    console.log('✅ Detection 처리 완료 (표시 전용):', ingredients);
    return ingredients;
  };

  // 스마트 분석 함수 - 개선된 버전 (실제 OCR 패턴 대응)
  const performSmartAnalysis = (text) => {
    console.log('🧠 스마트 분석 시작:', text);
    const results = [];
    
    // 분석 규칙들 (실제 OCR 패턴에 맞게 개선)
    const smartRules = [
      // 아몬드 음료 패턴들 (ml, 추출액 키워드 포함)
      {
        pattern: /(아몬드|ALMOND|almond).*?(ml|mL|ML|추출액|우유|milk|MILK|음료|beverage)/i,
        result: '아몬드우유',
        originalKeyword: 'almond',
        description: '아몬드 + 음료키워드 → 아몬드우유'
      },
      
      // 두유 패턴들
      {
        pattern: /(두유|콩|SOY|soy).*?(ml|mL|ML|추출액|우유|milk|MILK|음료)/i,
        result: '두유',
        originalKeyword: 'soy',
        description: '콩/두유 + 음료키워드 → 두유'
      },
      
      // 오트밀 음료 패턴들
      {
        pattern: /(오트|귀리|OAT|oat).*?(ml|mL|ML|추출액|우유|milk|MILK|음료)/i,
        result: '오트밀크',
        originalKeyword: 'oat',
        description: '오트/귀리 + 음료키워드 → 오트밀크'
      },
      
      // 코코넛 음료 패턴들
      {
        pattern: /(코코넛|coconut|COCONUT).*?(ml|mL|ML|추출액|우유|milk|MILK|음료)/i,
        result: '코코넛밀크',
        originalKeyword: 'coconut',
        description: '코코넛 + 음료키워드 → 코코넛밀크'
      },
      
      // 오렌지 관련 주스 패턴들
      {
        pattern: /(오렌지|ORANGE|orange).*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '오렌지주스',
        originalKeyword: 'orange',
        description: '오렌지 + 주스관련키워드 → 오렌지주스'
      },
      
      // 사과 관련 주스 패턴들  
      {
        pattern: /(사과|APPLE|apple).*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '사과주스',
        originalKeyword: 'apple',
        description: '사과 + 주스관련키워드 → 사과주스'
      },
      
      // 토마토 관련 주스 패턴들
      {
        pattern: /(토마토|TOMATO|tomato).*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '토마토주스',
        originalKeyword: 'tomato', 
        description: '토마토 + 주스관련키워드 → 토마토주스'
      },
      
      // 포도 관련 주스 패턴들
      {
        pattern: /(포도|GRAPE|grape).*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '포도주스',
        originalKeyword: 'grape',
        description: '포도 + 주스관련키워드 → 포도주스'
      },
      
      // 바나나 우유 패턴들
      {
        pattern: /(바나나|BANANA|banana).*?(우유|milk|MILK|ml|mL|ML)/i,
        result: '바나나우유',
        originalKeyword: 'banana',
        description: '바나나 + 우유 → 바나나우유'
      },
      
      // 딸기 우유 패턴들
      {
        pattern: /(딸기|STRAWBERRY|strawberry).*?(우유|milk|MILK|ml|mL|ML)/i,
        result: '딸기우유',
        originalKeyword: 'strawberry',
        description: '딸기 + 우유 → 딸기우유'
      },
      
      // 초콜릿 우유 패턴들
      {
        pattern: /(초콜릿|CHOCOLATE|chocolate).*?(우유|milk|MILK|ml|mL|ML)/i,
        result: '초콜릿우유',
        originalKeyword: 'chocolate',
        description: '초콜릿 + 우유 → 초콜릿우유'
      },
      
      // 복숭아 관련 주스 패턴들
      {
        pattern: /(복숭아|PEACH|peach).*?(100%|주스|juice|JUICE|ml|mL|ML|리터|L|l)/i,
        result: '복숭아주스',
        originalKeyword: 'peach',
        description: '복숭아 + 주스관련키워드 → 복숭아주스'
      },
      
      // 일반 견과류 음료 패턴 (위의 특정 패턴에 안걸릴 경우)
      {
        pattern: /(견과|호두|캐슈|피스타치오).*?(ml|mL|ML|추출액|우유|milk|MILK|음료)/i,
        result: '견과류음료',
        originalKeyword: 'nuts',
        description: '견과류 + 음료키워드 → 견과류음료'
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

  // 🔧 수정된 식재료 분석 실행 - 중복 호출 방지 강화
  const runIngredientAnalysis = async () => {
    if (!imageFile) {
      setStatusMessage('먼저 이미지를 로드하세요.');
      return;
    }

    // 🚨 중복 실행 방지 - 이미 처리 중이면 무시
    if (isProcessing) {
      console.log('⚠️ 이미 분석 중입니다. 중복 실행 방지.');
      return;
    }

    // 🚨 추가 중복 방지 - 짧은 시간 내 연속 호출 방지
    if (analysisTimeoutRef.current) {
      console.log('⚠️ 짧은 시간 내 연속 호출 방지');
      return;
    }

    // 2초간 추가 호출 방지
    analysisTimeoutRef.current = setTimeout(() => {
      analysisTimeoutRef.current = null;
    }, 2000);

    console.log('=== 수정된 분석 시작: Detection & OCR 병행 실행 ===');
    setIsProcessing(true);
    
    try {
      // 🔧 분석 전 냉장고 초기화 옵션
      if (clearBeforeAnalysis) {
        console.log('🧹 분석 전 냉장고 초기화');
        setFridgeIngredients([]);
      }

      // 1단계: Detection과 OCR 병행 실행
      setProcessingStep('식품 탐지 및 텍스트 추출 중...');
      setStatusMessage('식품 탐지 및 텍스트 추출 중...');

      let detections = [];
      let ocrText = '';
      let detectionSuccess = false;
      let ocrSuccess = false;
      
      // Detection과 OCR을 병행으로 실행
      const [detectionResult, ocrResult] = await Promise.allSettled([
        // Detection API 호출
        (async () => {
          try {
            const detectFormData = new FormData();
            detectFormData.append('file', imageFile);
            detectFormData.append('confidence', confidence);

            const detectResponse = await fetch(`${API_BASE_URL}/api/detect`, {
              method: 'POST',
              body: detectFormData,
            });

            if (detectResponse.ok) {
              const result = await detectResponse.json();
              console.log('✅ Detection API 성공:', result);
              setDetectionResults(result);
              detections = result.detections || [];
              return { success: true, data: detections };
            } else {
              throw new Error(`Detection API 실패: ${detectResponse.status}`);
            }
          } catch (error) {
            console.log('❌ Detection API 오류:', error.message);
            return { success: false, error: error.message };
          }
        })(),
        
        // OCR API 호출
        (async () => {
          try {
            const ocrFormData = new FormData();
            ocrFormData.append('file', imageFile);

            const ocrResponse = await fetch(`${API_BASE_URL}/api/ocr`, {
              method: 'POST',
              body: ocrFormData,
            });

            if (ocrResponse.ok) {
              const result = await ocrResponse.json();
              console.log('✅ OCR API 성공:', result);
              const text = result.text || '';
              setOcrResults(text);
              return { success: true, data: text };
            } else {
              throw new Error(`OCR API 실패: ${ocrResponse.status}`);
            }
          } catch (error) {
            console.log('❌ OCR API 오류:', error.message);
            return { success: false, error: error.message };
          }
        })()
      ]);

      // 결과 처리
      if (detectionResult.status === 'fulfilled' && detectionResult.value.success) {
        detectionSuccess = true;
        detections = detectionResult.value.data;
      }

      if (ocrResult.status === 'fulfilled' && ocrResult.value.success) {
        ocrSuccess = true;
        ocrText = ocrResult.value.data;
      }

      // 2단계: 결과 처리 로직 (수정된 부분)
      setProcessingStep('결과 처리 중...');
      
      let finalIngredients = [];
      let processingMethod = '';

      // 📌 핵심 변경: Detection과 OCR 모두 성공한 경우 OCR 우선 처리
      if (detectionSuccess && ocrSuccess && detections.length > 0 && ocrText && ocrText.trim().length > 2) {
        console.log('🔄 Detection과 OCR 모두 성공 → OCR 우선 처리 (대시보드용)');
        processingMethod = 'ocr_priority';
        
        // Detection 결과는 표시만 (대시보드에 추가 안함) - processDetectionResults 호출하지 않음
        console.log('🎯 Detection 결과는 표시만 함 (대시보드 추가 안함)');
        
        // OCR 결과만 대시보드에 추가
        const hasKorean = /[가-힣]/.test(ocrText);
        const hasEnglish = /[a-zA-Z]/.test(ocrText);
        const hasNumbers = /\d/.test(ocrText);
        
        if (hasKorean || hasEnglish || hasNumbers) {
          try {
            // Gemini OCR 분석 - 스마트 추론
            console.log('🧠 Gemini OCR 추론 요청 (우선 처리):', ocrText);
            
            const ocrAnalysisPrompt = `다음은 냉장고나 식품 관련 OCR로 추출된 텍스트입니다. 이를 분석하여 정확한 식재료나 음식 제품을 추론하고 "식재료명 개수개" 형식으로 출력해주세요.

OCR 추출 텍스트: "${ocrText}"

🧠 스마트 추론 규칙:
1. 식재료 + 용량/음료 키워드 = 음료로 판단
   - "아몬드 190ml 추출액" → 아몬드우유
   - "오렌지 100% 주스" → 오렌지주스
   - "사과 200ml" → 사과주스  
   - "토마토 juice" → 토마토주스
   - "콩 추출액 ml" → 두유

2. 과일/견과류 + 우유 키워드 = 우유음료로 판단
   - "바나나 우유" → 바나나우유
   - "딸기 MILK" → 딸기우유
   - "초콜릿 우유" → 초콜릿우유
   - "아몬드 milk" → 아몬드우유

3. 용량 기반 개수 추론
   - 200ml 이하 = 1개
   - 500ml = 2-3개  
   - 1L = 4-5개

4. 브랜드명/용량 제거 후 핵심 제품명만 추출
   - "그린덴마크 아몬드 190ml 추출액" → "아몬드우유 1개"
   - "델몬트 오렌지 100% (210ml)" → "오렌지주스 1개"
   - "서울우유 바나나맛 (200ml)" → "바나나우유 1개"

5. ml, 추출액, 음료 키워드가 있으면 음료로 우선 판단
   - "아몬드 추출액 95%" → "아몬드우유"
   - "콩 추출액 ml" → "두유"
   - "귀리 음료" → "오트밀크"

6. 불분명한 경우 가장 가능성 높은 식재료로 추론
   - "Fresh Apple" → "사과 1개"
   - "Premium 토마토" → "토마토 1개"

예시:
입력: "그린덴마크 아몬드 190ml 추출액 95%"
출력: 아몬드우유 1개

입력: "오렌지 100% 주스 (210ml) 바나나우유 사과"
출력:
오렌지주스 1개
바나나우유 1개  
사과 1개

입력: "${ocrText}"
출력:`;

            const geminiOcrResult = await callGeminiAPI(ocrAnalysisPrompt);
            console.log('✅ Gemini OCR 추론 완료 (우선 처리):', geminiOcrResult);
            
            setGeminiResults(`OCR 우선 처리 - Gemini 추론 결과:\n${geminiOcrResult}`);
            
            // Gemini 추론 결과를 파싱하여 식재료 추출 (이것만 대시보드에 추가)
            finalIngredients = processOCRResults(geminiOcrResult);
            setActiveTab('gemini');
            console.log('✅ OCR 우선 처리로 대시보드에 추가된 식재료:', finalIngredients);
            
          } catch (geminiError) {
            console.log('❌ Gemini OCR 추론 실패, 직접 처리로 대체');
            console.error('Gemini 오류 상세:', geminiError);
            
            // Gemini 실패시 OCR 텍스트 직접 처리 (이것만 대시보드에 추가)
            finalIngredients = processOCRResults(ocrText);
            setGeminiResults('OCR 우선 처리 - 직접 처리 결과:\n' + finalIngredients.map(item => `${item.name} ${item.quantity}개`).join('\n'));
            setActiveTab('ocr');
            console.log('✅ OCR 직접 처리로 대시보드에 추가된 식재료:', finalIngredients);
          }
        }
      }
      // Detection만 성공한 경우
      else if (detectionSuccess && detections.length > 0) {
        console.log('🎯 Detection만 성공 → Detection 처리');
        processingMethod = 'detection';
        
        try {
          finalIngredients = await processDetectionResults(detections, currentImage);
          if (finalIngredients && finalIngredients.length > 0) {
            setGeminiResults('Detection Gemini 번역:\n' + finalIngredients.map(item => `${item.name} ${item.quantity}개`).join('\n'));
            setActiveTab('detection');
            console.log('✅ Detection으로 대시보드에 추가된 식재료:', finalIngredients);
          } else {
            console.log('⚠️ Detection 처리 결과가 비어있음');
            finalIngredients = [];
          }
        } catch (detectionError) {
          console.error('❌ Detection 처리 중 오류:', detectionError);
          finalIngredients = [];
        }
      }
      // OCR만 성공한 경우
      else if (ocrSuccess && ocrText && ocrText.trim().length > 2) {
        console.log('📄 OCR만 성공 → OCR 처리');
        processingMethod = 'ocr';
        
        const hasKorean = /[가-힣]/.test(ocrText);
        const hasEnglish = /[a-zA-Z]/.test(ocrText);
        const hasNumbers = /\d/.test(ocrText);
        
        if (hasKorean || hasEnglish || hasNumbers) {
          try {
            const ocrAnalysisPrompt = `다음은 냉장고나 식품 관련 OCR로 추출된 텍스트입니다. 이를 분석하여 정확한 식재료나 음식 제품을 추론하고 "식재료명 개수개" 형식으로 출력해주세요.

OCR 추출 텍스트: "${ocrText}"

🧠 스마트 추론 규칙:
1. 식재료 + 용량/음료 키워드 = 음료로 판단
   - "아몬드 190ml 추출액" → 아몬드우유
   - "오렌지 100% 주스" → 오렌지주스
   - "콩 추출액 ml" → 두유
2. 과일/견과류 + 우유 키워드 = 우유음료로 판단
3. 용량 기반 개수 추론
4. 브랜드명/용량 제거 후 핵심 제품명만 추출
5. ml, 추출액, 음료 키워드가 있으면 음료로 우선 판단
6. 불분명한 경우 가장 가능성 높은 식재료로 추론

입력: "${ocrText}"
출력:`;

            const geminiOcrResult = await callGeminiAPI(ocrAnalysisPrompt);
            console.log('✅ Gemini OCR 추론 완료:', geminiOcrResult);
            
            setGeminiResults(`Gemini OCR 추론 결과:\n${geminiOcrResult}`);
            
            finalIngredients = processOCRResults(geminiOcrResult);
            setActiveTab('ocr');
            console.log('✅ OCR로 대시보드에 추가된 식재료:', finalIngredients);
            
          } catch (geminiError) {
            console.log('❌ Gemini OCR 추론 실패, 직접 처리로 대체');
            finalIngredients = processOCRResults(ocrText);
            setGeminiResults('OCR 직접 처리 결과:\n' + finalIngredients.map(item => `${item.name} ${item.quantity}개`).join('\n'));
            setActiveTab('ocr');
            console.log('✅ OCR 직접 처리로 대시보드에 추가된 식재료:', finalIngredients);
          }
        }
      }

      // 둘 다 실패하면 에러 메시지 표시
      if (finalIngredients.length === 0) {
        console.log('❌ Detection과 OCR 모두 실패 또는 결과 없음');
        
        if (!detectionSuccess && !ocrSuccess) {
          setStatusMessage('❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
        } else if (!detectionSuccess && ocrSuccess) {
          setStatusMessage('❌ Detection API 실패. OCR은 성공했지만 추출된 식재료가 없습니다.');
        } else if (detectionSuccess && !ocrSuccess) {
          setStatusMessage('❌ OCR API 실패. Detection 결과가 표시됩니다.');
        } else {
          setStatusMessage('❌ 분석된 식재료가 없습니다.');
        }
      }

      // 3단계: 냉장고에 추가 - 중복 방지 강화
      if (finalIngredients.length > 0) {
        console.log('🧊 냉장고에 추가 시작:', finalIngredients);
        
        // 한 번만 호출되도록 보장
        setTimeout(() => {
          addToFridge(finalIngredients);
        }, 100);
        
        // 소스별 개수 계산
        const ocrCount = finalIngredients.filter(item => item.source === 'ocr' || item.source === 'ocr_smart').length;
        const detectionCount = finalIngredients.filter(item => item.source === 'detection').length;
        
        let sourceText = '';
        if (processingMethod === 'ocr_priority') {
          sourceText = ` (OCR 우선 처리: ${ocrCount}개, Detection 표시만)`;
        } else if (processingMethod === 'detection') {
          sourceText = ` (Detection 분석: ${detectionCount}개)`;
        } else if (processingMethod === 'ocr') {
          sourceText = ` (OCR 분석: ${ocrCount}개)`;
        }
        
        setStatusMessage(`✅ 분석 완료: ${finalIngredients.length}개 식재료 추가됨${sourceText}`);
      }

    } catch (error) {
      console.error('❌ 전체 분석 오류:', error);
      setStatusMessage('분석 중 오류가 발생했습니다');
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
      console.log('=== 수정된 분석 완료 ===');
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

          {/* 냉장고 저장 및 불러오기 버튼들 */}
          {showSaveButton && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <button
                onClick={saveToMongoDB}
                disabled={isSaving || fridgeIngredients.length === 0}
                className="flex items-center justify-center gap-2 py-3 px-4 bg-green-600 text-white rounded-lg font-medium transition-all duration-200 active:scale-95 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isSaving ? <LoadingSpinner /> : <SaveIcon />}
                <span className="text-sm">
                  {isSaving ? '저장 중...' : `냉장고 저장 (${fridgeIngredients.length}종류)`}
                </span>
              </button>

              <button
                onClick={loadFromMongoDB}
                className="flex items-center justify-center gap-2 py-3 px-4 bg-blue-600 text-white rounded-lg font-medium transition-all duration-200 active:scale-95 hover:bg-blue-700"
              >
                <CheckIcon />
                <span className="text-sm">데이터 불러오기</span>
              </button>
            </div>
          )}

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

          {/* 분석 전 초기화 옵션 */}
          <div className="flex items-center gap-3 pt-2 border-t border-gray-200">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={clearBeforeAnalysis}
                onChange={(e) => setClearBeforeAnalysis(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">분석 전 냉장고 초기화</span>
            </label>
            <div className="text-xs text-gray-500">
              (동일 이미지 재분석 시 중복 방지)
            </div>
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
                            {(ingredient.source === 'ocr' || ingredient.source === 'ocr_smart') && '📄 OCR'}
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
                          총 {detectionResults.detections?.length || 0}개 탐지 (표시만, 대시보드 추가 안됨)
                        </div>
                        {detectionResults.detections?.map((detection, index) => (
                          <div key={index} className="p-2 bg-gray-50 rounded-lg">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-blue-600">
                                {detection.class}
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