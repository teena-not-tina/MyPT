// API 기본 설정
const API_BASE_URL = 'http://localhost:8080';

// API 서비스
const apiService = {
    // 객체 탐지 (Detection)
    async performDetection(file, confidence = 0.8) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('confidence', confidence);
        const response = await fetch(`${API_BASE_URL}/api/detect`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(`Detection API 오류: ${response.status}`);
        return await response.json();
    },

    // OCR 수행
    async performOCR(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/ocr`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(`OCR API 오류: ${response.status}`);
        return await response.json();
    },

    // 파일 업로드 (사용하지 않으면 생략 가능)
    async uploadFile(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload API 오류: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('❌ Upload 실패:', error);
            throw error;
        }
    },

    // 헬스체크
    async checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/`);
            return response.ok;
        } catch (error) {
            console.error('❌ 서버 연결 실패:', error);
            return false;
        }
    },

    // 냉장고 데이터 저장
    async saveFridgeData(data) {
        const response = await fetch(`${API_BASE_URL}/api/fridge/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('냉장고 데이터 저장 실패');
        return await response.json();
    },

    // 냉장고 데이터 불러오기
    async loadFridgeData(userId) {
        const response = await fetch(`${API_BASE_URL}/api/fridge/load?userId=${encodeURIComponent(userId)}`);
        if (!response.ok) throw new Error('냉장고 데이터 불러오기 실패');
        return await response.json();
    }
};

export default apiService; // ES6 모듈
// 또는
//window.apiService = apiService; // 전역 객체로 노출