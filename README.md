# B-FIT 프로젝트

## 프로젝트 구조

```
├── docker-compose.yml
├── .env.example
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── index.js
│       ├── components/
│       │   ├── Auth/
│       │   ├── Chatbot/
│       │   ├── MainPage/
│       │   ├── Exercise/
│       │   └── Diet/
│       └── services/
├── cv-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── modules/
│       ├── yolo_detector.py
│       ├── pose_analyzer.py
│       └── ocr_processor.py
├── rag-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── modules/
│       ├── pdf_processor.py
│       ├── routine_generator.py
│       └── vector_store.py
├── stable-diffusion/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── modules/
│       └── character_generator.py
└── db/
    └── init-mongo.js
```

## 개요

B-FIT은 AI 기반 개인 운동 트레이너 서비스입니다. 컴퓨터 비전을 활용한 자세 분석, RAG(Retrieval Augmented Generation)를 통한 맞춤형 운동 루틴 생성, 그리고 Stable Diffusion을 이용한 캐릭터 생성 등의 기능을 제공합니다.

## 서비스 구성

### Frontend
React 기반의 사용자 인터페이스입니다. 사용자 인증, 메인 페이지, 운동 추적, 식단 기록 및 챗봇 기능을 포함합니다.

### CV-Service
컴퓨터 비전 관련 기능을 제공하는 서비스입니다:
- YOLO 기반 객체 탐지
- 포즈 추정 및 운동 자세 분석
- OCR 처리

### RAG-Service
맞춤형 정보 검색 및 생성 서비스:
- PDF 문서 처리 및 정보 추출
- 개인화된 운동 루틴 생성
- 벡터 저장소를 활용한 효율적인 정보 검색

### Stable-Diffusion
사용자 맞춤형 마스코트 캐릭터 생성 서비스

### DB
MongoDB 데이터베이스 설정

## 설치 및 실행 방법

1. 저장소를 클론합니다.
   ```
   git clone https://github.com/teena-not-tina/MyPT.git
   cd MyPT
   ```

2. 환경 변수 설정
   ```
   cp .env.example .env
   # .env 파일을 적절히 수정하세요
   ```

3. Docker Compose를 사용하여 서비스 실행
   ```
   docker-compose up -d
   ```

4. 브라우저에서 프론트엔드 접속
   ```
   http://localhost:3000
   ```

## API 엔드포인트

### Character API
- `GET /api/character/current`: 현재 사용자의 마스코트 이미지 URL 반환

### Exercise API
- `POST /api/exercise/analyze`: 운동 자세 분석

### Diet API
- `POST /api/diet/record`: 식단 기록 저장

## 개발 가이드라인

각 서비스는 독립적인 Docker 컨테이너로 실행됩니다. 개발 시에는 해당 서비스의 Dockerfile과 관련 파일만 수정하면 됩니다.