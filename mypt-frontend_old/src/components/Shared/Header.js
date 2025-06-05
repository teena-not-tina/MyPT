// src/components/Shared/Header.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/global.css'; // 공통 스타일 임포트

// Header 컴포넌트
// props:
//   title: 헤더에 표시할 제목 (필수)
//   showBackButton: 뒤로 가기 버튼을 표시할지 여부 (선택, 기본값 false)
//   onBackClick: 뒤로 가기 버튼 클릭 시 실행할 함수 (선택, showBackButton이 true일 때만 유효)
function Header({ title, showBackButton = false, onBackClick }) {
  const navigate = useNavigate();

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick(); // 사용자 정의 함수가 있다면 실행
    } else {
      navigate(-1); // 기본적으로 이전 페이지로 이동
    }
  };

  return (
    <header className="app-header">
      {showBackButton && (
        <button onClick={handleBackClick} className="back-button">
          <i className="fas fa-arrow-left"></i> {/* 폰트어썸 아이콘 */}
        </button>
      )}
      <h1 className="header-title">{title}</h1>
      {/* 필요하다면 여기에 오른쪽 아이콘을 추가할 수 있습니다. */}
      {/* <div className="header-right-icon"></div> */}
    </header>
  );
}

export default Header;