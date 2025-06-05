// src/pages/Routine/RoutineDetailPage.js
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header'; // 헤더 임포트
import '../../styles/global.css'; // 공통 스타일 임포트
import './RoutineDetailPage.css'; // 루틴 상세 페이지 전용 스타일 (새로 생성)

function RoutineDetailPage() {
  const { id } = useParams(); // URL 파라미터에서 루틴 ID를 가져옴
  const navigate = useNavigate();

  // 실제 루틴 데이터를 백엔드에서 가져올 때 사용할 더미 데이터
  const dummyRoutineDetails = {
    '1': {
      name: '전신 근력 운동 - 초급',
      description: '초보자를 위한 전신 운동 루틴입니다.',
      exercises: [
        { name: '스쿼트', sets: 3, reps: 10, notes: '무릎이 발끝을 넘지 않도록' },
        { name: '푸쉬업', sets: 3, reps: '최대', notes: '무릎 대고 실시 가능' },
        { name: '런지', sets: 3, reps: 10, notes: '양쪽 다리 번갈아' },
        { name: '플랭크', sets: 3, time: '60초', notes: '복근에 힘 유지' },
      ],
    },
    '2': {
      name: '상체 강화 운동 - 중급',
      description: '가슴, 등, 어깨 위주의 루틴입니다.',
      exercises: [
        { name: '벤치프레스', sets: 3, reps: 12, notes: '가슴에 집중' },
        { name: '덤벨 로우', sets: 3, reps: 10, notes: '등 근육 자극' },
        { name: '오버헤드 프레스', sets: 3, reps: 10, notes: '어깨 운동' },
      ],
    },
    '3': {
      name: '하체 집중 운동 - 고급',
      description: '강도 높은 하체 루틴입니다.',
      exercises: [
        { name: '바벨 스쿼트', sets: 4, reps: 8, notes: '깊게 앉기' },
        { name: '데드리프트', sets: 3, reps: 6, notes: '허리 부상 주의' },
        { name: '레그 프레스', sets: 3, reps: 15, notes: '최대 이완' },
      ],
    },
  };

  const routine = dummyRoutineDetails[id];

  if (!routine) {
    return (
      <div className="page-container">
        <Header title="루틴 상세" showBackButton={true} />
        <div className="page-content-wrapper">
          <p>해당 루틴을 찾을 수 없습니다.</p>
          <button className="primary-button" onClick={() => navigate('/routine')}>
            루틴 목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  const handleStartExercise = () => {
    // 실제 운동 시작 로직 (예: 첫 번째 운동의 자세 분석 페이지로 이동)
    alert(`"${routine.name}" 운동 시작!`);
    navigate(`/routine/${id}/analyze`); // 자세 분석 페이지로 이동
  };

  return (
    <div className="page-container">
      <Header title={routine.name} showBackButton={true} /> {/* 뒤로 가기 버튼 추가 */}
      <div className="page-content-wrapper routine-detail-page-content">
        <p className="routine-detail-description">{routine.description}</p>

        <h3 className="exercise-list-title">운동 목록</h3>
        <ul className="exercise-list">
          {routine.exercises.map((exercise, index) => (
            <li key={index} className="exercise-item">
              <h4>{exercise.name}</h4>
              <p>세트: {exercise.sets} / 반복: {exercise.reps || exercise.time}</p>
              {exercise.notes && <p className="exercise-notes">주의사항: {exercise.notes}</p>}
            </li>
          ))}
        </ul>

        <button className="start-exercise-button primary-button" onClick={handleStartExercise}>
          <i className="fas fa-play"></i> 운동 시작하기
        </button>
      </div>
    </div>
  );
}

export default RoutineDetailPage;