// src/App.js
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import useAuthStore from './stores/authStore';

// --- 페이지 컴포넌트 임포트 ---
import SplashPage from './pages/Auth/SplashPage'; // ⭐️⭐️⭐️ SplashPage 다시 임포트 ⭐️⭐️⭐️
import LoginPage from './pages/Auth/LoginPage';
import SignupPage from './pages/Auth/SignupPage';
import InbodyFormPage from './pages/Onboarding/InbodyFormPage';
import DashboardPage from './pages/Home/DashboardPage';
import RoutineOverviewPage from './pages/Routine/RoutineOverviewPage';
import RoutineDetailPage from './pages/Routine/RoutineDetailPage';
import ExerciseCameraPage from './pages/Routine/ExerciseCameraPage';
import IngredientInputPage from './pages/Diet/IngredientInputPage';
import MenuRecommendationPage from './pages/Diet/MenuRecommendationPage';
import ChatbotPage from './pages/AI/ChatbotPage';
import AvatarProgressPage from './pages/AI/AvatarProgressPage';
import NotFoundPage from './pages/NotFoundPage'; // 임포트 확인

// --- 공통 컴포넌트 임포트 ---
// import Header from './components/Shared/Header';
import Navbar from './components/Shared/Navbar';
import './styles/global.css';

// 인증이 필요한 라우트를 감싸는 PrivateRoute 컴포넌트
const PrivateRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// 특정 라우트에서만 Navbar를 표시하기 위한 헬퍼 컴포넌트
const ConditionalNavbar = () => {
  const location = useLocation();
  const noNavbarPaths = [
    '/', // ⭐️⭐️⭐️ 스플래시 페이지에서는 Navbar 숨김 ⭐️⭐️⭐️
    '/login',
    '/signup',
    '/onboarding/inbody',
    '/routine/:id/analyze',
    '/404' // 404 페이지에서도 Navbar 숨김
  ];

  const shouldShowNavbar = !noNavbarPaths.some(path => location.pathname.startsWith(path.split(':')[0]));

  return shouldShowNavbar ? <Navbar /> : null;
};


function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth); 

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <Router>
      <div className="app-container">
        {/* Header는 ChatbotPage에서 사용되므로 여기서는 주석 처리 유지 */}
        {/* <Header /> */}

        <Routes>
          {/* ⭐️⭐️⭐️ 앱 시작 라우트를 SplashPage로 설정 ⭐️⭐️⭐️ */}
          <Route path="/" element={<SplashPage />} /> 

          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          
          {/* PrivateRoute가 필요한 라우트들 */}
          {/* DashboardPage는 이제 /dashboard 경로로 접근해야 합니다. */}
          <Route path="/onboarding/inbody" element={<PrivateRoute><InbodyFormPage /></PrivateRoute>} />
          <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} /> 
          <Route path="/routine" element={<PrivateRoute><RoutineOverviewPage /></PrivateRoute>} />
          <Route path="/routine/:id" element={<PrivateRoute><RoutineDetailPage /></PrivateRoute>} />
          <Route path="/routine/:id/analyze" element={<PrivateRoute><ExerciseCameraPage /></PrivateRoute>} />
          <Route path="/diet/ingredients" element={<PrivateRoute><IngredientInputPage /></PrivateRoute>} /> 
          <Route path="/diet/menu" element={<PrivateRoute><MenuRecommendationPage /></PrivateRoute>} />   
          <Route path="/chatbot" element={<PrivateRoute><ChatbotPage /></PrivateRoute>} />         
          <Route path="/avatar" element={<PrivateRoute><AvatarProgressPage /></PrivateRoute>} /> 

          {/* NotFoundPage는 항상 마지막에 배치 */}
          <Route path="*" element={<NotFoundPage />} /> 
        </Routes>

        <ConditionalNavbar />
      </div>
    </Router>
  );
}

export default App;