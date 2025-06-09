// src/stores/authStore.js (예시)
import { create } from 'zustand';

const useAuthStore = create((set) => ({
  isAuthenticated: false, // 초기값
  token: null, // 토큰 저장용 (필요시)
  user: null, // 사용자 정보 저장용 (필요시)

  login: (token = null, user = null) => { // 토큰과 사용자 정보를 받을 수 있도록
    // 실제 백엔드에서 받은 토큰이나 사용자 정보를 로컬 스토리지에 저장하는 로직
    if (token) localStorage.setItem('authToken', token);
    set({ isAuthenticated: true, token, user });
  },
  logout: () => {
    localStorage.removeItem('authToken'); // 로컬 스토리지에서 토큰 제거
    set({ isAuthenticated: false, token: null, user: null });
  },
  checkAuth: () => {
    // 앱 로드 시 로컬 스토리지에서 토큰 확인하여 인증 상태 설정
    const token = localStorage.getItem('authToken');
    if (token) {
      // 토큰 유효성 검사 로직 (선택 사항)
      set({ isAuthenticated: true, token });
    } else {
      set({ isAuthenticated: false, token: null });
    }
  },
}));

export default useAuthStore;