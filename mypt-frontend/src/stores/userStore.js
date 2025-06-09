// src/stores/authStore.js
import { create } from 'zustand';

const useAuthStore = create((set) => ({
  // ... 스토어 내용
}));

export default useAuthStore; // 이렇게 export 되어야 합니다!