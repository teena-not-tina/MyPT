// src/pages/Auth/LoginPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../../styles/global.css';
import useAuthStore from '../../stores/authStore'; // useAuthStore 임포트

const API_BASE_URL = 'http://localhost:5000'; // API 기본 URL 설정

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  // useAuthStore에서 login 액션 가져오기 (혹은 setAuthenticated 같은 액션)
  const login = useAuthStore((state) => state.login); // 예시: 'login' 액션이 있다고 가정

  const handleLogin = async (e) => {
    e.preventDefault();
    
    try {
        const response = await axios.post(
            'http://localhost:5000/api/auth/login',
            {
                email,
                password
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                },
                withCredentials: true
            }
        );

        if (response.data.success) {
            // 로그인 성공 시 사용자 정보 저장
            localStorage.setItem('user', JSON.stringify(response.data.user));
            // 로그인 상태 업데이트
            login();
            navigate('/onboarding/inbody');
        }
    } catch (error) {
        console.error('로그인 오류:', error);
        const errorMessage = error.response?.data?.error || '로그인 중 오류가 발생했습니다.';
        alert(errorMessage);
    }
  };

  return (
    <div className="page-content-wrapper auth-page-container">
      <h2 className="auth-title">로그인</h2>
      {error && <div className="error-message">{error}</div>}
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