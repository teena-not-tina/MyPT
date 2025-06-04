// components/CookingMode.js
import React, { useState, useEffect } from 'react';
import apiService from '../services/apiService';
import { useNavigate } from 'react-router-dom';

const CookingMode = () => {
  const navigate = useNavigate();
  const [fridgeIngredients, setFridgeIngredients] = useState([]);
  const [userId] = useState('user_' + Date.now());
  const [isLoading, setIsLoading] = useState(true);
  const [recipes, setRecipes] = useState([]);

  useEffect(() => {
    loadFridgeData();
  }, []);

  const loadFridgeData = async () => {
    try {
      setIsLoading(true);
      const result = await apiService.loadFridgeData(userId);
      if (result.ingredients && result.ingredients.length > 0) {
        setFridgeIngredients(result.ingredients);
      }
    } catch (error) {
      console.error('Failed to load fridge data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateRecipes = () => {
    // 간단한 레시피 생성 로직 (실제로는 AI API 호출)
    const sampleRecipes = [
      {
        id: 1,
        name: '김치찌개',
        ingredients: ['김치', '돼지고기', '두부'],
        difficulty: '쉬움',
        time: '30분'
      },
      {
        id: 2,
        name: '된장찌개',
        ingredients: ['된장', '두부', '호박', '양파'],
        difficulty: '쉬움',
        time: '25분'
      },
      {
        id: 3,
        name: '볶음밥',
        ingredients: ['밥', '계란', '파', '당근'],
        difficulty: '쉬움',
        time: '15분'
      }
    ];
    setRecipes(sampleRecipes);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-red-50">
      <div className="w-full max-w-6xl mx-auto p-4 md:p-8">
        {/* 헤더 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <span className="text-2xl">←</span>
              </button>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                  요리 모드
                </h1>
                <p className="text-sm text-gray-600">
                  보유한 식재료로 만들 수 있는 요리
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate('/food-detection')}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              식재료 관리
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 보유 식재료 목록 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-lg font-bold text-gray-800 mb-4">
                보유 식재료 ({fridgeIngredients.length}개)
              </h2>
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto"></div>
                  <p className="text-sm text-gray-500 mt-2">불러오는 중...</p>
                </div>
              ) : fridgeIngredients.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {fridgeIngredients.map((ingredient) => (
                    <div key={ingredient.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">{ingredient.name}</span>
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                        {ingredient.quantity}개
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">🥬</div>
                  <p className="text-gray-500 text-sm mb-4">
                    식재료가 없습니다
                  </p>
                  <button
                    onClick={() => navigate('/food-detection')}
                    className="text-blue-500 hover:text-blue-700 text-sm font-medium"
                  >
                    식재료 추가하기 →
                  </button>
                </div>
              )}

              {fridgeIngredients.length > 0 && (
                <button
                  onClick={generateRecipes}
                  className="w-full mt-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-bold hover:from-orange-600 hover:to-red-600 transition-all duration-300"
                >
                  레시피 추천받기
                </button>
              )}
            </div>
          </div>

          {/* 추천 레시피 목록 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-lg font-bold text-gray-800 mb-4">
                추천 레시피
              </h2>
              {recipes.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recipes.map((recipe) => (
                    <div key={recipe.id} className="border border-gray-200 rounded-xl p-4 hover:shadow-lg transition-shadow">
                      <h3 className="font-bold text-lg mb-2">{recipe.name}</h3>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <span>⏱️</span>
                          <span>{recipe.time}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <span>📊</span>
                          <span>난이도: {recipe.difficulty}</span>
                        </div>
                        <div className="mt-3">
                          <p className="text-xs text-gray-500 mb-1">필요한 재료:</p>
                          <div className="flex flex-wrap gap-1">
                            {recipe.ingredients.map((ing, idx) => (
                              <span key={idx} className="text-xs bg-gray-100 px-2 py-1 rounded">
                                {ing}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      <button className="w-full mt-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors text-sm font-medium">
                        레시피 보기
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4">👨‍🍳</div>
                  <p className="text-gray-500">
                    레시피 추천을 받으려면<br />
                    "레시피 추천받기" 버튼을 클릭하세요
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookingMode;