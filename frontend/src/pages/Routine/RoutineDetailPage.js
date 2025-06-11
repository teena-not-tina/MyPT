import React from 'react';

// Header 컴포넌트 (뒤로가기 버튼 포함)
function Header({ title, showBackButton = false, onBackClick }) {
  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      alert('뒤로 가기');
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="flex items-center justify-between px-4 py-3 max-w-screen-xl mx-auto">
        <div className="flex items-center space-x-3">
          {showBackButton && (
            <button 
              onClick={handleBackClick} 
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          <h1 className="text-lg font-semibold text-gray-900 truncate">{title}</h1>
        </div>
        <div className="w-8"></div>
      </div>
    </header>
  );
}

function RoutineDetailPage() {
  // URL에서 ID를 가져왔다고 가정하고 루틴 1을 표시
  const id = '1';

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

  const handleStartExercise = () => {
    alert(`"${routine.name}" 운동 시작!`);
  };

  const handleGoBack = () => {
    alert('루틴 목록으로 돌아가기');
  };

  if (!routine) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title="루틴 상세" showBackButton={true} />
        <div className="max-w-screen-xl mx-auto px-4 py-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 13.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <p className="text-gray-600 text-lg mb-4">해당 루틴을 찾을 수 없습니다.</p>
            <button 
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              onClick={handleGoBack}
            >
              루틴 목록으로 돌아가기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title={routine.name} showBackButton={true} />
      
      <div className="max-w-screen-xl mx-auto px-4 py-6">
        {/* 루틴 설명 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <p className="text-gray-600 text-lg leading-relaxed">{routine.description}</p>
        </div>

        {/* 운동 목록 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
            <svg className="w-6 h-6 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            운동 목록
          </h3>
          
          <div className="space-y-4">
            {routine.exercises.map((exercise, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors duration-200">
                <div className="flex items-start justify-between mb-3">
                  <h4 className="text-lg font-semibold text-gray-900">{exercise.name}</h4>
                  <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                    #{index + 1}
                  </span>
                </div>
                
                <div className="flex flex-wrap gap-4 mb-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    <span className="font-medium">세트:</span>
                    <span className="ml-1">{exercise.sets}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="font-medium">반복:</span>
                    <span className="ml-1">{exercise.reps || exercise.time}</span>
                  </div>
                </div>
                
                {exercise.notes && (
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                    <div className="flex items-start">
                      <svg className="w-4 h-4 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="text-sm text-yellow-800">
                        <span className="font-medium">주의사항:</span> {exercise.notes}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 운동 시작 버튼 */}
        <div className="sticky bottom-4">
          <button 
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl transform hover:scale-105"
            onClick={handleStartExercise}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293H15M9 10v4a2 2 0 002 2h2a2 2 0 002-2v-4M9 10V6a2 2 0 012-2h2a2 2 0 012 2v4" />
            </svg>
            <span className="text-lg">운동 시작하기</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default RoutineDetailPage;