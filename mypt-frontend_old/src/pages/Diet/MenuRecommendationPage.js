// src/pages/Diet/MenuRecommendationPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header'; // 헤더 임포트
import '../../styles/global.css'; // 공통 스타일 임포트
import './MenuRecommendationPage.css'; // 식단 추천 페이지 전용 스타일 (새로 생성)

function MenuRecommendationPage() {
  const navigate = useNavigate();

  // 실제로는 백엔드 API로부터 추천 메뉴를 받아올 더미 데이터
  const recommendedMenus = [
    {
      id: 1,
      name: '닭가슴살 샐러드',
      description: '신선한 채소와 함께 단백질을 보충할 수 있는 가벼운 식단입니다.',
      calories: 350,
      macros: { protein: 30, carbs: 25, fat: 15 }, // 단백질, 탄수화물, 지방 (g)
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
    // 선택된 메뉴를 기록하거나 다른 페이지로 이동 (예: 대시보드)
    navigate('/dashboard'); 
  };

  return (
    <div className="page-container">
      <Header title="식단 추천" showBackButton={true} />
      <div className="page-content-wrapper menu-recommendation-page-content">
        <h2 className="recommendation-title">추천 식단</h2>
        {recommendedMenus.length > 0 ? (
          <div className="menu-list">
            {recommendedMenus.map((menu) => (
              <div key={menu.id} className="menu-card">
                <h3>{menu.name}</h3>
                <p className="menu-description">{menu.description}</p>
                <div className="menu-details">
                  <span><i className="fas fa-fire"></i> {menu.calories} kcal</span>
                  <span>단백질: {menu.macros.protein}g</span>
                  <span>탄수화물: {menu.macros.carbs}g</span>
                  <span>지방: {menu.macros.fat}g</span>
                </div>
                <ul className="menu-ingredients">
                  {menu.ingredients.map((ing, idx) => (
                    <li key={idx}><i className="fas fa-check-circle"></i> {ing}</li>
                  ))}
                </ul>
                <button 
                  className="primary-button select-menu-button" 
                  onClick={() => handleSelectMenu(menu.name)}
                >
                  이 메뉴 선택
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-recommendation">입력된 재료로 추천할 수 있는 식단이 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default MenuRecommendationPage;