// frontend/src/components/Diet/components/FridgeManager.js
import React, { useState } from 'react';

const FridgeManager = ({ userId, ingredients, onIngredientsChange }) => {
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualIngredientName, setManualIngredientName] = useState('');
  const [manualIngredientQuantity, setManualIngredientQuantity] = useState(1);

  const handleQuantityChange = (index, delta) => {
    const updated = [...ingredients];
    updated[index].quantity = Math.max(1, (updated[index].quantity || 1) + delta);
    onIngredientsChange(updated);
  };

  const handleRemove = (index) => {
    const updated = ingredients.filter((_, i) => i !== index);
    onIngredientsChange(updated);
  };

  const handleNameChange = (index, newName) => {
    const updated = [...ingredients];
    updated[index].name = newName;
    onIngredientsChange(updated);
  };

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

    const existingIngredient = ingredients.find(item => 
      item.name.trim().toLowerCase() === ingredientName.toLowerCase()
    );

    if (existingIngredient) {
      const updated = ingredients.map(ingredient => 
        ingredient.id === existingIngredient.id
          ? { ...ingredient, quantity: ingredient.quantity + manualIngredientQuantity }
          : ingredient
      );
      onIngredientsChange(updated);
    } else {
      const maxId = ingredients.length > 0 ? Math.max(...ingredients.map(item => item.id || 0)) : 0;
      const newIngredient = {
        id: maxId + 1,
        name: ingredientName,
        quantity: manualIngredientQuantity,
        confidence: 1.0,
        source: 'manual'
      };

      onIngredientsChange([...ingredients, newIngredient]);
    }

    setManualIngredientName('');
    setManualIngredientQuantity(1);
    setShowManualAdd(false);
  };

  // 아이콘 컴포넌트들
  const FridgeIcon = () => <span className="text-lg md:text-xl">🧊</span>;
  const EditIcon = () => <span className="text-sm">✏️</span>;
  const PlusIcon = () => <span className="text-sm">+</span>;
  const MinusIcon = () => <span className="text-sm">-</span>;
  const DeleteIcon = () => <span className="text-sm">🗑️</span>;
  const CloseIcon = () => <span className="text-sm">✕</span>;

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-blue-100">
      <div className="p-4 md:p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3 md:mb-4">
          <div className="flex items-center gap-2 md:gap-3">
            <div className="p-1 bg-gradient-to-r from-blue-100 to-indigo-100 rounded-lg">
              <FridgeIcon />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-gray-800">냉장고 식재료</h3>
          </div>
          <div className="flex items-center gap-2 md:gap-3">
            <button
              onClick={() => setShowManualAdd(true)}
              className="flex items-center gap-1 px-3 py-1.5 md:px-4 md:py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-xs md:text-sm rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg"
            >
              <EditIcon />
              <span>추가</span>
            </button>
            <button
              onClick={() => onIngredientsChange([])}
              className="text-xs md:text-sm text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1.5 rounded-lg transition-all duration-200 font-medium"
            >
              전체삭제
            </button>
          </div>
        </div>
        <div className="text-xs md:text-sm text-gray-500 font-medium bg-gray-50 px-2 py-1 rounded inline-block">
          총 {ingredients.length}개 종류
        </div>
      </div>
      
      <div className="p-4 md:p-6" style={{ minHeight: '200px', maxHeight: '400px', overflowY: 'auto' }}>
        {ingredients.length > 0 ? (
          <div className="space-y-3 md:space-y-4">
            {ingredients.map((ingredient, index) => (
              <div key={ingredient.id || index} className="bg-gradient-to-r from-blue-50 via-white to-indigo-50 border-2 border-gray-200 rounded-xl p-3 md:p-4 transition-all duration-300 hover:shadow-lg hover:scale-105 hover:border-blue-300">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-bold text-gray-800 text-sm md:text-base">{ingredient.name}</h4>
                  <button
                    onClick={() => handleRemove(index)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded-full p-1 transition-all duration-200"
                  >
                    <DeleteIcon />
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 md:gap-4">
                    <button
                      onClick={() => handleQuantityChange(index, -1)}
                      disabled={ingredient.quantity <= 1}
                      className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-r from-red-100 to-red-200 text-red-600 hover:from-red-200 hover:to-red-300 disabled:from-gray-100 disabled:to-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold text-sm"
                    >
                      <MinusIcon />
                    </button>
                    
                    <div className="flex flex-col items-center bg-white rounded-lg p-2 md:p-3 shadow-sm border border-gray-200">
                      <span className="text-lg md:text-xl font-bold text-blue-600">{ingredient.quantity}</span>
                      <span className="text-xs text-gray-500 font-medium">개</span>
                    </div>
                    
                    <button
                      onClick={() => handleQuantityChange(index, 1)}
                      className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-r from-green-100 to-green-200 text-green-600 hover:from-green-200 hover:to-green-300 flex items-center justify-center transition-all duration-200 transform hover:scale-110 font-bold text-sm"
                    >
                      <PlusIcon />
                    </button>
                  </div>
                  
                  <div className="text-xs text-gray-500 bg-white bg-opacity-80 px-2 py-1 rounded-lg font-semibold border border-gray-200">
                    {ingredient.source === 'manual' && '✏️'}
                    {ingredient.source === 'detection' && '🎯'}
                    {ingredient.source === '4stage_enhanced' && '🚀'}
                    {ingredient.source === 'gemini_enhanced' && '🧠'}
                    {ingredient.confidence && (
                      <span className="ml-1 text-green-600 font-bold">
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
            <div className="text-4xl md:text-6xl mb-4">🥬</div>
            <h4 className="text-lg md:text-xl font-bold mb-2">냉장고가 비어있습니다</h4>
            <p className="text-xs md:text-sm mb-4">냉장고 사진을 분석하거나</p>
            <button
              onClick={() => setShowManualAdd(true)}
              className="inline-flex items-center gap-2 px-4 py-2 md:px-6 md:py-3 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-xs md:text-sm rounded-lg hover:from-blue-600 hover:to-indigo-600 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg"
            >
              <EditIcon />
              <span>직접 추가하기</span>
            </button>
          </div>
        )}
      </div>
      
      {ingredients.length > 0 && (
        <div className="px-4 py-3 md:px-6 md:py-4 bg-gradient-to-r from-gray-50 to-blue-50 border-t border-gray-200 rounded-b-2xl">
          <div className="flex items-center justify-between text-xs md:text-sm">
            <span className="text-gray-600 font-medium">총 수량</span>
            <span className="font-bold text-gray-800">
              {ingredients.reduce((sum, item) => sum + (item.quantity || 1), 0)}개
            </span>
          </div>
        </div>
      )}

      {/* 직접 추가 모달 */}
      {showManualAdd && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm md:max-w-md border border-blue-200">
            <div className="p-6 md:p-8">
              <div className="flex items-center justify-between mb-4 md:mb-6">
                <h2 className="text-lg md:text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">식재료 직접 추가</h2>
                <button
                  onClick={() => setShowManualAdd(false)}
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
                    type="text"
                    value={manualIngredientName}
                    onChange={(e) => setManualIngredientName(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addManualIngredient()}
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
                  onClick={() => setShowManualAdd(false)}
                  className="flex-1 py-3 md:py-4 px-4 md:px-6 bg-gray-200 text-gray-800 rounded-lg font-bold hover:bg-gray-300 transition-all duration-200 transform hover:scale-105 text-sm md:text-base"
                >
                  취소
                </button>
                <button
                  onClick={addManualIngredient}
                  disabled={!manualIngredientName.trim()}
                  className="flex-1 py-3 md:py-4 px-4 md:px-6 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-lg font-bold hover:from-blue-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 disabled:transform-none flex items-center justify-center gap-2 shadow-lg text-sm md:text-base"
                >
                  <PlusIcon />
                  <span>추가하기</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FridgeManager;