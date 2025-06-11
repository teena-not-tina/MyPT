// frontend/src/components/Diet/hooks/useFridge.js
import { useState } from 'react';
import { fridgeService } from '../CVservices/fridgeService';

export const useFridgeService = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const saveFridgeData = async (data) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fridgeService.saveFridgeData(data);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const loadFridgeData = async (userId) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fridgeService.loadFridgeData(userId);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const loadV3Data = async (userId) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fridgeService.loadV3Data(userId);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    saveFridgeData,
    loadFridgeData,
    loadV3Data,
    isLoading,
    error
  };
};