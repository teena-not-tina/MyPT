// src/pages/NotFoundPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from './Shared/Header'; // 헤더 컴포넌트 임포트 (선택 사항)


function NotFoundPage() {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/dashboard'); // 홈 페이지로 이동 (여기서는 대시보드로 설정)
  };

  const handleGoBack = () => {
    navigate(-1); // 이전 페이지로 돌아가기
  };

  return (
    <div className="page-container not-found-page-container">
      {/* 404 페이지에서는 헤더를 숨기는 경우도 많지만, 여기서는 뒤로가기 버튼을 위해 Header를 포함 */}
      <Header title="페이지를 찾을 수 없습니다" showBackButton={false} /> {/* 404페이지이므로 뒤로가기 버튼은 필요없음 */}
      
      <div className="not-found-content">
        <h1 className="not-found-code">404</h1>
        <p className="not-found-message">죄송합니다, 요청하신 페이지를 찾을 수 없습니다.</p>
        <p className="not-found-description">
          주소가 올바른지 확인하거나, 아래 버튼을 통해 다른 페이지로 이동해주세요.
        </p>
        
        <div className="not-found-actions">
          <button className="primary-button go-home-button" onClick={handleGoHome}>
            <i className="fas fa-home"></i> 홈으로 이동
          </button>
          <button className="secondary-button go-back-button" onClick={handleGoBack}>
            <i className="fas fa-arrow-left"></i> 이전 페이지로 돌아가기
          </button>
        </div>

        {/* 선택 사항: 유용한 링크나 검색창 추가 */}
        {/*
        <div className="helpful-links">
          <h3>다른 유용한 페이지</h3>
          <ul>
            <li><a href="/routine">나의 루틴</a></li>
            <li><a href="/diet/ingredients">식단 기록</a></li>
            <li><a href="/chatbot">AI 트레이너</a></li>
          </ul>
        </div>
        */}
      </div>
    </div>
  );
}

export default NotFoundPage;