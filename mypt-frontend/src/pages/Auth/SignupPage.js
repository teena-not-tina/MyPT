// src/pages/Auth/SignupPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios'; // axios 임포트
import '../../styles/global.css'; // 공통 스타일 임포트

function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
        alert('비밀번호와 비밀번호 확인이 일치하지 않습니다.');
        return;
    }

    try {
        const response = await axios.post(
            'http://localhost:5000/api/auth/register',
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
            alert('회원가입이 완료되었습니다!');
            navigate('/login');
        }
    } catch (error) {
        console.error('회원가입 실패:', error);
        const errorMessage = error.response?.data?.error || '회원가입 중 오류가 발생했습니다.';
        alert(errorMessage);
    }
  };

  return (
    <div className="page-content-wrapper auth-page-container">
      <h2 className="auth-title">회원가입</h2>
      <form onSubmit={handleSignup} className="auth-form">
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
        <div className="form-group">
          <label htmlFor="confirmPassword">비밀번호 확인:</label>
          <input
            type="password"
            id="confirmPassword"
            className="form-input"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            placeholder="비밀번호를 다시 입력해주세요"
          />
        </div>
        <button type="submit" className="primary-button auth-button">
          회원가입
        </button>
      </form>
      <p className="auth-link-text">
        이미 계정이 있으신가요? <Link to="/login" className="auth-link">로그인</Link>
      </p>
    </div>
  );
}

export default SignupPage;