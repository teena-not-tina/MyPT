// src/pages/Auth/LoginPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../../styles/global.css'; // 공통 스타일 임포트

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault(); // 폼 제출 시 페이지 새로고침 방지
    console.log('로그인 시도:', { email, password });
    // TODO: 백엔드 로그인 API 연동 (나중에 구현)
    alert('로그인 시도 (백엔드 연동 전)');
    // 실제 로그인 성공 시 navigate('/dashboard'); 등으로 이동
  };

  return (
    <div className="page-content-wrapper auth-page-container">
      <h2 className="auth-title">로그인</h2>
      <form onSubmit={handleLogin} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">이메일:</label>
          <input
            type="email"
            id="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="이메일을 입력해주세요"
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">비밀번호:</label>
          <input
            type="password"
            id="password"
            className="form-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="비밀번호를 입력해주세요"
          />
        </div>
        <button type="submit" className="primary-button auth-button">
          로그인
        </button>
      </form>
      <p className="auth-link-text">
        계정이 없으신가요? <Link to="/signup" className="auth-link">회원가입</Link>
      </p>
    </div>
  );
}

export default LoginPage;