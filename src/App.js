import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import HomePage from './components/HomePage';
import MainPage from './components/MainPage';
import FoodDetectionApp from './components/FoodDetectionApp';
// import CookingMode from './components/CookingMode'; // 필요 없으면 주석 처리
import './App.css';

// 네비게이션 바 컴포넌트
function NavigationBar() {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // 홈페이지에서는 네비게이션 바를 숨김
  if (location.pathname === '/') {
    return null;
  }

  return (
    <nav className="navigation-bar" style={{
      backgroundColor: '#2c3e50',
      padding: '1rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div className="nav-container" style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Link to="/main" className="nav-logo" style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color: 'white',
          textDecoration: 'none'
        }}>
          🏋️‍♂️ MyPT
        </Link>

        {/* 데스크탑 메뉴 */}
        <div className="nav-links desktop-menu" style={{
          display: 'flex',
          gap: '2rem',
          alignItems: 'center'
        }}>
          <NavLink to="/main" currentPath={location.pathname}>
            홈
          </NavLink>
          <NavLink to="/food-detection" currentPath={location.pathname}>
            음식 분석
          </NavLink>
          {/* <NavLink to="/cooking" currentPath={location.pathname}>
            요리 모드
          </NavLink> */}
        </div>

        {/* 모바일 메뉴 버튼 */}
        <button
          className="mobile-menu-button"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          style={{
            display: 'none',
            background: 'none',
            border: 'none',
            color: 'white',
            fontSize: '1.5rem',
            cursor: 'pointer'
          }}
        >
          ☰
        </button>
      </div>

      {/* 모바일 메뉴 */}
      {isMenuOpen && (
        <div className="mobile-menu" style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: '#2c3e50',
          padding: '1rem',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <NavLink to="/main" currentPath={location.pathname} onClick={() => setIsMenuOpen(false)}>
            홈
          </NavLink>
          <NavLink to="/food-detection" currentPath={location.pathname} onClick={() => setIsMenuOpen(false)}>
            음식 분석
          </NavLink>
          {/* <NavLink to="/cooking" currentPath={location.pathname} onClick={() => setIsMenuOpen(false)}>
            요리 모드
          </NavLink> */}
        </div>
      )}
    </nav>
  );
}

// 네비게이션 링크 컴포넌트
function NavLink({ to, children, currentPath, onClick }) {
  const isActive = currentPath === to;
  
  return (
    <Link
      to={to}
      onClick={onClick}
      style={{
        color: isActive ? '#3498db' : 'white',
        textDecoration: 'none',
        padding: '0.5rem 1rem',
        borderRadius: '4px',
        transition: 'all 0.3s',
        backgroundColor: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
        display: 'block'
      }}
      onMouseEnter={(e) => {
        if (!isActive) {
          e.target.style.backgroundColor = 'rgba(255,255,255,0.05)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isActive) {
          e.target.style.backgroundColor = 'transparent';
        }
      }}
    >
      {children}
    </Link>
  );
}

// 레이아웃 컴포넌트
function Layout({ children }) {
  return (
    <>
      <NavigationBar />
      <main style={{ minHeight: 'calc(100vh - 60px)' }}>
        {children}
      </main>
    </>
  );
}

// 404 페이지 컴포넌트
function NotFound() {
  return (
    <div className="not-found-container" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      textAlign: 'center',
      padding: '2rem'
    }}>
      <h1 style={{ fontSize: '6rem', marginBottom: '1rem', color: '#e74c3c' }}>404</h1>
      <h2 style={{ marginBottom: '2rem', color: '#34495e' }}>페이지를 찾을 수 없습니다</h2>
      <p style={{ marginBottom: '2rem', color: '#7f8c8d' }}>
        요청하신 페이지가 존재하지 않거나 이동되었습니다.
      </p>
      <Link to="/main" style={{
        padding: '12px 24px',
        backgroundColor: '#3498db',
        color: 'white',
        textDecoration: 'none',
        borderRadius: '5px',
        transition: 'background-color 0.3s'
      }}
      onMouseEnter={(e) => e.target.style.backgroundColor = '#2980b9'}
      onMouseLeave={(e) => e.target.style.backgroundColor = '#3498db'}>
        메인으로 돌아가기
      </Link>
    </div>
  );
}

// 로딩 컴포넌트
function Loading() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh'
    }}>
      <div className="spinner" style={{
        border: '3px solid #f3f3f3',
        borderTop: '3px solid #3498db',
        borderRadius: '50%',
        width: '40px',
        height: '40px',
        animation: 'spin 1s linear infinite'
      }}></div>
    </div>
  );
}

// 메인 App 컴포넌트
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
            
            {/* 요리 모드 - 레시피 및 요리 가이드 */}
            {/* <Route path="/cooking" element={
              <CookingMode user={user} />
            } /> */}
            
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

// CSS 애니메이션 추가 (App.css에 추가)
const styles = `
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.mobile-menu-button {
  display: none !important;
}

@media (max-width: 768px) {
  .desktop-menu {
    display: none !important;
  }
  
  .mobile-menu-button {
    display: block !important;
  }
}

.navigation-bar {
  position: sticky;
  top: 0;
  z-index: 1000;
}
`;