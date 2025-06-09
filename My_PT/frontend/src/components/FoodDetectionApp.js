// components/FoodDetectionApp.js
import React, { useState, useRef, useEffect } from 'react';

// Services
import apiService from '../services/apiService';
import geminiService from '../services/geminiService';

// Enhanced OCR Inference
import { 
  enhancedOCRInference, 
  summarizeOCRText,
  extractKeywordsFromOCR 
} from '../utils/enhancedOCRInference';

// Utils
import { 
  detectBrandAndProductAdvanced,
  isBeverageByMl,
  detectBrandOnly,
  getRepresentativeProduct
} from '../utils/brandDetection';
import { 
  extractFoodNameFromGeminiResult,
  checkBasicFoodDictionary
} from '../utils/foodProcessing';
import {
  processImageFiles,
  createDragHandlers,
  validateImage
} from '../utils/imageUtils';
import {
  performAdvancedInference,
  performAdvancedFallback,
  inferFromTextMaximally
} from '../utils/inferenceEngine';
import {
  extractIngredientsFromText,
  classifyByIngredientsOnly
} from '../utils/ingredientClassification';
import {
  convertV3DataToCurrentFormat,
  findV3DataInLocalStorage,
  findV3DataForUser,
  mergeIngredientData
} from '../utils/legacyDataMigration';

// 아이콘 컴포넌트들
const Icons = {
  Cooking: () => <span className="text-2xl md:text-3xl">👨‍🍳</span>,
  Eating: () => <span className="text-2xl md:text-3xl">🍽️</span>,
  Upload: () => <span className="text-sm">📁</span>,
  Eye: () => <span className="text-sm">👁️</span>,
  Brain: () => <span className="text-sm">🧠</span>,
  FileText: () => <span className="text-sm">📄</span>,
  Fridge: () => <span className="text-lg md:text-xl">🧊</span>,
  Back: () => <span className="text-sm">←</span>,
  Plus: () => <span className="text-sm">+</span>,
  Minus: () => <span className="text-sm">-</span>,
  Delete: () => <span className="text-sm">🗑️</span>,
  Save: () => <span className="text-sm">💾</span>,
  Check: () => <span className="text-sm">✅</span>,
  Close: () => <span className="text-sm">✕</span>,
  Edit: () => <span className="text-sm">✏️</span>,
  All: () => <span className="text-sm">🔄</span>,
  FatSecret: () => <span className="text-sm">🔍</span>,
  Dashboard: () => <span className="text-sm">📊</span>,
  Nutrition: () => <span className="text-sm">🥗</span>,
  Link: () => <span className="text-sm">🔗</span>,
  LoadingSpinner: () => (
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
  )
};

// 안전한 문자열 처리를 위한 헬퍼 함수
const safeStringTrim = (str) => {
  return (str && typeof str === 'string') ? str.trim() : '';
};

const FoodDetectionApp = () => {
  // 상태 관리
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
  
  // 직접 추가 기능 관련 상태
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualIngredientName, setManualIngredientName] = useState('');
  const [manualIngredientQuantity, setManualIngredientQuantity] = useState(1);
  const [isAddingManual, setIsAddingManual] = useState(false);
  
  // Detection 결과 표시용 번역 캐시
  const [detectionTranslations, setDetectionTranslations] = useState({});

  // FatSecret 검색 활성화 상태 (UI에 남아있음)
  const [fatSecretSearchEnabled, setFatSecretSearchEnabled] = useState(false);

  // Refs
  const fileInputRef = useRef(null);
  const analysisTimeoutRef = useRef(null);
  const manualInputRef = useRef(null);

  // useEffect hooks
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

  // Detection 결과의 번역을 캐시하는 함수
  const getOrTranslateDetection = async (englishName) => {
    if (detectionTranslations[englishName]) {
      return detectionTranslations[englishName];
    }
    const translated = await geminiService.translateDetectionResult(englishName);
    if (translated) {
      setDetectionTranslations(prev => ({
        ...prev,
        [englishName]: translated
      }));
    }
    return translated || checkBasicFoodDictionary(englishName);
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

  // 수정된 addManualIngredient 함수
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
    
    // 🔧 안전한 문자열 비교
    const existingIngredient = fridgeIngredients.find(item => 
      safeStringTrim(item.name).toLowerCase() === ingredientName.toLowerCase()
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
        ingredients: fridgeIngredients.map(ingredient => ({
          id: ingredient.id,
          name: ingredient.name,
          quantity: ingredient.quantity || 1,
          confidence: ingredient.confidence || 0.8,
          source: ingredient.source || "manual"
        })),
        timestamp: new Date().toISOString(),
        totalCount: fridgeIngredients.reduce((sum, item) => sum + item.quantity, 0),
        totalTypes: fridgeIngredients.length
      };
      console.log('백엔드 호환 데이터 저장:', saveData);
      const result = await apiService.saveFridgeData(saveData);
      console.log('✅ 서버 저장 성공:', result);
      setStatusMessage(`✅ 냉장고 데이터가 성공적으로 저장되었습니다! (총 ${fridgeIngredients.length}종류)`);
      setShowSaveButton(false);
      setTimeout(() => {
        setStatusMessage('저장 완료');
      }, 3000);
    } catch (error) {
      console.error('❌ MongoDB 저장 실패:', error);
      try {
        const localData = {
          userId: userId,
          createdAt: new Date().toISOString(),
          ingredients: fridgeIngredients.map(ingredient => ({
            id: ingredient.id,
            name: ingredient.name,
            confidence: ingredient.confidence || 0.8
          })),
          timestamp: new Date().toISOString()
        };
        localStorage.setItem(`fridge_data_${userId}`, JSON.stringify(localData));
        setStatusMessage(`📱 로컬에 저장되었습니다 (총 ${fridgeIngredients.length}종류) - 서버: ${error.message}`);
        setShowSaveButton(false);
      } catch (localError) {
        setStatusMessage(`❌ 저장 실패: ${error.message}`);
      }
    } finally {
      setIsSaving(false);
    }
  };

  const loadFromMongoDB = async () => {
    try {
      const result = await apiService.loadFridgeData(userId);
      if (result.ingredients && result.ingredients.length > 0) {
        const convertedIngredients = result.ingredients.map((ingredient, index) => ({
          id: ingredient.id || (Date.now() + index),
          name: ingredient.name,
          quantity: ingredient.quantity || 1,
          confidence: ingredient.confidence || 0.8,
          source: ingredient.source || 'loaded'
        }));
        setFridgeIngredients(convertedIngredients);
        setStatusMessage(`📥 저장된 데이터를 불러왔습니다 (${convertedIngredients.length}종류)`);
        setShowSaveButton(false);
      } else {
        setStatusMessage('저장된 데이터가 없습니다.');
      }
    } catch (error) {
      console.error('❌ MongoDB 로드 실패:', error);
      setStatusMessage('저장된 데이터가 없습니다.');
    }
  };

  const loadFromV3Data = async () => {
    try {
      setStatusMessage('📥 버전3 서버 데이터를 확인하는 중...');
      const result = await apiService.loadFridgeData(userId);
      if (result.success && result.ingredients && result.ingredients.length > 0) {
        const shouldUse = window.confirm(`서버에 ${result.ingredients.length}개의 식재료 데이터가 있습니다.\n이 데이터를 불러오시겠습니까?\n\n확인: 서버 데이터 사용\n취소: 로컬 버전3 데이터 찾기`);
        if (shouldUse) {
          setFridgeIngredients(result.ingredients);
          setStatusMessage(`📥 서버 데이터를 불러왔습니다 (${result.ingredients.length}개 항목)`);
          setShowSaveButton(false);
          return;
        }
      }
      setStatusMessage('📥 버전3 API가 없습니다. 로컬 데이터를 자동으로 확인합니다...');
      setTimeout(() => {
        loadFromV3LocalStorage();
      }, 1000);
    } catch (error) {
      console.error('❌ 서버 연결 실패:', error);
      setStatusMessage('❌ 서버 연결 실패. 로컬 버전3 데이터를 확인합니다...');
      setTimeout(() => {
        loadFromV3LocalStorage();
      }, 1000);
    }
  };

  const loadFromV3LocalStorage = () => {
    try {
      setStatusMessage('📥 로컬 버전3 데이터를 확인하는 중...');
      const searchResult = findV3DataInLocalStorage();
      if (searchResult.foundData.length > 0) {
        const firstFound = searchResult.foundData[0];
        const convertedData = convertV3DataToCurrentFormat(firstFound.data);
        const shouldMerge = fridgeIngredients.length > 0 && 
          window.confirm(`현재 냉장고에 ${fridgeIngredients.length}개의 식재료가 있습니다. 버전3 데이터(${convertedData.length}개)와 병합하시겠습니까?\n\n확인: 병합\n취소: 덮어쓰기`);
        if (shouldMerge) {
          const { mergedData, addedCount } = mergeIngredientData(fridgeIngredients, convertedData);
          setFridgeIngredients(mergedData);
          setStatusMessage(`📥 버전3 데이터를 병합했습니다! (${addedCount}개 새로 추가, 키: ${firstFound.key})`);
        } else {
          setFridgeIngredients(convertedData);
          setStatusMessage(`📥 버전3 데이터를 불러왔습니다! (${convertedData.length}개 항목, 키: ${firstFound.key})`);
        }
        setShowSaveButton(true);
        console.log(`✅ 버전3 데이터 로드 성공:`, {
          usedKey: firstFound.key,
          originalData: firstFound.data,
          convertedData,
          totalKeysChecked: searchResult.totalChecked
        });
      } else {
        setStatusMessage(`❌ 로컬 스토리지에서 버전3 데이터를 찾을 수 없습니다. (${searchResult.totalChecked}개 키 확인됨)`);
        console.log('🔍 확인된 로컬 스토리지 키들:', Object.keys(localStorage));
      }
    } catch (error) {
      console.error('❌ 로컬 버전3 데이터 로드 실패:', error);
      setStatusMessage('❌ 로컬 버전3 데이터 불러오기에 실패했습니다.');
    }
  };

  // 수정된 addToFridge 함수
  const addToFridge = (newIngredients) => {
    setFridgeIngredients(prevIngredients => {
      const updatedIngredients = [...prevIngredients];
      let maxId = updatedIngredients.length > 0 ? Math.max(...updatedIngredients.map(item => item.id)) : 0;
      
      newIngredients.forEach(newItem => {
        // 🔧 안전한 데이터 검증
        if (!newItem || !newItem.name) {
          console.warn('잘못된 식재료 데이터:', newItem);
          return;
        }

        // 🔧 안전한 문자열 비교
        const existingItemIndex = updatedIngredients.findIndex(item => 
          safeStringTrim(item.name).toLowerCase() === safeStringTrim(newItem.name).toLowerCase()
        );
        
        if (existingItemIndex !== -1) {
          const oldQuantity = updatedIngredients[existingItemIndex].quantity;
          updatedIngredients[existingItemIndex] = {
            ...updatedIngredients[existingItemIndex],
            quantity: oldQuantity + (newItem.quantity || 1),
            confidence: Math.max(
              updatedIngredients[existingItemIndex].confidence || 0, 
              newItem.confidence || 0
            ),
            source: newItem.source || updatedIngredients[existingItemIndex].source
          };
        } else {
          const newIngredient = {
            id: ++maxId,
            name: safeStringTrim(newItem.name), // 🔧 안전한 문자열 처리
            quantity: newItem.quantity || 1,
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
  const { handleDragOver, handleDragLeave, handleDrop } = createDragHandlers(
    setIsDragOver,
    async (result) => {
      if (result.success) {
        setImages(prev => [...prev, ...result.images]);
        setSelectedImageIndex(images.length);
        setStatusMessage(result.message);
      } else {
        setStatusMessage(result.message);
      }
    }
  );

  // 이미지 처리 함수들
  const handleImageLoad = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      const result = await processImageFiles(files);
      if (result.success) {
        setImages(prev => [...prev, ...result.images]);
        setSelectedImageIndex(images.length);
        setStatusMessage(result.message);
      }
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

  // 고급 분석 함수 (FatSecret 완전 제거)
  const analyzeImageAdvanced = async (imageIndex) => {
    const validation = validateImage(imageIndex, images);
    if (!validation.valid) {
      setStatusMessage(validation.message);
      return;
    }
    if (isProcessing) {
      return;
    }
    const image = validation.image;
    setIsProcessing(true);
    setProcessingImageIndex(imageIndex);
    try {
      setProcessingStep(`이미지 ${imageIndex + 1} 향상된 추론 중...`);
      setStatusMessage(`이미지 ${imageIndex + 1} 향상된 추론 중...`);
      let finalIngredients = [];
      let detectionResult = null;
      let ocrResult = null;
      
      // 1단계: OCR API 호출 - 수정된 부분
      setProcessingStep(`1/4 - 텍스트 추출 중...`);
      try {
        // ✅ 수정: image.dataUrl 대신 image.file 사용
        ocrResult = await apiService.performOCR(image.file);
        setOcrResults(prev => ({
          ...prev,
          [image.id]: ocrResult
        }));
        console.log(`📄 OCR 결과: "${ocrResult.text || '텍스트 없음'}"`);
      } catch (error) {
        console.error('OCR 실패:', error);
      }
      
      // 2단계: Detection API 호출
      setProcessingStep(`2/4 - 객체 탐지 중...`);
      try {
        detectionResult = await apiService.performDetection(image.file, confidence);
        setDetectionResults(prev => ({
          ...prev,
          [image.id]: detectionResult
        }));
        console.log(`🎯 Detection 결과: ${detectionResult.detections?.length || 0}개 탐지`);
      } catch (error) {
        console.error('Detection 실패:', error);
      }
      
      // 3단계: 향상된 추론 시스템 적용
      setProcessingStep(`3/4 - 향상된 추론 시스템 적용 중...`);
      const hasOcrText = ocrResult && ocrResult.text && ocrResult.text.trim().length > 0;
      const hasDetectionResults = detectionResult && detectionResult.detections && detectionResult.detections.length > 0;
      
      if (hasOcrText) {
        // OCR 텍스트가 있으면 4단계 추론 적용
        try {
          const inferenceResult = await callGeminiAPIWithAdvancedInference(ocrResult.text);
          if (inferenceResult && inferenceResult.ingredient) {
            setGeminiResults(prev => ({
              ...prev,
              [image.id]: {
                text: inferenceResult.ingredient,
                extractedText: ocrResult.text,
                source: 'ocr_4stage_inference',
                mode: 'OCR 4단계',
                inferenceSource: inferenceResult.source,
                inferenceConfidence: inferenceResult.confidence
              }
            }));
            finalIngredients.push({
              name: inferenceResult.ingredient,
              quantity: 1,
              confidence: inferenceResult.confidence || 0.95,
              source: inferenceResult.source || '4stage_ocr'
            });
          }
        } catch (error) {
          console.error('❌ OCR 기반 향상된 추론 오류:', error);
        }
      } else if (hasDetectionResults) {
        // OCR 텍스트가 없을 때는 Detection만 사용
        console.log("🎯 과일 시각적 보정 시스템 적용");
        // 🍎 [추가] 색상 정보 가져오기
        const colorInfo = detectionResult.enhanced_info?.color_analysis;
        
        try {
            for (let detection of detectionResult.detections.filter(d => d.confidence >= 0.5)) {
              // 🍎 [추가] 보정된 탐지 결과를 저장할 변수 (스프레드 연산자 대신 명시적 복사)
              let correctedDetection = {
                id: detection.id,
                class: detection.class,
                korean_name: detection.korean_name,
                confidence: detection.confidence,
                bbox: detection.bbox,
                center: detection.center,
                width: detection.width,
                height: detection.height,
                area: detection.area
                };
              let corrected = false; // 🍎 [추가] 보정 여부 체크
              // 🍎 [중요] 색상 정보 상세 분석
                console.log('🎨 색상 분석:', {
                  primary_color: colorInfo?.primary_color,
                  dominant_colors: colorInfo?.dominant_colors,
                  detected_class: detection.class,
                  aspect_ratio: detection.height && detection.width ? (detection.height / detection.width).toFixed(2) : 'unknown'
                });
                              
                // 🥑 [개선] 아보카도 보정 - 훨씬 더 정확한 조건
                if (detection.class === 'apple') {
                  // 1. 색상 조건 (더 포괄적)
                  const isAvocadoColor = colorInfo?.primary_color && (
                    colorInfo.primary_color.includes('초록') || 
                    colorInfo.primary_color.includes('황록') ||
                    colorInfo.primary_color.includes('녹색') ||
                    colorInfo.primary_color === '연한초록색' ||
                    colorInfo.primary_color === '중간초록색' ||
                    colorInfo.primary_color === '진한초록색' ||
                    colorInfo.primary_color.includes('어두운') ||
                    colorInfo.primary_color.includes('갈색')
                  );
                  
                  // 2. 형태 조건 (아보카도는 다양한 형태 가능)
                  const isAvocadoShape = detection.height && detection.width && (
                    (detection.height / detection.width) > 0.8 ||  // 세로형
                    (detection.height / detection.width) < 0.6     // 반으로 자른 경우 가로형
                  );
                  
                  // 3. 크기 조건 (적절한 크기)
                  const isAvocadoSize = true; // 일단 크기 조건 무시하고 테스트

                  // 4. 신뢰도 조건 (apple로 탐지되었지만 신뢰도가 낮은 경우)
                  const isLowConfidenceApple = detection.confidence < 0.7;
                  
                  console.log('🥑 아보카도 조건 체크:', { 
                    isAvocadoColor, 
                    isAvocadoShape, 
                    isAvocadoSize,
                    isLowConfidenceApple,
                    primary_color: colorInfo?.primary_color,
                    aspect_ratio: detection.height && detection.width ? (detection.height / detection.width).toFixed(2) : 'unknown',
                    area: detection.area,
                    confidence: detection.confidence
                  });
                  
                   // 조건: (색상이 아보카도 같거나) OR (형태가 특이하거나) OR (신뢰도가 낮은 apple)
                    if ((isAvocadoColor || isAvocadoShape || isLowConfidenceApple) && isAvocadoSize) {
                      correctedDetection.class = 'avocado';
                      correctedDetection.confidence = Math.min(0.9, detection.confidence + 0.3);
                      correctedDetection.corrected = true;
                      correctedDetection.original_class = 'apple';
                      corrected = true;
                      console.log('🥑 아보카도 보정 적용:', detection.class, '→ avocado');
                    }
                  }
               // 🍑 [수정] 복숭아 보정 - 아보카도가 아닌 경우만 적용
              else if (detection.class === 'apple' && !corrected && // 아보카도로 보정되지 않은 경우만
                colorInfo?.primary_color && 
                (colorInfo.primary_color.includes('주황') ||
                colorInfo.primary_color === '연한주황색' ||
                colorInfo.primary_color === '진한주황색') &&
                detection.height && detection.width && 
                (detection.height / detection.width) >= 0.7 && (detection.height / detection.width) <= 1.3 && // 적절한 비율
                detection.confidence > 0.6) {  // 어느 정도 신뢰도가 있는 경우만
                
                correctedDetection.class = 'peach';
                correctedDetection.confidence = Math.min(0.9, detection.confidence + 0.2);
                correctedDetection.corrected = true;
                correctedDetection.original_class = 'apple';
                corrected = true;
                console.log('🍑 복숭아 보정 적용: apple → peach');
              }     
              // 🥝 [추가] 키위 보정 로직: potato나 orange가 갈색/황록색인 경우
              else if ((detection.class === 'potato' || detection.class === 'orange') &&
                  colorInfo && colorInfo.primary_color && 
                  (colorInfo.primary_color.includes('갈색') || colorInfo.primary_color.includes('황록'))) {
                
                // 🥝 [추가] 키위로 보정
                correctedDetection.class = 'kiwi';
                correctedDetection.confidence = Math.min(0.85, detection.confidence + 0.15);
                correctedDetection.corrected = true;
                correctedDetection.original_class = detection.class;
                corrected = true;
                console.log('🥝 키위 보정 적용:', detection.class, '→ kiwi');
              }
            // 🍑 [수정] onion → peach 보정 (별도 처리)
              else if (detection.class === 'onion' &&
                colorInfo?.primary_color && 
                (colorInfo.primary_color.includes('주황') ||
                colorInfo.primary_color === '연한주황색')) {
              
              correctedDetection.class = 'peach';
              correctedDetection.confidence = Math.min(0.9, detection.confidence + 0.2);
              correctedDetection.corrected = true;
              correctedDetection.original_class = 'onion';
              corrected = true;
              console.log('🍑 복숭아 보정 적용: onion → peach');
            }
            // 🍑 [추가] 복숭아 보정 로직: apple이나 onion이 주황색인 경우
            else if (colorInfo?.primary_color && 
              (colorInfo.primary_color.includes('주황') || 
              colorInfo.primary_color === '연한주황색' ||
              colorInfo.primary_color === '진한주황색') &&
              detection.height && detection.width && 
              (detection.height / detection.width) >= 0.7 && (detection.height / detection.width) <= 1.3 && // 적절한 비율
              detection.confidence > 0.6) {  // 어느 정도 신뢰도가 있는 경우만
              
              correctedDetection.class = 'peach';
              correctedDetection.confidence = Math.min(0.9, detection.confidence + 0.2);
              correctedDetection.corrected = true;
              correctedDetection.original_class = 'apple';
              corrected = true;
              console.log('🍑 복숭아 보정 적용: apple → peach');
            }
            
            // 🍎 [추가] 번역 및 최종 식재료 추가
            const classToTranslate = correctedDetection.class;
            let translatedName = null;
            
            // 🍎 [추가] 과일 직접 번역 (빠른 처리)
            const fruitTranslations = {
              'avocado': '아보카도',
              'kiwi': '키위', 
              'peach': '복숭아',
              'apple': '사과',
              'orange': '오렌지',
              'banana': '바나나',
              'potato': '감자',
              'onion': '양파'
            };
            
            // 🍎 [추가] 직접 번역이 있으면 사용, 없으면 Gemini 번역
            if (fruitTranslations[classToTranslate]) {
              translatedName = fruitTranslations[classToTranslate];
            } else {
              // 🍎 [기존] 기존 번역 로직 유지
              getOrTranslateDetection(correctedDetection.class);
              translatedName = await geminiService.translateDetectionResult(classToTranslate);
            }
            
            // 🍎 [수정] 최종 식재료 추가 (소스 정보 개선)
            if (translatedName) {
              finalIngredients.push({
                name: translatedName,
                quantity: 1,
                confidence: correctedDetection.confidence,
                source: corrected ? 'fruit_correction' : 'detection' // 🍎 [추가] 보정 여부에 따른 소스 구분
              });
            }
          }
          
          // 🍎 [추가] Gemini 결과에 과일 보정 정보 추가
          if (finalIngredients.length > 0) {
            const correctedCount = finalIngredients.filter(f => f.source === 'fruit_correction').length;
            
            setGeminiResults(prev => ({
              ...prev,
              [image.id]: {
                text: finalIngredients.map(f => f.name).join(', '),
                extractedText: '과일 시각적 보정 적용', // 🍎 [추가]
                source: 'fruit_visual_correction', // 🍎 [추가]
                mode: '🍎 과일 보정', // 🍎 [추가]
                colorInfo: colorInfo ? colorInfo.primary_color : null, // 🍎 [추가]
                correctionCount: correctedCount, // 🍎 [추가]
                totalDetections: finalIngredients.length // 🍎 [추가]
              }
            }));
            
            console.log(`✅ 과일 보정 완료: ${correctedCount}개 보정, 총 ${finalIngredients.length}개 식재료`);
          }
        
        } catch (error) {
          console.error('❌ 과일 보정 처리 오류:', error); // 🍎 [수정] 에러 메시지 개선
        }
      }
      // 4단계: 결과 처리 및 상태 메시지 업데이트
      setProcessingStep(`4/4 - 결과 처리 완료`);
      if (finalIngredients.length > 0) {
        addToFridge(finalIngredients);
        setStatusMessage(`✅ 이미지 ${imageIndex + 1} 분석 완료: ${finalIngredients.length}개 식재료 추가`);
        setImages(prev => prev.map((img, idx) => 
          idx === imageIndex ? { ...img, processed: true } : img
        ));
      } else {
        setStatusMessage(`❌ 이미지 ${imageIndex + 1}: 분석 결과에서 식재료를 찾을 수 없습니다.`);
      }
    } catch (error) {
      console.error('향상된 추론 시스템 분석 오류:', error);
      setStatusMessage(`❌ 이미지 ${imageIndex + 1} 향상된 추론 중 오류가 발생했습니다.`);
    } finally {
      setIsProcessing(false);
      setProcessingImageIndex(-1);
      setProcessingStep('');
    }
  }; // <- analyzeImageAdvanced 함수 닫기

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
      setStatusMessage(`전체 ${images.length}개 이미지 향상된 추론 일괄 분석을 시작합니다...`);
      for (let i = 0; i < images.length; i++) {
        if (!images[i].processed) {
          await analyzeImageAdvanced(i);
          if (i < images.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      }
      setStatusMessage(`✅ 전체 향상된 추론 일괄 분석 완료!`);
    } catch (error) {
      console.error('향상된 추론 일괄 분석 오류:', error);
      setStatusMessage('❌ 향상된 추론 일괄 분석 중 오류가 발생했습니다.');
    } finally {
      setIsProcessing(false);
      setProcessingImageIndex(-1);
      setProcessingStep('');
    }
  };

  const testServerConnection = async () => {
    try {
      const result = await apiService.testConnection();
      setStatusMessage('서버 연결 성공');
    } catch (error) {
      setStatusMessage(`서버 연결 실패: ${error.message}`);
    }
  };

  // 웹 검색 래퍼 함수 (apiService를 통한 웹 검색)
  const performWebSearch = async (query) => {
    try {
      // apiService에 웹 검색 기능이 있다고 가정
      if (apiService.performWebSearch) {
        return await apiService.performWebSearch(query);
      }
      
      // 웹 검색이 불가능한 경우 로컬 패턴 매칭만 사용
      console.log(`웹 검색 기능 없음, 로컬 패턴 매칭만 사용: ${query}`);
      return [];
    } catch (error) {
      console.error('웹 검색 오류:', error);
      return [];
    }
  };

  // 향상된 OCR 추론 함수 (웹 검색 포함)
  const callGeminiAPIWithAdvancedInference = async (text, detectionResults = null) => {
    if (!text || text.trim() === "") {
      console.log("분석할 텍스트가 없습니다.");
      return null;
    }

    try {
      console.log(`🚀 향상된 OCR 추론 시작: "${text}"`);
      
      // 1단계: 향상된 OCR 추론 시스템 사용
      const enhancedResult = await enhancedOCRInference(text, performWebSearch);
      
      if (enhancedResult && enhancedResult.confidence >= 0.8) {
        console.log(`✅ 향상된 OCR 추론 성공:`, enhancedResult);
        const sourceMessage = enhancedResult.source === 'pattern_matching' ? '패턴 매칭' : 
                             enhancedResult.source === 'web_search' ? '웹 검색' : '향상된 추론';
        setStatusMessage(`🚀 ${sourceMessage} 성공: ${enhancedResult.ingredient} (${(enhancedResult.confidence * 100).toFixed(0)}%)`);
        
        // 결과에 소스 정보 추가
        return {
          ingredient: enhancedResult.ingredient,
          source: enhancedResult.source,
          confidence: enhancedResult.confidence
        };
      }

      // 2단계: 기존 추론 시스템 (백업)
      const advancedResult = performAdvancedInference(text);
      if (advancedResult.result && advancedResult.stage !== 'need_gemini') {
        console.log(`📋 기존 추론 시스템 결과: ${advancedResult.result}`);
        return {
          ingredient: advancedResult.result,
          source: 'legacy_inference',
          confidence: 0.8
        };
      }

      // 3단계: 브랜드 탐지
      const brandResult = detectBrandAndProductAdvanced(text);
      let brandContext = "";
      if (brandResult.brand && brandResult.product) {
        brandContext = `\n\n중요: 텍스트에서 '${brandResult.brand} ${brandResult.product}' 브랜드/제품이 직접 탐지되었습니다. 이를 최우선으로 고려하세요.`;
      } else if (brandResult.brand) {
        brandContext = `\n\n중요: 텍스트에서 '${brandResult.brand}' 브랜드가 탐지되었습니다.`;
      }

      // 4단계: Gemini API 호출
      const geminiResult = await geminiService.callGeminiAPI(text + brandContext, detectionResults);
      if (geminiResult) {
        const foodName = extractFoodNameFromGeminiResult(geminiResult, text, performAdvancedFallback);
        console.log(`🧠 Gemini API 결과: ${foodName}`);
        return {
          ingredient: foodName,
          source: 'gemini',
          confidence: 0.85
        };
      }

      // 5단계: 향상된 OCR 결과가 있다면 낮은 신뢰도라도 사용
      if (enhancedResult && enhancedResult.confidence >= 0.6) {
        console.log(`🔄 낮은 신뢰도 향상된 OCR 결과 사용:`, enhancedResult);
        setStatusMessage(`⚠️ 낮은 신뢰도 추론: ${enhancedResult.ingredient} (${(enhancedResult.confidence * 100).toFixed(0)}%)`);
        return {
          ingredient: enhancedResult.ingredient,
          source: enhancedResult.source,
          confidence: enhancedResult.confidence
        };
      }

      // 6단계: 최종 백업
      const fallbackResult = performAdvancedFallback(text);
      console.log(`🔙 최종 백업 결과: ${fallbackResult}`);
      return {
        ingredient: fallbackResult,
        source: 'fallback',
        confidence: 0.5
      };

    } catch (error) {
      console.error('향상된 추론 시스템 오류:', error);
      const fallbackResult = performAdvancedFallback(text);
      return {
        ingredient: fallbackResult,
        source: 'fallback',
        confidence: 0.5
      };
    }
  };

  // 렌더링
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="w-full max-w-sm md:max-w-2xl lg:max-w-4xl xl:max-w-6xl mx-auto p-3 md:p-6 lg:p-8">
        
        {/* 헤더 */}
        <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6 mb-4 md:mb-6">
          <div className="flex items-center gap-3 md:gap-4 mb-3">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl p-2 md:p-3 text-white">
              <Icons.Cooking />
            </div>
            <div className="flex-1">
              <h1 className="text-lg md:text-xl lg:text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                스마트 푸드 매니저 v13 (향상된 추론)
              </h1>
              <p className="text-xs md:text-sm text-gray-600">
                패턴 매칭 + 웹 검색 + 정밀 추론 시스템
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
                  <Icons.Upload />
                  <span>업로드</span>
                </button>

                <button
                  onClick={analyzeAllImages}
                  disabled={images.length === 0 || isProcessing}
                  className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:transform-none"
                >
                  {isProcessing && processingImageIndex === -1 ? <Icons.LoadingSpinner /> : <Icons.All />}
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
                    {isSaving ? <Icons.LoadingSpinner /> : <Icons.Save />}
                    <span className="text-xs md:text-sm">
                      {isSaving ? '저장 중...' : `저장 (${fridgeIngredients.length})`}
                    </span>
                  </button>

                  <button
                    onClick={loadFromMongoDB}
                    className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                  >
                    <Icons.Check />
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
                    <Icons.FatSecret />
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
                      {isDragOver ? '' : '여러 이미지 선택 가능 - 향상된 추론 + 패턴 매칭 + 웹 검색'}
                    </p>
                  </div>
                )}
              </div>

              {/* 진행 상태 */}
              {isProcessing && (
                <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-3 md:p-4">
                  <div className="flex items-center gap-2">
                    <Icons.LoadingSpinner />
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
                      <Icons.Fridge />
                    </div>
                    <h3 className="text-lg md:text-xl font-bold text-gray-800">냉장고 식재료</h3>
                  </div>
                  <div className="flex items-center gap-2 md:gap-3">
                    <button
                      onClick={() => setShowManualAdd(true)}
                      className="flex items-center gap-1 px-3 py-1.5 md:px-4 md:py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-xs md:text-sm rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg"
                    >
                      <Icons.Edit />
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
                            <Icons.Delete />
                          </button>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 md:gap-4">
                            <button
                              onClick={() => updateIngredientQuantity(ingredient.id, ingredient.quantity - 1)}
                              disabled={ingredient.quantity <= 1}
                              className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-r from-red-100 to-red-200 text-red-600 hover:from-red-200 hover:to-red-300 disabled:from-gray-100 disabled:to-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold text-sm"
                            >
                              <Icons.Minus />
                            </button>
                            
                            <div className="flex flex-col items-center bg-white rounded-lg p-2 md:p-3 shadow-sm border border-gray-200">
                              <span className="text-lg md:text-xl font-bold text-blue-600">{ingredient.quantity}</span>
                              <span className="text-xs text-gray-500 font-medium">개</span>
                            </div>
                            
                            <button
                              onClick={() => updateIngredientQuantity(ingredient.id, ingredient.quantity + 1)}
                              className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-r from-green-100 to-green-200 text-green-600 hover:from-green-200 hover:to-green-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold text-sm"
                            >
                              <Icons.Plus />
                            </button>
                          </div>
                          
                          <div className="text-xs text-gray-500 bg-white bg-opacity-80 px-2 py-1 rounded-lg font-semibold border border-gray-200">
                            {ingredient.source === 'manual' && '✏️'}
                            {ingredient.source === 'detection' && '🎯'}
                            {ingredient.source === '4stage_ocr' && '🚀'}
                            {ingredient.source === 'enhanced_ocr' && '⚡'}
                            {ingredient.source === 'pattern_matching' && '🔍'}
                            {ingredient.source === 'web_search' && '🌐'}
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
                      <Icons.Edit />
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
                {/* 탭 네비게이션 (FatSecret 및 대시보드 탭 제거) */}
                <div className="flex border-b border-gray-200 mb-4 md:mb-6 overflow-x-auto">
                  <button
                    onClick={() => setActiveTab('detection')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'detection'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icons.Eye />
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
                    <Icons.FileText />
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
                    <Icons.Brain />
                    AI분석
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
                          
                          {/* 원본 OCR 텍스트 */}
                          <div className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                            <div className="text-xs md:text-sm text-gray-600 mb-1 font-semibold">원본 텍스트:</div>
                            <p className="text-xs md:text-sm text-gray-800 whitespace-pre-wrap font-medium">
                              {ocrResults[images[selectedImageIndex].id].text || '추출된 텍스트가 없습니다.'}
                            </p>
                          </div>

                          {/* 요약된 키워드 */}
                          {ocrResults[images[selectedImageIndex].id].text && (
                            <div className="p-3 md:p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                              <div className="text-xs md:text-sm text-purple-700 mb-1 font-semibold">🔑 추출된 키워드:</div>
                              <p className="text-xs md:text-sm text-purple-800 font-medium">
                                {summarizeOCRText(ocrResults[images[selectedImageIndex].id].text)}
                              </p>
                              <div className="mt-2 text-xs text-purple-600">
                                전체 키워드: {extractKeywordsFromOCR(ocrResults[images[selectedImageIndex].id].text).join(', ')}
                              </div>
                            </div>
                          )}

                          {/* 신뢰도 정보 */}
                          {ocrResults[images[selectedImageIndex].id].confidence && (
                            <div className="text-xs md:text-sm text-gray-600 font-semibold">
                              OCR 신뢰도: {(ocrResults[images[selectedImageIndex].id].confidence * 100).toFixed(1)}%
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
                                🚀 향상된 추론
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
                          
                          {/* 메인 결과 */}
                          <div className="p-4 md:p-5 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border-2 border-purple-200">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="p-1 bg-purple-100 rounded">
                                <span className="text-sm">🚀</span>
                              </div>
                              <span className="text-xs md:text-sm font-bold text-purple-700">향상된 추론 결과</span>
                            </div>
                            <p className="text-sm md:text-base font-bold text-gray-800">
                              {geminiResults[images[selectedImageIndex].id].text}
                            </p>
                          </div>

                          {/* 추론 과정 상세 정보 */}
                          {geminiResults[images[selectedImageIndex].id].extractedText && (
                            <>
                              <div className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                                <div className="text-xs md:text-sm text-gray-600 mb-1 font-semibold">분석에 사용된 텍스트:</div>
                                <p className="text-xs md:text-sm text-gray-700 font-medium">
                                  {geminiResults[images[selectedImageIndex].id].extractedText}
                                </p>
                              </div>

                              {/* 키워드 분석 */}
                              <div className="p-3 md:p-4 bg-gradient-to-r from-green-50 to-teal-50 rounded-lg border border-green-200">
                                <div className="text-xs md:text-sm text-green-700 mb-1 font-semibold">🔍 추론 과정:</div>
                                <div className="text-xs md:text-sm text-green-800">
                                  <div>• 키워드 추출: {extractKeywordsFromOCR(geminiResults[images[selectedImageIndex].id].extractedText).slice(0, 5).join(', ')}</div>
                                  <div>• 요약: {summarizeOCRText(geminiResults[images[selectedImageIndex].id].extractedText)}</div>
                                  {geminiResults[images[selectedImageIndex].id].inferenceSource && (
                                    <div>• 추론 방법: {
                                      geminiResults[images[selectedImageIndex].id].inferenceSource === 'pattern_matching' ? '패턴 매칭' :
                                      geminiResults[images[selectedImageIndex].id].inferenceSource === 'web_search' ? '웹 검색' :
                                      geminiResults[images[selectedImageIndex].id].inferenceSource === 'gemini' ? 'Gemini AI' :
                                      geminiResults[images[selectedImageIndex].id].inferenceSource === 'legacy_inference' ? '기존 추론' :
                                      geminiResults[images[selectedImageIndex].id].inferenceSource === 'fallback' ? '백업 추론' :
                                      '향상된 추론'
                                    }</div>
                                  )}
                                  {geminiResults[images[selectedImageIndex].id].inferenceConfidence && (
                                    <div>• 추론 신뢰도: {(geminiResults[images[selectedImageIndex].id].inferenceConfidence * 100).toFixed(0)}%</div>
                                  )}
                                  <div>• 최종 추론: {geminiResults[images[selectedImageIndex].id].text}</div>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs md:text-sm text-gray-500 text-center py-6">이미지를 선택하고 향상된 추론을 진행해주세요.</p>
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
                  <Icons.Close />
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
                      <Icons.Minus />
                    </button>
                    
                    <div className="flex flex-col items-center min-w-[60px] md:min-w-[80px] bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 md:p-4 border-2 border-blue-200">
                      <span className="text-2xl md:text-3xl font-bold text-blue-600">{manualIngredientQuantity}</span>
                      <span className="text-xs text-gray-500 font-medium">개</span>
                    </div>
                    
                    <button
                      onClick={() => setManualIngredientQuantity(manualIngredientQuantity + 1)}
                      className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-gradient-to-r from-green-100 to-green-200 text-green-600 hover:from-green-200 hover:to-green-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold"
                    >
                      <Icons.Plus />
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
                  {isAddingManual ? <Icons.LoadingSpinner /> : <Icons.Plus />}
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