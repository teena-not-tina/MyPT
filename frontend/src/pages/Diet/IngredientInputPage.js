// src/pages/Diet/IngredientInputPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../Shared/Header';
import { generateFoodImage } from '../../service/foodmake';

function IngredientInputPage() {
  const [ingredientText, setIngredientText] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const imageBase64 = await generateFoodImage(ingredientText);
      alert('이미지 생성 및 저장 완료!');
      // 예시: 이미지 결과를 다음 페이지로 전달하려면 아래처럼 사용
      // navigate('/diet/menu', { state: { imageBase64 } });
      navigate('/diet/menu');
    } catch (error) {
      alert('이미지 생성 실패: ' + (error.message || error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="식단 기록" showBackButton={true} />
      <div className="px-4 py-6 max-w-md mx-auto">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
            오늘 먹은 것을 기록해주세요
          </h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label
                htmlFor="ingredientInput"
                className="block text-sm font-medium text-gray-700"
              >
                재료 또는 음식명 입력:
              </label>
              <textarea
                id="ingredientInput"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors duration-200 text-gray-700 placeholder-gray-400"
                value={ingredientText}
                onChange={(e) => setIngredientText(e.target.value)}
                rows="7"
                placeholder="예: 닭가슴살 100g, 밥 한 공기, 김치, 사과 1개&#10;여러 줄로 입력 가능합니다."
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              disabled={loading}
            >
              {loading ? '이미지 생성 중...' : '기록 완료'}
            </button>
          </form>
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-sm text-blue-700 text-center space-x-4">
              <span className="inline-flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
                음성 인식
              </span>
              <span className="inline-flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                </svg>
                사진 인식
              </span>
              <span className="block mt-2 text-xs">
                기능은 나중에 추가됩니다.
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default IngredientInputPage;