// src/pages/Onboarding/InbodyFormPage.js (프론트엔드 파일)
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../../styles/global.css'; // 공통 스타일 임포트

function InbodyFormPage() {
  const navigate = useNavigate();

  // 인바디 정보를 위한 상태 변수들 정의
  const [height, setHeight] = useState(''); // 키 (cm)
  const [weight, setWeight] = useState(''); // 체중 (kg)
  const [bodyFat, setBodyFat] = useState(''); // 체지방률 (%)
  const [muscleMass, setMuscleMass] = useState(''); // 골격근량 (kg)

  const handleSubmit = async (e) => {
    e.preventDefault(); // 폼 제출 시 페이지 새로고침 방지

    // 입력된 인바디 정보를 객체로 만듭니다.
    const inbodyData = {
      height: parseFloat(height), // 숫자로 변환
      weight: parseFloat(weight),
      bodyFat: parseFloat(bodyFat),
      muscleMass: parseFloat(muscleMass),
    };

    console.log('인바디 정보 제출 시도:', inbodyData);

    try {
      // 백엔드 API로 인바디 정보 전송
      // TODO: 백엔드의 인바디 API 엔드포인트는 아래에서 정의할 예정입니다.
      // 일단 'http://localhost:5000/api/inbody/submit'으로 가정합니다.
      const response = await axios.post('http://localhost:5000/api/inbody/submit', inbodyData);

      console.log('인바디 정보 저장 성공:', response.data);
      alert('인바디 정보가 성공적으로 저장되었습니다!');
      
      // 인바디 정보 저장 성공 후 다음 페이지 (예: 대시보드)로 이동
      navigate('/dashboard'); // 대시보드 페이지로 이동

    } catch (error) {
      console.error('인바디 정보 저장 실패:', error.response?.data?.message || error.message);
      alert(error.response?.data?.message || '인바디 정보 저장에 실패했습니다.');
    }
  };

  return (
    <div className="page-content-wrapper auth-page-container">
      <h2 className="auth-title">인바디 정보 입력</h2>
      <form onSubmit={handleSubmit} className="auth-form">
        {/* 키 입력 필드 */}
        <div className="form-group">
          <label htmlFor="height">키 (cm):</label>
          <input
            type="number" // 숫자만 입력받도록
            id="height"
            className="form-input"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            required
            placeholder="예: 175.5"
            step="0.1" // 소수점 첫째 자리까지 허용
          />
        </div>

        {/* 체중 입력 필드 */}
        <div className="form-group">
          <label htmlFor="weight">체중 (kg):</label>
          <input
            type="number"
            id="weight"
            className="form-input"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            required
            placeholder="예: 68.2"
            step="0.1"
          />
        </div>

        {/* 체지방률 입력 필드 */}
        <div className="form-group">
          <label htmlFor="bodyFat">체지방률 (%):</label>
          <input
            type="number"
            id="bodyFat"
            className="form-input"
            value={bodyFat}
            onChange={(e) => setBodyFat(e.target.value)}
            required
            placeholder="예: 15.0"
            step="0.1"
          />
        </div>

        {/* 골격근량 입력 필드 */}
        <div className="form-group">
          <label htmlFor="muscleMass">골격근량 (kg):</label>
          <input
            type="number"
            id="muscleMass"
            className="form-input"
            value={muscleMass}
            onChange={(e) => setMuscleMass(e.target.value)}
            required
            placeholder="예: 30.5"
            step="0.1"
          />
        </div>

        <button type="submit" className="primary-button auth-button">
          인바디 정보 제출
        </button>
      </form>
    </div>
  );
}

export default InbodyFormPage;