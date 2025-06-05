// src/pages/Onboarding/InbodyFormPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/global.css'; // 공통 스타일 임포트

function InbodyFormPage() {
  const navigate = useNavigate();

  // 사용자 정보 상태 관리
  const [formData, setFormData] = useState({
    gender: '', // 성별 (male, female)
    age: '',    // 나이
    height: '', // 키 (cm)
    weight: '', // 체중 (kg)
    bodyFat: '', // 체지방률 (%) - 인바디 정보
    muscleMass: '', // 근육량 (kg) - 인바디 정보
    activityLevel: '', // 활동 수준 (low, moderate, high)
    goal: '', // 목표 (weightLoss, muscleGain, maintenance)
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

    // TODO: 백엔드에 사용자 정보 및 인바디 데이터 전송 (나중에 구현)
    alert('사용자 정보 입력 완료 (백엔드 연동 전)');

    // 정보 입력 완료 후 대시보드 페이지로 이동 가정
    // 실제 앱에서는 백엔드 저장 성공 후 이동해야 함
    navigate('/dashboard'); // 예시: 대시보드 페이지로 이동
  };

  return (
    <div className="page-content-wrapper auth-page-container"> {/* 기존 인증 페이지 스타일 재활용 */}
      <h2 className="auth-title">사용자 정보 및 인바디 입력</h2>
      <form onSubmit={handleSubmit} className="auth-form"> {/* 기존 폼 스타일 재활용 */}
        {/* 성별 */}
        <div className="form-group">
          <label>성별:</label>
          <div>
            <input
              type="radio"
              id="male"
              name="gender"
              value="male"
              checked={formData.gender === 'male'}
              onChange={handleChange}
              required
            />
            <label htmlFor="male"> 남성</label>
            <input
              type="radio"
              id="female"
              name="gender"
              value="female"
              checked={formData.gender === 'female'}
              onChange={handleChange}
              required
              style={{ marginLeft: '1rem' }}
            />
            <label htmlFor="female"> 여성</label>
          </div>
        </div>

        {/* 나이 */}
        <div className="form-group">
          <label htmlFor="age">나이:</label>
          <input
            type="number"
            id="age"
            name="age"
            className="form-input"
            value={formData.age}
            onChange={handleChange}
            required
            placeholder="나이를 입력하세요"
          />
        </div>

        {/* 키 */}
        <div className="form-group">
          <label htmlFor="height">키 (cm):</label>
          <input
            type="number"
            id="height"
            name="height"
            className="form-input"
            value={formData.height}
            onChange={handleChange}
            required
            placeholder="키를 입력하세요 (cm)"
          />
        </div>

        {/* 체중 */}
        <div className="form-group">
          <label htmlFor="weight">체중 (kg):</label>
          <input
            type="number"
            id="weight"
            name="weight"
            className="form-input"
            value={formData.weight}
            onChange={handleChange}
            required
            placeholder="체중을 입력하세요 (kg)"
          />
        </div>

        {/* 체지방률 (인바디) */}
        <div className="form-group">
          <label htmlFor="bodyFat">체지방률 (%):</label>
          <input
            type="number"
            id="bodyFat"
            name="bodyFat"
            className="form-input"
            value={formData.bodyFat}
            onChange={handleChange}
            placeholder="체지방률을 입력하세요 (%)"
            step="0.1" // 소수점 입력 가능
          />
        </div>

        {/* 근육량 (인바디) */}
        <div className="form-group">
          <label htmlFor="muscleMass">근육량 (kg):</label>
          <input
            type="number"
            id="muscleMass"
            name="muscleMass"
            className="form-input"
            value={formData.muscleMass}
            onChange={handleChange}
            placeholder="근육량을 입력하세요 (kg)"
            step="0.1"
          />
        </div>

        {/* 활동 수준 */}
        <div className="form-group">
          <label htmlFor="activityLevel">활동 수준:</label>
          <select
            id="activityLevel"
            name="activityLevel"
            className="form-input"
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

        {/* 목표 */}
        <div className="form-group">
          <label htmlFor="goal">주요 목표:</label>
          <select
            id="goal"
            name="goal"
            className="form-input"
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

        <button type="submit" className="primary-button auth-button">
          정보 입력 완료
        </button>
      </form>
    </div>
  );
}

export default InbodyFormPage;