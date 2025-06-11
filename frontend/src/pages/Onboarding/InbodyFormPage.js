// src/pages/Onboarding/InbodyFormPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function InbodyFormPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    gender: '',
    age: '',
    height: '',
    weight: '',
    bodyFat: '',
    muscleMass: '',
    activityLevel: '',
    goal: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('인바디 및 사용자 정보 제출:', formData);
    alert('사용자 정보 입력 완료 (백엔드 연동 전)');
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          {/* 헤더 섹션 */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6">
            <h2 className="text-2xl font-bold text-white text-center">
              사용자 정보 및 인바디 입력
            </h2>
            <p className="text-blue-100 text-center mt-2 text-sm">
              정확한 식단 추천을 위해 정보를 입력해주세요
            </p>
          </div>

          {/* 폼 섹션 */}
          <form onSubmit={handleSubmit} className="p-8 space-y-6">
            {/* 성별 */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-700">
                성별 <span className="text-red-500">*</span>
              </label>
              <div className="flex space-x-6">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="gender"
                    value="male"
                    checked={formData.gender === 'male'}
                    onChange={handleChange}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    required
                  />
                  <span className="ml-2 text-gray-700">남성</span>
                </label>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="gender"
                    value="female"
                    checked={formData.gender === 'female'}
                    onChange={handleChange}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    required
                  />
                  <span className="ml-2 text-gray-700">여성</span>
                </label>
              </div>
            </div>

            {/* 기본 정보 그리드 */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* 나이 */}
              <div className="space-y-2">
                <label htmlFor="age" className="block text-sm font-semibold text-gray-700">
                  나이 <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="age"
                  name="age"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
                  value={formData.age}
                  onChange={handleChange}
                  required
                  placeholder="나이를 입력하세요"
                  min="1"
                  max="120"
                />
              </div>

              {/* 키 */}
              <div className="space-y-2">
                <label htmlFor="height" className="block text-sm font-semibold text-gray-700">
                  키 (cm) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="height"
                  name="height"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
                  value={formData.height}
                  onChange={handleChange}
                  required
                  placeholder="키를 입력하세요"
                  min="100"
                  max="250"
                />
              </div>

              {/* 체중 */}
              <div className="space-y-2">
                <label htmlFor="weight" className="block text-sm font-semibold text-gray-700">
                  체중 (kg) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="weight"
                  name="weight"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
                  value={formData.weight}
                  onChange={handleChange}
                  required
                  placeholder="체중을 입력하세요"
                  min="20"
                  max="300"
                  step="0.1"
                />
              </div>

              {/* 체지방률 */}
              <div className="space-y-2">
                <label htmlFor="bodyFat" className="block text-sm font-semibold text-gray-700">
                  체지방률 (%)
                </label>
                <input
                  type="number"
                  id="bodyFat"
                  name="bodyFat"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
                  value={formData.bodyFat}
                  onChange={handleChange}
                  placeholder="체지방률을 입력하세요"
                  min="3"
                  max="50"
                  step="0.1"
                />
              </div>

              {/* 근육량 */}
              <div className="space-y-2">
                <label htmlFor="muscleMass" className="block text-sm font-semibold text-gray-700">
                  근육량 (kg)
                </label>
                <input
                  type="number"
                  id="muscleMass"
                  name="muscleMass"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
                  value={formData.muscleMass}
                  onChange={handleChange}
                  placeholder="근육량을 입력하세요"
                  min="10"
                  max="100"
                  step="0.1"
                />
              </div>

              {/* 활동 수준 */}
              <div className="space-y-2">
                <label htmlFor="activityLevel" className="block text-sm font-semibold text-gray-700">
                  활동 수준 <span className="text-red-500">*</span>
                </label>
                <select
                  id="activityLevel"
                  name="activityLevel"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 bg-white"
                  value={formData.activityLevel}
                  onChange={handleChange}
                  required
                >
                  <option value="">선택해주세요</option>
                  <option value="low">낮음 (거의 운동 안함)</option>
                  <option value="moderate">보통 (주 3-5회 운동)</option>
                  <option value="high">높음 (매일 격렬한 운동)</option>
                </select>
              </div>
            </div>

            {/* 목표 */}
            <div className="space-y-2">
              <label htmlFor="goal" className="block text-sm font-semibold text-gray-700">
                주요 목표 <span className="text-red-500">*</span>
              </label>
              <select
                id="goal"
                name="goal"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200 bg-white"
                value={formData.goal}
                onChange={handleChange}
                required
              >
                <option value="">선택해주세요</option>
                <option value="weightLoss">체중 감량</option>
                <option value="muscleGain">근육 증량</option>
                <option value="maintenance">현상 유지</option>
              </select>
            </div>

            {/* 안내 메시지 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="text-sm text-blue-700">
                  <p className="font-medium mb-1">정보 입력 안내</p>
                  <p>체지방률과 근육량은 인바디 측정값이 있을 때만 입력해주세요. 없다면 비워두셔도 됩니다.</p>
                </div>
              </div>
            </div>

            {/* 제출 버튼 */}
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              정보 입력 완료
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default InbodyFormPage;