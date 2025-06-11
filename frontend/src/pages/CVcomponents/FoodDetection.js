// frontend/src/components/Diet/components/FoodDetection.js
import React, { useState, useRef, useEffect } from 'react';
import ImageUploader from './ImageUploader';
import FridgeManager from './FridgeManager';
import { useCVService } from '../CVhooks/useCV.js';
import { useFridgeService } from '../CVhooks/useFridge.js';
import { 
  detectBrandAndProductAdvanced,
  isBeverageByMl,
  extractIngredientsFromText,
  inferFromTextMaximally
} from '../../components/Diet/utils/foodUtils';

const FoodDetection = ({ onGoHome }) => {
  // 상태 관리 (FatSecret 관련 제거)
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

  // Refs
  const fileInputRef = useRef(null);
  const manualInputRef = useRef(null);

  // 서비스 훅들
  const { detectFood, analyzeOCR, analyzeWithGemini, translateDetectionResult } = useCVService();
  const { saveFridgeData, loadFridgeData } = useFridgeService();

  // ===== 4단계 추론 시스템 (간소화) =====
  const performAdvancedInference = (ocrText) => {
    if (!ocrText) {
      return {
        result: null,
        stage: 'no_input',
        confidence: 0.0,
        reasoning: '입력 텍스트가 없습니다.'
      };
    }

    console.log(`🚀 4단계 추론 시스템 시작: "${ocrText}"`);
    
    // 1단계: ml 음료 감지
    if (isBeverageByMl(ocrText)) {
      console.log(`🥤 1단계: ml 음료 감지 성공`);
      
      const brandResult = detectBrandAndProductAdvanced(ocrText);
      if (brandResult.brand && brandResult.product) {
        const result = `${brandResult.brand} ${brandResult.product}`;
        console.log(`✅ 1단계 완료 - 브랜드+제품: "${result}"`);
        return {
          result: result,
          stage: 'ml_brand_product',
          confidence: 0.95,
          reasoning: `ml 단위 음료에서 브랜드+제품 감지: ${result}`
        };
      }
      
      const maxInference = inferFromTextMaximally(ocrText);
      if (maxInference) {
        console.log(`✅ 1단계 완료 - 최대 추론: "${maxInference}"`);
        return {
          result: maxInference,
          stage: 'ml_max_inference',
          confidence: 0.85,
          reasoning: `ml 단위 음료에서 최대 추론: ${maxInference}`
        };
      }
      
      return {
        result: '음료',
        stage: 'ml_default',
        confidence: 0.8,
        reasoning: 'ml 단위와 음료 키워드가 감지되어 음료로 분류'
      };
    }

    // 2단계: 식재료명 직접 매칭
    const foundIngredients = extractIngredientsFromText(ocrText);
    if (foundIngredients.length > 0) {
      const bestIngredient = foundIngredients[0].name;
      console.log(`✅ 2단계 완료 - 식재료명 직접 매칭: "${bestIngredient}"`);
      return {
        result: bestIngredient,
        stage: 'ingredient_direct',
        confidence: 0.9,
        reasoning: `식재료명 직접 매칭: ${bestIngredient}`
      };
    }

    // 3단계: Gemini API 호출 필요
    console.log(`🤖 3단계: Gemini API 호출 필요`);
    return {
      result: null,
      stage: 'need_gemini',
      confidence: 0.0,
      reasoning: 'Gemini API 호출이 필요합니다.'
    };
  };

  // 이미지 처리 함수들
  const processImageFiles = (files) => {
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
      setStatusMessage('이미지 파일만 업로드 가능합니다.');
      return;
    }

    const processedImages = [];
    let processedCount = 0;

    imageFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        processedImages[index] = {
          id: Date.now() + index,
          file: file,
          dataUrl: e.target.result,
          name: file.name,
          size: file.size,
          processed: false
        };
        
        processedCount++;
        if (processedCount === imageFiles.length) {
          setImages(prev => [...prev, ...processedImages.filter(img => img)]);
          setSelectedImageIndex(images.length);
          setStatusMessage(`✅ ${imageFiles.length}개 이미지가 추가되었습니다.`);
        }
      };
      
      reader.readAsDataURL(file);
    });
  };

  const handleImagesSelected = (files) => {
    processImageFiles(files);
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
    
    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length > 0) {
      processImageFiles(imageFiles);
    } else {
      setStatusMessage('이미지 파일만 업로드 가능합니다.');
    }
  };

  // 고급 이미지 분석 함수 (FatSecret 제거)
  const analyzeImageAdvanced = async (imageIndex) => {
    if (imageIndex < 0 || imageIndex >= images.length) {
      setStatusMessage('유효하지 않은 이미지입니다.');
      return;
    }

    const image = images[imageIndex];
    if (!image || !image.file) {
      setStatusMessage('이미지 파일이 없습니다.');
      return;
    }

    if (isProcessing) {
      return;
    }

    setIsProcessing(true);
    setProcessingImageIndex(imageIndex);

    try {
      setProcessingStep(`이미지 ${imageIndex + 1} 4단계 추론 분석 중...`);
      setStatusMessage(`이미지 ${imageIndex + 1} 4단계 추론 분석 중...`);

      let finalIngredients = [];
      let detectionResult = null;
      let ocrResult = null;

      // 1단계: OCR API 호출
      setProcessingStep(`1/4 - 텍스트 추출 중...`);
      try {
        ocrResult = await analyzeOCR(image.file);
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
        detectionResult = await detectFood(image.file, confidence);
        setDetectionResults(prev => ({
          ...prev,
          [image.id]: detectionResult
        }));
        console.log(`🎯 Detection 결과: ${detectionResult.detections?.length || 0}개 탐지`);
      } catch (error) {
        console.error('Detection 실패:', error);
      }

      // 3단계: 4단계 추론 시스템 적용
      setProcessingStep(`3/4 - 4단계 추론 시스템 적용 중...`);
      
      const hasOcrText = ocrResult && ocrResult.text && ocrResult.text.trim().length > 0;
      const hasDetectionResults = detectionResult && detectionResult.detections && detectionResult.detections.length > 0;
      
      if (hasOcrText) {
        // OCR 텍스트가 있으면 4단계 추론 적용
        console.log(`🚀 OCR 우선 모드 - 4단계 추론 시스템 적용`);
        
        try {
          console.log(`📄 OCR 텍스트 분석: "${ocrResult.text}"`);
          
          // 4단계 추론 실행
          const advancedResult = performAdvancedInference(ocrResult.text);
          
          if (advancedResult.result && advancedResult.stage !== 'need_gemini') {
            // 1~2단계에서 해결된 경우
            const foodName = advancedResult.result;
            
            setGeminiResults(prev => ({
              ...prev,
              [image.id]: {
                text: foodName,
                extractedText: ocrResult.text,
                source: 'ocr_4stage',
                mode: 'OCR 4단계 추론',
                stage: advancedResult.stage
              }
            }));

            finalIngredients.push({
              name: foodName,
              quantity: 1,
              confidence: advancedResult.confidence,
              source: '4stage_enhanced'
            });
            
          } else {
            // 3단계: Gemini API 호출 필요
            try {
              const geminiResult = await analyzeWithGemini(ocrResult.text, detectionResult?.detections);
              
              if (geminiResult) {
                setGeminiResults(prev => ({
                  ...prev,
                  [image.id]: {
                    text: geminiResult,
                    extractedText: ocrResult.text,
                    source: 'gemini_4stage',
                    mode: 'Gemini + 4단계',
                    stage: 'gemini_api'
                  }
                }));

                finalIngredients.push({
                  name: geminiResult,
                  quantity: 1,
                  confidence: 0.85,
                  source: 'gemini_enhanced'
                });
              }
            } catch (error) {
              console.error('Gemini 분석 실패:', error);
            }
          }
        } catch (error) {
          console.error('❌ OCR 기반 종합 분석 오류:', error);
        }
        
      } else if (hasDetectionResults) {
        // OCR 텍스트가 없을 때는 Detection만 사용
        console.log(`🎯 Detection 전용 모드 - OCR 텍스트 없음`);
        
        try {
          for (let detection of detectionResult.detections.filter(d => d.confidence >= 0.5)) {
            const translatedName = await translateDetectionResult(detection.class);
            if (translatedName) {
              finalIngredients.push({
                name: translatedName,
                quantity: 1,
                confidence: detection.confidence,
                source: 'detection'
              });
              console.log(`🥬 Detection 전용 모드 - 냉장고 추가: "${translatedName}"`);
            }
          }
        } catch (error) {
          console.error('❌ Detection 처리 오류:', error);
        }
        
      } else {
        console.log(`❌ OCR, Detection 모두 결과 없음`);
      }

      // 4단계: 결과 처리
      setProcessingStep(`4/4 - 결과 처리 완료`);
      
      if (finalIngredients.length > 0) {
        addToFridge(finalIngredients);
        
        const analysisMode = hasOcrText ? 'OCR 4단계 추론' : 'Detection 전용';
        
        setStatusMessage(`✅ 이미지 ${imageIndex + 1} ${analysisMode} 분석 완료: ${finalIngredients.length}개 식재료 추가`);
        console.log(`✅ ${analysisMode} 분석 완료: ${finalIngredients.map(item => item.name).join(', ')}`);
        
        setImages(prev => prev.map((img, idx) => 
          idx === imageIndex ? { ...img, processed: true } : img
        ));
      } else {
        const analysisMode = hasOcrText ? 'OCR 4단계 추론' : hasDetectionResults ? 'Detection' : '분석';
        setStatusMessage(`❌ 이미지 ${imageIndex + 1}: ${analysisMode} 결과에서 식재료를 찾을 수 없습니다.`);
      }

    } catch (error) {
      console.error('4단계 추론 시스템 분석 오류:', error);
      setStatusMessage(`❌ 이미지 ${imageIndex + 1} 종합 분석 중 오류가 발생했습니다.`);
    } finally {
      setIsProcessing(false);
      setProcessingImageIndex(-1);
      setProcessingStep('');
    }
  };

  // 전체 이미지 분석
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

      setStatusMessage(`전체 ${images.length}개 이미지 4단계 추론 일괄 분석을 시작합니다...`);
      
      for (let i = 0; i < images.length; i++) {
        if (!images[i].processed) {
          await analyzeImageAdvanced(i);
          if (i < images.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      }
      
      setStatusMessage(`✅ 전체 4단계 추론 일괄 분석 완료!`);

    } catch (error) {
      console.error('종합 일괄 분석 오류:', error);
      setStatusMessage('❌ 종합 일괄 분석 중 오류가 발생했습니다.');
    } finally {
      setIsProcessing(false);
      setProcessingImageIndex(-1);
      setProcessingStep('');
    }
  };

  // 냉장고에 식재료 추가
  const addToFridge = (newIngredients) => {
    setFridgeIngredients(prevIngredients => {
      const updatedIngredients = [...prevIngredients];
      let maxId = updatedIngredients.length > 0 ? Math.max(...updatedIngredients.map(item => item.id)) : 0;

      newIngredients.forEach(newItem => {
        const existingItemIndex = updatedIngredients.findIndex(item => 
          item.name.trim().toLowerCase() === newItem.name.trim().toLowerCase()
        );

        if (existingItemIndex !== -1) {
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
        } else {
          const newIngredient = {
            id: ++maxId,
            name: newItem.name.trim(),
            quantity: newItem.quantity,
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

  // 저장/불러오기 함수들
  const handleSave = async () => {
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

      await saveFridgeData(saveData);
      setStatusMessage(`✅ 냉장고 데이터가 성공적으로 저장되었습니다! (총 ${fridgeIngredients.length}종류)`);
      setShowSaveButton(false);
      
      setTimeout(() => {
        setStatusMessage('저장 완료');
      }, 3000);
    } catch (error) {
      console.error('❌ 저장 실패:', error);
      setStatusMessage(`❌ 저장 실패: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoad = async () => {
    try {
      const result = await loadFridgeData(userId);
      
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
      console.error('❌ 불러오기 실패:', error);
      setStatusMessage('저장된 데이터가 없습니다.');
    }
  };

  // 직접 추가 관련 함수들
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

    const existingIngredient = fridgeIngredients.find(item => 
      item.name.trim().toLowerCase() === ingredientName.toLowerCase()
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

  // 아이콘 컴포넌트들
  const CookingIcon = () => <span className="text-2xl md:text-3xl">👨‍🍳</span>;
  const UploadIcon = () => <span className="text-sm">📁</span>;
  const EyeIcon = () => <span className="text-sm">👁️</span>;
  const BrainIcon = () => <span className="text-sm">🧠</span>;
  const FileTextIcon = () => <span className="text-sm">📄</span>;
  const AllIcon = () => <span className="text-sm">🔄</span>;
  const SaveIcon = () => <span className="text-sm">💾</span>;
  const CheckIcon = () => <span className="text-sm">✅</span>;
  const EditIcon = () => <span className="text-sm">✏️</span>;
  const PlusIcon = () => <span className="text-sm">+</span>;
  const CloseIcon = () => <span className="text-sm">✕</span>;
  const LoadingSpinner = () => (
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
  );

  // UI 렌더링
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="w-full max-w-sm md:max-w-2xl lg:max-w-4xl xl:max-w-6xl mx-auto p-3 md:p-6 lg:p-8">
        
        {/* 헤더 수정 */}
        <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6 mb-4 md:mb-6">
          <div className="flex items-center gap-3 md:gap-4 mb-4 md:mb-6">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl p-2 md:p-3 text-white">
              <CookingIcon />
            </div>
            <div className="flex-1">
              <h1 className="text-lg md:text-xl lg:text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                스마트 푸드 매니저 v12 (모듈화)
              </h1>
              <p className="text-xs md:text-sm text-gray-600">
                4단계 추론 + 객체탐지 + OCR 분석
              </p>
            </div>
            <button
              onClick={onGoHome}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
            >
              홈으로
            </button>
          </div>
        </div>
         {/* 상단 액션 버튼들 */}
        <div className="bg-white rounded-2xl shadow-lg border border-blue-100 p-4 md:p-6 mb-4 md:mb-6">
          <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleImagesSelected(Array.from(e.target.files))}
              ref={fileInputRef}
              className="hidden"
              multiple
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
            >
              <UploadIcon />
              <span>이미지 업로드</span>
            </button>

            <button
              onClick={analyzeAllImages}
              disabled={images.length === 0 || isProcessing}
              className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isProcessing && processingImageIndex === -1 ? <LoadingSpinner /> : <span>🔍</span>}
              <span>식재료 분석</span>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4">
            <button
              onClick={handleSave}
              disabled={isSaving || fridgeIngredients.length === 0}
              className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isSaving ? <LoadingSpinner /> : <SaveIcon />}
              <span className="text-xs md:text-sm">냉장고 저장 ({fridgeIngredients.length}종류)</span>
            </button>

            <button
              onClick={handleLoad}
              className="flex items-center justify-center gap-2 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-semibold text-sm md:text-base transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
            >
              <CheckIcon />
              <span className="text-xs md:text-sm">데이터 불러오기</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">신뢰도</span>
            <span className="text-sm text-blue-600 font-bold">{confidence}</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1"
            step="0.1"
            value={confidence}
            onChange={(e) => setConfidence(parseFloat(e.target.value))}
            className="w-full mt-2"
          />
          <div className="text-xs text-gray-500 mt-1">
            분석 신 냉장고 초기화 (등급 이미지 재분석 시 충돌 방지)
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
          {/* 왼쪽 컬럼 */}
          <div className="space-y-4 md:space-y-6">
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
                      {isDragOver ? '' : '여러 이미지 선택 가능 - 4단계 추론 시스템'}
                    </p>
                  </div>
                )}
              </div>

              {/* 진행 상태 */}
              {isProcessing && (
                <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-3 md:p-4">
                  <div className="flex items-center gap-2">
                    <LoadingSpinner />
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
            {/* 냉장고 식재료 관리 */}
            <FridgeManager
              userId={userId}
              ingredients={fridgeIngredients}
              onIngredientsChange={setFridgeIngredients}
            />

            {/* 분석 결과 표시 */}
            <div className="bg-white rounded-2xl shadow-lg border border-blue-100 overflow-hidden">
              <div className="p-4 md:p-6">
                {/* 탭 네비게이션 */}
                <div className="flex border-b border-gray-200 mb-4 md:mb-6 overflow-x-auto">
                  <button
                    onClick={() => setActiveTab('detection')}
                    className={`flex items-center gap-1 px-3 py-2 md:px-4 md:py-3 text-xs md:text-sm font-semibold transition-all duration-200 rounded-t-lg whitespace-nowrap ${
                      activeTab === 'detection'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <EyeIcon />
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
                    <FileTextIcon />
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
                    <BrainIcon />
                    AI분석
                  </button>
                </div>

                {/* 탭 내용 */}
                <div className="min-h-[150px] md:min-h-[200px]">
                  {activeTab === 'detection' && (
                    <div>
                      <h3 className="text-sm md:text-base font-bold text-gray-800 mb-3 md:mb-4">객체 탐지 결과</h3>
                      {images.length > 0 && selectedImageIndex >= 0 && detectionResults[images[selectedImageIndex]?.id] ? (
                        <div className="space-y-2 md:space-y-3">
                          <div className="text-xs md:text-sm text-gray-600 mb-2 bg-blue-50 px-2 py-1 rounded font-medium">
                            이미지 {selectedImageIndex + 1}: 총 {detectionResults[images[selectedImageIndex].id].detections?.length || 0}개 탐지
                          </div>
                          {detectionResults[images[selectedImageIndex].id].detections?.filter(d => d.confidence >= 0.5).map((detection, index) => (
                            <div key={index} className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                              <div className="flex justify-between items-center">
                                <span className="text-xs md:text-sm font-bold text-blue-600">
                                  {detection.class}
                                </span>
                                <span className="text-xs md:text-sm font-bold px-2 py-0.5 rounded-full bg-gradient-to-r from-green-100 to-emerald-100 text-green-700">
                                  {(detection.confidence * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
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
                          <div className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                            <p className="text-xs md:text-sm text-gray-800 whitespace-pre-wrap font-medium">
                              {ocrResults[images[selectedImageIndex].id].text || '추출된 텍스트가 없습니다.'}
                            </p>
                          </div>
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
                            {geminiResults[images[selectedImageIndex].id].mode && (
                              <span className="ml-1 text-xs text-gray-500">
                                ({geminiResults[images[selectedImageIndex].id].mode})
                              </span>
                            )}
                          </div>
                          <div className="p-4 md:p-5 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border-2 border-purple-200">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="p-1 bg-purple-100 rounded">
                                <span className="text-sm">🚀</span>
                              </div>
                              <span className="text-xs md:text-sm font-bold text-purple-700">4단계 추론 결과</span>
                              {geminiResults[images[selectedImageIndex].id].stage && (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                  {geminiResults[images[selectedImageIndex].id].stage}
                                </span>
                              )}
                            </div>
                            <p className="text-sm md:text-base font-bold text-gray-800">
                              {geminiResults[images[selectedImageIndex].id].text}
                            </p>
                          </div>
                          {geminiResults[images[selectedImageIndex].id].extractedText && (
                            <div className="p-3 md:p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
                              <div className="text-xs md:text-sm text-gray-600 mb-1 font-semibold">분석에 사용된 텍스트:</div>
                              <p className="text-xs md:text-sm text-gray-700 font-medium">
                                {geminiResults[images[selectedImageIndex].id].extractedText}
                              </p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs md:text-sm text-gray-500 text-center py-6">이미지를 선택하고 4단계 추론 분석을 진행해주세요.</p>
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
                  <CloseIcon />
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
                      -
                    </button>
                    
                    <div className="flex flex-col items-center min-w-[60px] md:min-w-[80px] bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 md:p-4 border-2 border-blue-200">
                      <span className="text-2xl md:text-3xl font-bold text-blue-600">{manualIngredientQuantity}</span>
                      <span className="text-xs md:text-sm text-gray-500 font-medium">개</span>
                    </div>
                    
                    <button
                      onClick={() => setManualIngredientQuantity(manualIngredientQuantity + 1)}
                      className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-gradient-to-r from-green-100 to-green-200 text-green-600 hover:from-green-200 hover:to-green-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold"
                    >
                      +
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
                  {isAddingManual ? <LoadingSpinner /> : <PlusIcon />}
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

export default FoodDetection;