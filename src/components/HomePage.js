import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css'; // 별도 CSS 파일 사용 가능

function HomePage() {
  return (
    <div className="home-page">
      {/* 히어로 섹션 */}
      <section className="hero-section" style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        textAlign: 'center',
        padding: '2rem'
      }}>
        <h1 style={{
          fontSize: '3.5rem',
          marginBottom: '1rem',
          fontWeight: 'bold'
        }}>
          🏋️‍♂️ MyPT
        </h1>
        <p style={{
          fontSize: '1.5rem',
          marginBottom: '2rem',
          maxWidth: '600px'
        }}>
          AI 기반 개인 트레이너와 영양 관리 서비스
        </p>
        <p style={{
          fontSize: '1.1rem',
          marginBottom: '3rem',
          opacity: 0.9
        }}>
          음식을 촬영하면 AI가 영양 정보를 분석하고 맞춤형 식단을 추천해드립니다
        </p>
        
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link to="/main" style={{
            padding: '14px 32px',
            backgroundColor: 'white',
            color: '#667eea',
            textDecoration: 'none',
            borderRadius: '30px',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            transition: 'all 0.3s',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
          }}>
            시작하기
          </Link>
          
          <Link to="/food-detection" style={{
            padding: '14px 32px',
            backgroundColor: 'transparent',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '30px',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            border: '2px solid white',
            transition: 'all 0.3s'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = 'white';
            e.target.style.color = '#667eea';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'transparent';
            e.target.style.color = 'white';
          }}>
            음식 분석 체험하기
          </Link>
        </div>
      </section>

      {/* 기능 소개 섹션 */}
      <section style={{
        padding: '4rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <h2 style={{
          fontSize: '2.5rem',
          textAlign: 'center',
          marginBottom: '3rem',
          color: '#2c3e50'
        }}>
          주요 기능
        </h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem'
        }}>
          <FeatureCard
            icon="📸"
            title="AI 음식 인식"
            description="사진 한 장으로 음식을 자동으로 인식하고 영양 정보를 분석합니다"
          />
          <FeatureCard
            icon="📊"
            title="영양 분석"
            description="칼로리, 단백질, 탄수화물, 지방 등 상세한 영양 성분을 제공합니다"
          />
          <FeatureCard
            icon="👨‍🍳"
            title="요리 모드"
            description="건강한 레시피와 요리 방법을 단계별로 안내해드립니다"
          />
          <FeatureCard
            icon="📈"
            title="진행 상황 추적"
            description="일일 섭취량을 기록하고 목표 달성률을 확인할 수 있습니다"
          />
          <FeatureCard
            icon="🎯"
            title="맞춤형 추천"
            description="개인의 목표와 선호도에 맞는 식단을 추천받을 수 있습니다"
          />
          <FeatureCard
            icon="🌐"
            title="다국어 지원"
            description="한국어와 영어를 지원하며 전 세계 음식을 인식합니다"
          />
        </div>
      </section>

      {/* CTA 섹션 */}
      <section style={{
        background: '#f8f9fa',
        padding: '4rem 2rem',
        textAlign: 'center'
      }}>
        <h2 style={{
          fontSize: '2rem',
          marginBottom: '1rem',
          color: '#2c3e50'
        }}>
          지금 바로 시작하세요!
        </h2>
        <p style={{
          fontSize: '1.2rem',
          marginBottom: '2rem',
          color: '#7f8c8d'
        }}>
          건강한 삶을 위한 첫 걸음을 내딛어보세요
        </p>
        <Link to="/main" style={{
          display: 'inline-block',
          padding: '16px 40px',
          backgroundColor: '#3498db',
          color: 'white',
          textDecoration: 'none',
          borderRadius: '30px',
          fontSize: '1.2rem',
          fontWeight: 'bold',
          transition: 'all 0.3s',
          boxShadow: '0 4px 15px rgba(52, 152, 219, 0.3)'
        }}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = '#2980b9';
          e.target.style.transform = 'translateY(-2px)';
          e.target.style.boxShadow = '0 6px 20px rgba(52, 152, 219, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = '#3498db';
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = '0 4px 15px rgba(52, 152, 219, 0.3)';
        }}>
          무료로 시작하기
        </Link>
      </section>
    </div>
  );
}

// 기능 카드 컴포넌트
function FeatureCard({ icon, title, description }) {
  return (
    <div style={{
      background: 'white',
      padding: '2rem',
      borderRadius: '12px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
      textAlign: 'center',
      transition: 'all 0.3s'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-5px)';
      e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>{icon}</div>
      <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#2c3e50' }}>{title}</h3>
      <p style={{ color: '#7f8c8d', lineHeight: '1.6' }}>{description}</p>
    </div>
  );
}

export default HomePage;