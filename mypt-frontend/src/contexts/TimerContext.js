import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const TimerContext = createContext();

export function TimerProvider({ children }) {
  const [profileImage, setProfileImage] = useState(null);
  const [timeLeft, setTimeLeft] = useState(0);

  const clearTimer = async () => {
    try {
      // 서버에 이미지 삭제 요청
      await axios.delete('http://localhost:5000/api/images/cleanup', {
        withCredentials: true
      });

      // 상태 및 로컬 스토리지 초기화
      setProfileImage(null);
      setTimeLeft(0);
      localStorage.removeItem('userProfileImage');
      localStorage.removeItem('timerTimeLeft');
      localStorage.removeItem('timerStartTime');

      const timerId = localStorage.getItem('timerId');
      if (timerId) {
        clearInterval(parseInt(timerId));
        localStorage.removeItem('timerId');
      }

      console.log('타이머 종료 및 이미지 정리 완료');
    } catch (error) {
      console.error('이미지 정리 중 오류:', error);
    }
  };

  const startTimer = (duration) => {
    setTimeLeft(duration);
    localStorage.setItem('timerTimeLeft', duration.toString());
    localStorage.setItem('timerStartTime', Date.now().toString());

    const intervalId = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearTimer();
          return 0;
        }
        localStorage.setItem('timerTimeLeft', (prev - 1).toString());
        return prev - 1;
      });
    }, 1000);

    localStorage.setItem('timerId', intervalId.toString());
    return intervalId;
  };

  return (
    <TimerContext.Provider value={{ profileImage, timeLeft, clearTimer, startTimer }}>
      {children}
    </TimerContext.Provider>
  );
};

export const useTimerContext = () => {
  return useContext(TimerContext);
};