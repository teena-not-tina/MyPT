// LoginPage.js
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login-json', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // 토큰과 사용자 정보 저장
        sessionStorage.setItem('access_token', data.access_token);
        sessionStorage.setItem('token_type', data.token_type);
        sessionStorage.setItem('user_id', data.user_id);

        console.log('로그인 성공, 저장된 데이터:', {
          access_token: data.access_token ? '있음' : '없음',
          user_id: data.user_id
        });
          // 디버깅 로그 추가
        console.log('로그인 응답 데이터:', data);
        console.log('저장된 토큰:', data.access_token);
        console.log('토큰 타입:', data.token_type);
        console.log('사용자 ID:', data.user_id);  

        // 대시보드로 이동
        setTimeout(() => {
          navigate('/dashboard');
        }, 0);
      } else {
        setError(data.detail || '로그인에 실패했습니다.');
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f3f4f6',
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          textAlign: 'center',
          marginBottom: '1.5rem'
        }}>
          로그인
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              marginBottom: '0.25rem'
            }}>
              이메일
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
              placeholder="user@example.com"
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              marginBottom: '0.25rem'
            }}>
              비밀번호
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div style={{
              padding: '0.75rem',
              marginBottom: '1rem',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '0.375rem',
              color: '#c00',
              fontSize: '0.875rem'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.5rem 1rem',
              backgroundColor: loading ? '#9ca3af' : '#3b82f6',
              color: 'white',
              borderRadius: '0.375rem',
              fontSize: '1rem',
              fontWeight: '500',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginBottom: '1rem'
            }}
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <p style={{
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#6b7280'
        }}>
          계정이 없으신가요?{' '}
          <Link to="/register" style={{
            color: '#3b82f6',
            textDecoration: 'none',
            fontWeight: '500'
          }}>
            회원가입
          </Link>
        </p>
      </div>
    </div>
  );
}