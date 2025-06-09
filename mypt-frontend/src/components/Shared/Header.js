// src/components/Shared/Header.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css'; // Header 전용 CSS 임포트

function Header({ title, showBackButton, profileImage }) {
  const [currentProfileImage, setCurrentProfileImage] = useState(profileImage);
  const navigate = useNavigate();

  useEffect(() => {
    // 로컬 스토리지에서 이미지 확인
    const savedImage = localStorage.getItem('userProfileImage');
    if (savedImage) {
      setCurrentProfileImage(savedImage);
    }
  }, [profileImage]);

  const handleBackButtonClick = () => {
    navigate(-1); // 이전 페이지로 이동
  };

  return (
    <header className="app-header">
      {showBackButton && (
        <button className="back-button" onClick={handleBackButtonClick}>
          &larr; {/* 왼쪽 화살표 */}
        </button>
      )}
      <h1>{title}</h1>
      {/* ⭐️⭐️⭐️ 프로필 이미지 표시 영역 ⭐️⭐️⭐️ */}
      {currentProfileImage && (
        <div className="header-profile-area">
          <img
            src={`data:image/png;base64,${currentProfileImage}`}
            alt="Profile"
            className="header-profile-image"
          />
        </div>
      )}
    </header>
  );
}

export default Header;