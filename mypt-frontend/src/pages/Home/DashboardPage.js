// src/pages/Home/DashboardPage.js (프론트엔드 파일)
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/global.css';
import './DashboardPage.css';
import ChibiAvatar from '../../assets/images/chibi_avatar.png';

function DashboardPage() {
  const navigate = useNavigate();
  const [profileImage, setProfileImage] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30); // 타이머 상태 추가

  useEffect(() => {
    const savedImage = localStorage.getItem('userProfileImage');
    if (savedImage) {
      setProfileImage(savedImage);
      setTimeLeft(30); // 타이머 초기화
      
      // 1초마다 타이머 업데이트
      const intervalId = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(intervalId);
            setProfileImage(null);
            localStorage.removeItem('userProfileImage');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      // 30초 후에 이미지 초기화
      const timer = setTimeout(() => {
        setProfileImage(null);
        localStorage.removeItem('userProfileImage');
        console.log('이미지가 기본 이미지로 초기화되었습니다.');
      }, 30000);

      return () => {
        clearTimeout(timer);
        clearInterval(intervalId);
      };
    }
  }, []);

  // TODO: 실제 사용자 데이터 및 아바타 상태 관리 로직 추가

  // 버튼 클릭 핸들러 (예시)
  const handleWorkoutClick = () => {
    navigate('/routine'); // 운동 루틴 페이지로 이동 (App.js 라우트 참고)
  };

  const handleDietClick = () => {
    navigate('/diet/menu'); // 식단 추천 페이지로 이동 (App.js 라우트 참고)
  };

  // 아바타 클릭 핸들러
  const handleAvatarClick = () => {
    navigate('/avatar'); // 아바타 진행 상황 페이지로 이동 (App.js 라우트 참고)
  };

  return (
    <div className="dashboard-container"> {/* CSS의 .dashboard-container 적용 */}
      <h2 className="dashboard-title">환영합니다!</h2> {/* 타이틀은 그대로 유지 */}

      {/* 상단 버튼 컨테이너 */}
      <div className="dashboard-buttons"> {/* CSS의 .dashboard-buttons 적용 */}
        <button className="dashboard-button workout-button" onClick={handleWorkoutClick}>
          운동 시작하기
        </button>
        <button className="dashboard-button diet-button" onClick={handleDietClick}>
          식단 기록하기
        </button>
      </div>

      {/* 중앙 캐릭터/이미지 영역 */}
      <div className="dashboard-character-area"> {/* CSS의 .dashboard-character-area 적용 */}
        <div className="character-placeholder" onClick={handleAvatarClick}> {/* CSS의 .character-placeholder 적용 */}
          {/* ⭐️⭐️⭐️ 이미지 삽입 ⭐️⭐️⭐️ */}
          <img
            src={profileImage ? `data:image/png;base64,${profileImage}` : ChibiAvatar}
            alt="내 아바타"
            className="character-image" // CSS의 .character-image 적용
          />
          {profileImage && timeLeft > 0 && (
            <div className="timer-overlay">
              {timeLeft}초
            </div>
          )}
        </div>
      </div>
      
      {/* 추가적인 대시보드 정보나 섹션이 필요하다면 여기에 추가 */}
      {/* 이 부분은 CSS에 직접적인 클래스가 없으므로, 추가적인 스타일링 필요 */}
      {/* <div className="dashboard-info-sections">
        <h3>오늘의 진행 상황</h3>
        <p>어제보다 더 나은 당신이 되었습니다!</p>
      </div> */}
    </div>
  );
}

export default DashboardPage;