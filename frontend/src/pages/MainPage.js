import React from "react";

/**
 * MainPage shown after login.
 * TODO: Change this to Chatbot page in future.
 */
export default function MainPage() {
  return (
    <div style={{
      maxWidth: '768px',
      margin: '0 auto',
      minHeight: '100vh',
      padding: '2.5rem 1rem'
    }}>
      <div style={{
        textAlign: 'center',
        marginTop: '5rem'
      }}>
        <h1 style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          marginBottom: '1rem'
        }}>
          메인 페이지
        </h1>
        <p style={{
          fontSize: '1rem',
          color: '#6b7280',
          marginTop: '1rem'
        }}>
          로그인 성공! (여기서 챗봇 페이지로 이동하도록 변경 예정)
        </p>
      </div>
    </div>
  );
}