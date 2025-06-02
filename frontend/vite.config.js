
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': 'http://localhost:5000', // 백엔드 Flask 서버로 '/chat' 요청을 프록시
    },
  },
  build: {
    outDir: 'dist', // 빌드 결과물이 저장될 폴더 (백엔드에서 서빙할 때 사용)
  },
});
