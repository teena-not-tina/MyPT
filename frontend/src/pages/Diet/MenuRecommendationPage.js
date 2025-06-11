// src/pages/Diet/MenuRecommendationPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../Shared/Header';

function MenuRecommendationPage() {
  const navigate = useNavigate();

  const recommendedMenus = [
    {
      id: 1,
      name: '닭가슴살 샐러드',
      description: '신선한 채소와 함께 단백질을 보충할 수 있는 가벼운 식단입니다.',
      calories: 350,
      macros: { protein: 30, carbs: 25, fat: 15 },
      ingredients: ['닭가슴살 150g', '양상추 100g', '방울토마토 5개', '오이 1/2개', '발사믹 드레싱'],
    },
    {
      id: 2,
      name: '고구마 닭가슴살 구이',
      description: '간단하면서도 영양 균형이 잘 잡힌 식단입니다.',
      calories: 450,
      macros: { protein: 35, carbs: 40, fat: 18 },
      ingredients: ['닭가슴살 200g', '고구마 1개 (150g)', '브로콜리 50g', '올리브유'],
    },
    {
      id: 3,
      name: '두부 야채 볶음밥',
      description: '식물성 단백질과 다양한 채소를 섭취할 수 있는 볶음밥입니다.',
      calories: 400,
      macros: { protein: 25, carbs: 50, fat: 12 },
      ingredients: ['두부 1/2모', '현미밥 1공기', '당근, 양파, 피망', '간장, 참기름'],
    },
  ];

  const handleSelectMenu = (menuName) => {
    alert(`"${menuName}" 메뉴를 선택했습니다! (추후 기록 기능 구현)`);
    navigate('/dashboard'); 
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="식단 추천" showBackButton={true} />
      
      <div className="px-4 py-6 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          추천 식단
        </h2>
        
        {recommendedMenus.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {recommendedMenus.map((menu) => (
              <div key={menu.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow duration-200">
                <div className="p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-2">
                    {menu.name}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4 leading-relaxed">
                    {menu.description}
                  </p>
                  
                  {/* 영양 정보 */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-orange-50 rounded-lg p-3 text-center">
                      <div className="flex items-center justify-center mb-1">
                        <svg className="w-4 h-4 text-orange-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0112.12 15.12z" clipRule="evenodd" />
                        </svg>
                        <span className="text-xs font-medium text-orange-700">칼로리</span>
                      </div>
                      <span className="text-lg font-bold text-orange-600">{menu.calories}</span>
                      <span className="text-xs text-orange-600"> kcal</span>
                    </div>
                    
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">단백질</span>
                        <span className="font-medium text-blue-600">{menu.macros.protein}g</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">탄수화물</span>
                        <span className="font-medium text-green-600">{menu.macros.carbs}g</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">지방</span>
                        <span className="font-medium text-purple-600">{menu.macros.fat}g</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* 재료 목록 */}
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">재료</h4>
                    <ul className="space-y-1">
                      {menu.ingredients.map((ing, idx) => (
                        <li key={idx} className="flex items-center text-sm text-gray-600">
                          <svg className="w-3 h-3 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          {ing}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <button 
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    onClick={() => handleSelectMenu(menu.name)}
                  >
                    이 메뉴 선택
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 max-w-md mx-auto">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.291-1.1-5.291-2.709M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <p className="text-gray-500">입력된 재료로 추천할 수 있는 식단이 없습니다.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MenuRecommendationPage;