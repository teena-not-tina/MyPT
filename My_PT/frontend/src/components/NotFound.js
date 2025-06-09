import React from 'react';
import { Link } from 'react-router-dom';

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

export default NotFound;