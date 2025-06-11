// frontend/src/components/Diet/hooks/useCV.js
import { useState } from 'react';
import { cvService } from '../CVservices/cvService';

export const useCVService = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const detectFood = async (file, confidence = 0.5) => {
    setIsProcessing(true);
    setError(null);
    try {
      const result = await cvService.detectFood(file, confidence);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsProcessing(false);
    }
  };

  const analyzeOCR = async (file) => {
    setIsProcessing(true);
    setError(null);
    try {
      const result = await cvService.analyzeOCR(file);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsProcessing(false);
    }
  };

  const analyzeWithGemini = async (text, detectionResults = null) => {
    setIsProcessing(true);
    setError(null);
    try {
      const result = await cvService.analyzeWithGemini(text, detectionResults);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    detectFood,
    analyzeOCR,
    analyzeWithGemini,
    isProcessing,
    error
  };
};