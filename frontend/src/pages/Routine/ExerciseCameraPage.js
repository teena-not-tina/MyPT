// src/pages/Routine/ExerciseCameraPage.js
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Header from '../Shared/Header';

function ExerciseCameraPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const handleFinishAnalysis = () => {
    alert('자세 분석 종료 (실제 로직 구현 필요)');
    navigate(`/routine/${id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="자세 분석 중..." showBackButton={true} />
      
      <div className="px-4 py-6 space-y-6">
        {/* 상태 표시 */}
        <div className="flex items-center justify-center space-x-2 text-blue-600">
          <i className="fas fa-video text-xl"></i>
          <p className="text-lg font-medium">카메라 준비 중...</p>
        </div>
        
        {/* 카메라 피드 영역 */}
        <div className="bg-gray-900 rounded-lg aspect-video flex flex-col items-center justify-center text-white space-y-4 shadow-lg">
          <div className="text-center space-y-2">
            <i className="fas fa-camera text-4xl text-gray-400"></i>
            <p className="text-lg">카메라 영상이 여기에 표시됩니다.</p>
            <p className="text-sm text-gray-300">자세 인식을 위해 카메라를 바라봐 주세요.</p>
          </div>
        </div>

        {/* 운동 가이드 */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 mb-4">다음 운동: 스쿼트</h3>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <p className="text-gray-700">반복 횟수: <span className="font-semibold text-blue-600">3/10</span></p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <p className="text-gray-700">자세를 정확히 유지해주세요!</p>
            </div>
          </div>
        </div>

        {/* 분석 종료 버튼 */}
        <button 
          className="w-full bg-red-500 hover:bg-red-600 text-white font-semibold py-4 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2 shadow-sm"
          onClick={handleFinishAnalysis}
        >
          <i className="fas fa-stop-circle text-xl"></i>
          <span>분석 종료</span>
        </button>
      </div>
    </div>
  );
}

export default ExerciseCameraPage;