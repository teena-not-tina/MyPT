// src/pages/Auth/SignupPage.js
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

    console.log('회원가입 시도:', { email, password });

    try {
      const response = await fetch('http://localhost:5000/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      });

      if (!response.ok) {
        throw new Error('회원가입 실패');
      }

      const data = await response.json();
      console.log('회원가입 성공:', data);
      alert('회원가입이 성공적으로 완료되었습니다!');
      navigate('/login'); // 회원가입 성공 후 로그인 페이지로 이동
      // 또는 navigate('/onboarding/inbody'); // 온보딩 페이지로 이동 (프로젝트 흐름에 따라)

    } catch (error) {
      // 에러 발생 시 처리
      console.error('회원가입 실패:', error);
      alert('회원가입 중 오류가 발생했습니다.');
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