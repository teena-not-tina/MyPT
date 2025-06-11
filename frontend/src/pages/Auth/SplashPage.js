// src/pages/Auth/SplashPage.js
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

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
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-800 flex items-center justify-center">
      <div className="text-center">
        <div className="mb-8">
          <div className="w-24 h-24 mx-auto mb-6 bg-white rounded-full flex items-center justify-center shadow-2xl">
            <span className="text-3xl font-bold text-blue-600">PT</span>
          </div>
          <h1 className="text-6xl font-bold text-white mb-4 tracking-wide">MyPT</h1>
          <p className="text-xl text-blue-100 font-light">당신의 개인 트레이너</p>
        </div>
        
        {/* 로딩 애니메이션 */}
        <div className="flex justify-center space-x-2 mt-8">
          <div className="w-3 h-3 bg-white rounded-full animate-bounce"></div>
          <div className="w-3 h-3 bg-white rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
          <div className="w-3 h-3 bg-white rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
        </div>
      </div>
    </div>
  );
}

export default SplashPage;