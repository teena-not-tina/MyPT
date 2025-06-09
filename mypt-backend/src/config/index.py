# src/config/index.py (기타 설정 통합)
# 환경 변수, JWT 비밀 키 등 다양한 설정을 통합 관리하는 파일
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# MongoDB 연결 URI
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/test')
