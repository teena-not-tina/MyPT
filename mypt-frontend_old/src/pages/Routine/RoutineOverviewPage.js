// src/pages/Routine/RoutineOverviewPage.js
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header'; // 헤더 임포트
import '../../styles/global.css'; // 공통 스타일 임포트
import './RoutineOverviewPage.css'; // 루틴 페이지 전용 스타일

function RoutineOverviewPage() {
  const navigate = useNavigate();

  // 실제 루틴 데이터가 들어올 자리 (나중에 백엔드에서 가져옴)
  const dummyRoutines = [
    { id: '1', name: '전신 근력 운동 - 초급', description: '초보자를 위한 전신 운동 루틴', days: 3 },
    { id: '2', name: '상체 강화 운동 - 중급', description: '가슴, 등, 어깨 위주의 루틴', days: 2 },
    { id: '3', name: '하체 집중 운동 - 고급', description: '강도 높은 하체 루틴', days: 1 },
  ];

  const handleAddRoutine = () => {
    alert('새 루틴 추가 기능은 나중에 구현됩니다.');
    // navigate('/routine/new'); // 새 루틴 추가 페이지로 이동 (필요 시)
  };

  return (
    <div className="page-container">
      <Header title="나의 운동 루틴" />
      <div className="page-content-wrapper routine-overview-page-content">
        <h2 className="routine-list-title">나의 루틴</h2>
        
        {/* 새 루틴 추가 버튼 */}
        <button className="add-routine-button primary-button" onClick={handleAddRoutine}>
          <i className="fas fa-plus"></i> 새 루틴 추가
        </button>

        {/* 루틴 목록 */}
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
    </div>
  );
}

export default RoutineOverviewPage;