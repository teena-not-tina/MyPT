import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

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
        </div>
      )}
    </nav>
  );
}

export default NavigationBar;