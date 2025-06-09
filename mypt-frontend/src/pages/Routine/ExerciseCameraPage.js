// src/pages/Routine/ExerciseCameraPage.js
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Header from '../../components/Shared/Header';
import '../../styles/global.css';
import './ExerciseCameraPage.css'; // 자세 분석 페이지 전용 스타일 (새로 생성)

function ExerciseCameraPage() {
  const { id } = useParams(); // 루틴 ID를 가져올 수 있습니다.
  const navigate = useNavigate();

  const handleFinishAnalysis = () => {
    alert('자세 분석 종료 (실제 로직 구현 필요)');
    navigate(`/routine/${id}`); // 루틴 상세 페이지로 돌아가기
  };

  return (
    <div className="page-container">
      <Header title="자세 분석 중..." showBackButton={true} />
      <div className="page-content-wrapper exercise-camera-page-content">
        <p className="analysis-status">
          <i className="fas fa-video"></i> 카메라 준비 중...
        </p>
        
        {/* 카메라 피드/인식 영역 플레이스홀더 */}
        <div className="camera-feed-placeholder">
          {/* 실제 웹캠 스트림이 여기에 렌더링될 것입니다. */}
          {/* <video ref={videoRef} autoPlay playsInline muted className="camera-video"></video> */}
          <p>카메라 영상이 여기에 표시됩니다.</p>
          <p>자세 인식을 위해 카메라를 바라봐 주세요.</p>
        </div>

        {/* 운동 가이드 텍스트 (옵션) */}
        <div className="exercise-guide">
          <h3>다음 운동: 스쿼트</h3>
          <p>반복 횟수: 3/10</p>
          <p>자세를 정확히 유지해주세요!</p>
        </div>

        {/* 분석 종료 버튼 */}
        <button className="end-analysis-button primary-button" onClick={handleFinishAnalysis}>
          <i className="fas fa-stop-circle"></i> 분석 종료
        </button>
      </div>
    </div>
  );
}

export default ExerciseCameraPage;