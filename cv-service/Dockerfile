# Frontend build stage
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend

# Package files 복사 및 의존성 설치
COPY frontend/package*.json ./
RUN npm ci --only=production

# Frontend 소스 복사 및 빌드
COPY frontend/ ./
RUN npm run build

# Backend stage
FROM python:3.9-slim as backend

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 코드 복사
COPY . .

# 빌드된 프론트엔드 파일 복사
COPY --from=frontend-build /app/frontend/build ./frontend/build

# 포트 노출
EXPOSE 5000

# 애플리케이션 실행
CMD ["python", "run.py"]