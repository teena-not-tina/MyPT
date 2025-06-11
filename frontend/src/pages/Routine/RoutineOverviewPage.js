import React from 'react';

// Header 컴포넌트 (간단 버전)
function Header({ title }) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="flex items-center justify-between px-4 py-3 max-w-screen-xl mx-auto">
        <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
      </div>
    </header>
  );
}

function RoutineOverviewPage() {
  // 실제 루틴 데이터가 들어올 자리 (나중에 백엔드에서 가져옴)
  const dummyRoutines = [
    { id: '1', name: '전신 근력 운동 - 초급', description: '초보자를 위한 전신 운동 루틴', days: 3 },
    { id: '2', name: '상체 강화 운동 - 중급', description: '가슴, 등, 어깨 위주의 루틴', days: 2 },
    { id: '3', name: '하체 집중 운동 - 고급', description: '강도 높은 하체 루틴', days: 1 },
  ];

  const handleAddRoutine = () => {
    alert('새 루틴 추가 기능은 나중에 구현됩니다.');
  };

  const handleViewRoutine = (routineId) => {
    alert(`루틴 ${routineId} 상세 보기`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="나의 운동 루틴" />
      
      <div className="max-w-screen-xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">나의 루틴</h2>
          
          {/* 새 루틴 추가 버튼 */}
          <button 
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2 shadow-sm"
            onClick={handleAddRoutine}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>새 루틴 추가</span>
          </button>
        </div>

        {/* 루틴 목록 */}
        <div className="space-y-4">
          {dummyRoutines.length > 0 ? (
            dummyRoutines.map((routine) => (
              <div key={routine.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex-1 mb-4 sm:mb-0">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{routine.name}</h3>
                    <p className="text-gray-600 mb-3">{routine.description}</p>
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        주 {routine.days}회
                      </span>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => handleViewRoutine(routine.id)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center space-x-2 w-full sm:w-auto justify-center"
                  >
                    <span>루틴 상세 보기</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <p className="text-gray-500 text-lg">아직 등록된 루틴이 없습니다.</p>
              <p className="text-gray-400 text-sm mt-1">새로운 루틴을 추가해보세요!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RoutineOverviewPage;