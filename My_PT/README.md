# 스마트 푸드 매니저 v12 (4단계 + FatSecret)

AI 기반 식재료 인식 및 영양정보 관리 시스템

## 🚀 주요 기능

### 1. 4단계 추론 시스템
- **1단계**: ml 단위 음료 감지 → 브랜드명 감지 → 브랜드 제품 감지
- **2단계**: 식재료명 직접 매칭 (한국어 식재료 데이터베이스)
- **3단계**: Gemini AI를 활용한 고급 추론
- **4단계**: 고급 fallback 추론 (API 실패 시)

### 2. FatSecret 영양정보 통합
- 자동 영양정보 검색
- 칼로리, 탄수화물, 단백질 정보 제공
- 영양정보 대시보드

### 3. 이미지 분석
- OCR (Optical Character Recognition)
- Object Detection (객체 탐지)
- 드래그 앤 드롭 지원
- 다중 이미지 일괄 처리

### 4. 냉장고 관리
- 식재료 자동 인식
- 수동 식재료 추가
- 수량 관리
- MongoDB 저장/불러오기
- 버전3 데이터 마이그레이션

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/
│   │   ├── FoodDetectionApp.js    # 메인 식재료 감지 앱
│   │   ├── HomePage.js            # 홈 페이지
│   │   ├── CookingMode.js         # 요리 모드
│   │   └── MainPage.js            # HomePage 별칭
│   ├── services/
│   │   ├── apiService.js          # 백엔드 API 통신
│   │   ├── fatSecretService.js    # FatSecret API 서비스
│   │   └── geminiService.js       # Gemini AI API 서비스
│   ├── utils/
│   │   ├── brandDetection.js      # 브랜드 감지 유틸리티
│   │   ├── foodProcessing.js      # 식품 처리 유틸리티
│   │   ├── imageUtils.js          # 이미지 처리 유틸리티
│   │   ├── inferenceEngine.js     # 4단계 추론 엔진
│   │   ├── ingredientClassification.js  # 식재료 분류
│   │   └── legacyDataMigration.js       # 버전3 데이터 마이그레이션
│   ├── App.js                     # 메인 앱 컴포넌트
│   ├── App.css                    # 앱 스타일
│   ├── index.js                   # 진입점
│   └── index.css                  # 전역 스타일
├── public/
├── package.json
├── tailwind.config.js
├── postcss.config.js
└── .env                          # 환경 변수 설정

```

## 🛠️ 설치 방법

### 1. 프로젝트 클론
```bash
git clone [repository-url]
cd frontend
```

### 2. 의존성 설치
```bash
npm install
```

### 3. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 필요한 API 키를 설정합니다.

```bash
cp .env.example .env
```

`.env` 파일 편집:
```
REACT_APP_API_BASE_URL=http://192.168.0.19:8080
REACT_APP_GEMINI_API_KEY=your_actual_gemini_api_key
REACT_APP_GEMINI_API_URL=https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent
```

### 4. 개발 서버 실행
```bash
npm start
```

브라우저에서 `http://localhost:3000` 접속

## 🔧 백엔드 API 요구사항

백엔드 서버는 다음 엔드포인트를 제공해야 합니다:

### 기본 API
- `POST /api/ocr` - OCR 텍스트 추출
- `POST /api/detect` - 객체 탐지
- `POST /api/fridge/save` - 냉장고 데이터 저장
- `GET /api/fridge/load/{userId}` - 냉장고 데이터 불러오기
- `GET /health` - 서버 상태 확인

### FatSecret API
- `POST /api/fatsecret/search` - FatSecret 식품 검색
- `POST /api/dashboard/upload` - 대시보드 업로드
- `GET /api/dashboard/load/{userId}` - 대시보드 데이터 불러오기
- `DELETE /api/dashboard/delete/{entryId}` - 대시보드 항목 삭제

## 🎯 사용 방법

### 1. 식재료 인식
1. 홈페이지에서 "냉장고 스캔" 선택
2. 냉장고 사진 업로드 (드래그 앤 드롭 지원)
3. "전체 분석" 버튼 클릭
4. 자동으로 식재료 인식 및 냉장고에 추가

### 2. 수동 식재료 추가
1. "추가" 버튼 클릭
2. 식재료 이름과 수량 입력
3. "추가하기" 버튼 클릭

### 3. 영양정보 확인
1. FatSecret 검색 활성화
2. 이미지 분석 시 자동으로 영양정보 검색
3. 대시보드 탭에서 영양정보 확인

### 4. 데이터 저장/불러오기
- "저장" 버튼: 현재 냉장고 데이터를 서버에 저장
- "불러오기" 버튼: 저장된 데이터 불러오기
- "V3 서버/로컬" 버튼: 이전 버전 데이터 마이그레이션

## 📱 반응형 디자인
- 모바일, 태블릿, 데스크톱 모든 화면 크기 지원
- Tailwind CSS를 활용한 반응형 레이아웃

## 🔒 보안 고려사항
- API 키는 환경 변수로 관리
- 사용자별 고유 ID로 데이터 분리
- CORS 설정 필요 (백엔드)

## 🐛 문제 해결

### OCR이 작동하지 않는 경우
- 이미지 품질 확인 (선명한 이미지 사용)
- 텍스트가 잘 보이는 각도로 촬영
- 백엔드 OCR API 상태 확인

### FatSecret 검색이 안 되는 경우
- FatSecret 검색 활성화 여부 확인
- 한국어 식품명으로 검색되는지 확인
- 백엔드 FatSecret API 연동 상태 확인

### 데이터 저장이 안 되는 경우
- 백엔드 서버 연결 상태 확인
- MongoDB 연결 상태 확인 (백엔드)
- 네트워크 연결 확인

## 📄 라이센스
MIT License

## 👥 기여
Pull Request와 Issue는 언제든 환영합니다!