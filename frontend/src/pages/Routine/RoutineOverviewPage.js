import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header';
import ChatbotPage from '../AI/ChatbotPage';
import '../../styles/global.css';
import './RoutineOverviewPage.css';

function RoutineOverviewPage() {
  const navigate = useNavigate();
  const [showChatbot, setShowChatbot] = useState(false);

  // 예시용 더미 루틴 데이터
  const dummyRoutines = [
    { id: '1', name: '전신 근력 운동 - 초급', description: '초보자를 위한 전신 운동 루틴', days: 3 },
    { id: '2', name: '상체 강화 운동 - 중급', description: '가슴, 등, 어깨 위주의 루틴', days: 2 },
    { id: '3', name: '하체 집중 운동 - 고급', description: '강도 높은 하체 루틴', days: 1 },
  ];

  const handleAddRoutine = () => {
    alert('새 루틴 추가 기능은 나중에 구현됩니다.');
    // navigate('/routine/new');
  };

  return (
    <div className="page-container">
      <Header title="나의 운동 루틴" />
      <div className="page-content-wrapper routine-overview-page-content">
        <h2 className="routine-list-title">나의 루틴</h2>
        <button className="add-routine-button primary-button" onClick={handleAddRoutine}>
          <i className="fas fa-plus"></i> 새 루틴 추가
        </button>
        <div className="routine-list">
          {dummyRoutines.length > 0 ? (
            dummyRoutines.map((routine) => (
              <div key={routine.id} className="routine-card">
                <h3>{routine.name}</h3>
                <p>{routine.description}</p>
                <p className="routine-days">주 {routine.days}회</p>
                <Link to={`/routine/${routine.id}`} className="view-routine-button">
                  <i className="fas fa-arrow-right"></i> 루틴 상세 보기
                </Link>
              </div>
            ))
          ) : (
            <p className="no-routine-message">아직 등록된 루틴이 없습니다. 새로운 루틴을 추가해보세요!</p>
          )}
        </div>
      </div>

      {/* 우측하단 채팅 아이콘 (SVG 말풍선) */}
      {!showChatbot && (
        <button
          className="floating-chatbot-btn"
          onClick={() => setShowChatbot(true)}
          aria-label="AI 트레이너 열기"
        >
          {/* 말풍선 SVG 아이콘 */}
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" stroke="#fff" strokeWidth="2" fill="#1976d2"/>
          </svg>
        </button>
      )}

      {/* 챗봇 창 (전체화면, 애니메이션) */}
      {showChatbot && (
        <div className="floating-chatbot-full-window">
          <button
            className="close-chatbot-btn"
            onClick={() => setShowChatbot(false)}
            aria-label="챗봇 닫기"
          >
            ×
          </button>
          <ChatbotPage />
        </div>
      )}
    </div>
  );
}

export default RoutineOverviewPage;