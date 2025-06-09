// src/pages/AI/AvatarProgressPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header';
import '../../styles/global.css';
import './AvatarProgressPage.css';
import chibiAvatar from '../../assets/images/chibi_avatar.png';

function AvatarProgressPage() {
  const [profileImage, setProfileImage] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const navigate = useNavigate();

  const handleAvatarClick = () => {
    navigate('/avatar');
  };

  const dummyUserData = {
    userName: '김헬린',
    avatarImage: '/images/default_avatar.png',
    currentLevel: 5,
    progressPercentage: 60,
    routineCompleted: 15,
    dietRecorded: 25,
    lastActive: '2025-06-02',
  };

  useEffect(() => {
    const savedImage = localStorage.getItem('userProfileImage');
    if (savedImage) {
      setProfileImage(savedImage);
      setTimeLeft(30);
      
      // 1초마다 타이머 업데이트
      const intervalId = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(intervalId);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      // 컴포넌트 언마운트 시 정리
      return () => clearInterval(intervalId);
    }
  }, []);

  return (
    <div className="page-container">
      <Header title="나의 아바타" showBackButton={true} />
      <div className="page-content-wrapper avatar-progress-page-content">
        <h2 className="avatar-title">안녕하세요, {dummyUserData.userName}님!</h2>
        
        {/* 중앙 캐릭터/이미지 영역 */}
        <div className="dashboard-character-area">
          <div className="character-placeholder" onClick={handleAvatarClick}>
            {profileImage && timeLeft > 0 && (
              <div className={`timer-overlay ${timeLeft === 0 ? 'hidden' : ''}`}>
                {timeLeft}초
              </div>
            )}
            <img
              src={profileImage ? `data:image/png;base64,${profileImage}` : chibiAvatar}
              alt="내 아바타"
              className="character-image"
            />
          </div>
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