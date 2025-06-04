// src/pages/Home/DashboardPage.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/global.css'; // 공통 스타일 임포트
import './DashboardPage.css'; // 대시보드 전용 스타일 임포트

function DashboardPage() {
  const navigate = useNavigate();

  // "운동 시작하기" 버튼 클릭 시 동작
  const handleStartWorkout = () => {
    console.log('운동 시작하기 클릭');
    navigate('/routine'); // 운동 루틴 페이지로 이동 (예시)
  };

  // "식단 기록하기" 버튼 클릭 시 동작
  const handleRecordDiet = () => {
    console.log('식단 기록하기 클릭');
    navigate('/diet/ingredients'); // 식단 기록 페이지로 이동 (예시)
  };

  // ⭐️⭐️⭐️ character-placeholder 클릭 핸들러 추가 ⭐️⭐️⭐️
  const handleCharacterClick = () => {
    console.log('캐릭터 플레이스홀더 클릭');
    navigate('/avatar'); // AvatarProgressPage 경로로 이동
  };

  return (
    <div className="page-content-wrapper dashboard-container">
      {/* 상단 버튼 섹션 */}
      <div className="dashboard-buttons">
        <button className="dashboard-button workout-button" onClick={handleStartWorkout}>
          운동 시작하기
        </button>
        <button className="dashboard-button diet-button" onClick={handleRecordDiet}>
          식단 기록하기
        </button>
      </div>

      {/* 중앙 캐릭터/이미지 공간 */}
      <div className="dashboard-character-area">
        {/* ⭐️⭐️⭐️ character-placeholder에 onClick 이벤트 추가 ⭐️⭐️⭐️ */}
        <div className="character-placeholder" onClick={handleCharacterClick}>
          {/* 여기에 인바디 기반 캐릭터 이미지가 들어갈 공간 */}
          {/* <img src="/path/to/your/character-image.png" alt="MyPT Character" className="character-image" /> */}
          {/* 현재는 파란색 원으로 표시 */}
          {/* 클릭 유도를 위한 텍스트 추가 (선택 사항, CSS로 숨기거나 디자인에 맞게) */}
          <p className="character-click-hint">내 아바타 보기 (클릭)</p>
        </div>
      </div>

      {/* 하단 네비게이션 바는 App.js의 ConditionalNavbar에서 렌더링되므로 여기서는 제외 */}
    </div>
  );
}

export default DashboardPage;