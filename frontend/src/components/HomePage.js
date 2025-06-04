import React from 'react';
import { testServerConnection } from '../services/api';

const HomePage = ({ onStartCooking, onStartEating }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🍽️</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            스마트 푸드 매니저
          </h1>
          <p className="text-gray-600 text-sm">
            AI로 똑똑하게 식사 계획하기
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={onStartCooking}
            className="w-full bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl hover:scale-105 active:scale-95"
          >
            <div className="flex items-center gap-4">
              <div className="bg-green-100 rounded-full p-3">
                <span className="text-2xl">👨‍🍳</span>
              </div>
              <div className="text-left flex-1">
                <h3 className="text-lg font-semibold text-gray-800">해먹기</h3>
                <p className="text-sm text-gray-600">냉장고 식재료로 요리하기</p>
              </div>
              <div className="text-gray-400">→</div>
            </div>
          </button>

          <button
            onClick={onStartEating}
            className="w-full bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl hover:scale-105 active:scale-95"
          >
            <div className="flex items-center gap-4">
              <div className="bg-orange-100 rounded-full p-3">
                <span className="text-2xl">🍽️</span>
              </div>
              <div className="text-left flex-1">
                <h3 className="text-lg font-semibold text-gray-800">사먹기</h3>
                <p className="text-sm text-gray-600">맛집 추천 및 주문하기</p>
              </div>
              <div className="text-gray-400">→</div>
            </div>
          </button>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={testServerConnection}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            서버 연결 테스트
          </button>
        </div>
      </div>
    </div>
  );
};

export default HomePage;