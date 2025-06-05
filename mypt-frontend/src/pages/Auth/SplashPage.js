// src/pages/Auth/SplashPage.js
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/global.css'; // global.css 임포트 중요

function SplashPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // 3초 후 로그인 페이지로 이동
    const timer = setTimeout(() => {
      navigate('/login');
    }, 3000); // 3000ms = 3초

    // 컴포넌트 언마운트 시 타이머 클리어
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="splash-container"> {/* 이 클래스가 중요 */}
      <h1 className="splash-title">MyPT</h1> {/* MyPT 텍스트 */}
    </div>
  );
}

export default SplashPage;