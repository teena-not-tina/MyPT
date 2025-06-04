// src/pages/AI/AvatarProgressPage.js
import React from 'react';
import Header from '../../components/Shared/Header'; // 헤더 임포트
import '../../styles/global.css'; // 공통 스타일 임포트
import './AvatarProgressPage.css'; // 아바타 페이지 전용 스타일 (새로 생성)

function AvatarProgressPage() {
  // 실제로는 Zustand 스토어 또는 백엔드에서 사용자 및 아바타 정보를 가져올 것입니다.
  const dummyUserData = {
    userName: '김헬린',
    avatarImage: '/images/default_avatar.png', // 실제 아바타 이미지 경로 (나중에 추가)
    currentLevel: 5,
    progressPercentage: 60, // 다음 레벨까지의 진행도
    routineCompleted: 15, // 완료된 루틴 수
    dietRecorded: 25, // 기록된 식단 수
    lastActive: '2025-06-02',
  };

  return (
    <div className="page-container">
      <Header title="나의 아바타" showBackButton={true} />
      <div className="page-content-wrapper avatar-progress-page-content">
        <h2 className="avatar-title">안녕하세요, {dummyUserData.userName}님!</h2>
        
        {/* 아바타 이미지 영역 */}
        <div className="avatar-image-container">
          {dummyUserData.avatarImage ? (
            <img 
              src={dummyUserData.avatarImage} 
              alt="My Avatar" 
              className="avatar-image" 
            />
          ) : (
            <div className="avatar-placeholder">
              <i className="fas fa-user-circle"></i>
              <p>아바타 이미지가 여기에 표시됩니다.</p>
            </div>
          )}
          <p className="avatar-level">Lv. {dummyUserData.currentLevel}</p>
        </div>

        {/* 진행도 바 */}
        <div className="progress-bar-container">
          <div className="progress-bar-fill" style={{ width: `${dummyUserData.progressPercentage}%` }}></div>
          <span className="progress-text">다음 레벨까지 {dummyUserData.progressPercentage}%</span>
        </div>

        {/* 핵심 정보 요약 */}
        <div className="summary-cards">
          <div className="summary-card">
            <i className="fas fa-dumbbell card-icon"></i>
            <h3>운동 루틴</h3>
            <p className="card-value">{dummyUserData.routineCompleted}회 완료</p>
            <p className="card-note">이번 주 3회 완료</p> {/* 예시 */}
          </div>
          <div className="summary-card">
            <i className="fas fa-utensils card-icon"></i>
            <h3>식단 기록</h3>
            <p className="card-value">{dummyUserData.dietRecorded}회 기록</p>
            <p className="card-note">오늘 아침 기록 완료</p> {/* 예시 */}
          </div>
        </div>

        {/* 추가 정보 (나중에 상세 내용 추가) */}
        <div className="additional-info-section">
          <h3>아바타 히스토리</h3>
          <p className="info-placeholder">
            아바타의 성장 스토리가 여기에 표시됩니다.
            <br />(달성한 목표, 변화 등)
          </p>
        </div>

        <div className="additional-info-section">
          <h3>나의 목표</h3>
          <p className="info-placeholder">
            등록된 목표가 여기에 표시됩니다.
            <br />(예: 체지방 5kg 감량, 스쿼트 100kg 달성)
          </p>
        </div>
      </div>
    </div>
  );
}

export default AvatarProgressPage;