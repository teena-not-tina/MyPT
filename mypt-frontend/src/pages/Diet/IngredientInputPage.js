// src/pages/Diet/IngredientInputPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header'; // 헤더 임포트
import '../../styles/global.css'; // 공통 스타일 임포트
import './IngredientInputPage.css'; // 식단 페이지 전용 스타일

function IngredientInputPage() {
  const [ingredientText, setIngredientText] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('입력된 재료:', ingredientText);
    alert(`입력된 재료: ${ingredientText} (나중에 백엔드 처리)`);
    // TODO: 입력된 재료를 백엔드로 전송하거나, 메뉴 추천 페이지로 이동
    navigate('/diet/menu'); // 예시: 메뉴 추천 페이지로 이동
  };

  return (
    <div className="page-container"> {/* 전체 페이지 컨테이너 */}
      <Header title="식단 기록" showBackButton={true} /> {/* 뒤로가기 버튼 추가 */}
      <div className="page-content-wrapper diet-input-page-content">
        <h2 className="diet-input-title">오늘 먹은 것을 기록해주세요</h2>
        <form onSubmit={handleSubmit} className="diet-input-form"> {/* auth-form 대신 전용 클래스 사용 */}
          <div className="form-group">
            <label htmlFor="ingredientInput" className="input-label">재료 또는 음식명 입력:</label>
            <textarea
              id="ingredientInput"
              className="form-input-textarea" // 텍스트 영역 전용 스타일
              value={ingredientText}
              onChange={(e) => setIngredientText(e.target.value)}
              rows="7" // 높이 조정
              placeholder="예: 닭가슴살 100g, 밥 한 공기, 김치, 사과 1개 &#10;여러 줄로 입력 가능합니다."
              required
            ></textarea>
          </div>
          <button type="submit" className="primary-button diet-submit-button">
            기록 완료
          </button>
        </form>
        <p className="diet-feature-note">
          <i className="fas fa-microphone"></i> 음성 인식, <i className="fas fa-camera"></i> 사진 인식 기능은 나중에 추가됩니다.
        </p>
      </div>
    </div>
  );
}

export default IngredientInputPage;