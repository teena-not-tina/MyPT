import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './components/HomePage';
import MainPage from './components/MainPage';
import FoodDetectionApp from './components/FoodDetectionApp';
import Layout from './components/Layout';
import NotFound from './components/NotFound';
import Loading from './components/Loading';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 초기 로딩 시뮬레이션 (실제로는 API 호출 등)
    setTimeout(() => {
      setIsLoading(false);
      // 로컬 스토리지에서 사용자 정보 로드
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
    }, 1000);
  }, []);

  if (isLoading) {
    return <Loading />;
  }

  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            {/* 홈페이지 - 랜딩 페이지 */}
            <Route path="/" element={<HomePage />} />
            
            {/* 메인 페이지 - 대시보드 */}
            <Route path="/main" element={
              <MainPage user={user} setUser={setUser} />
            } />
            
            {/* 음식 감지 앱 - AI 음식 분석 */}
            <Route path="/food-detection" element={
              <FoodDetectionApp user={user} />
            } />
            
            {/* 기본 경로를 메인으로 리다이렉트 */}
            <Route path="/home" element={<Navigate to="/main" replace />} />
            
            {/* 404 페이지 - 잘못된 경로 처리 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;