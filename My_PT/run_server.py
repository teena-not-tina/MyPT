#!/usr/bin/env python3
"""
MyPT 서버 실행 스크립트
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_requirements():
    """필수 패키지 확인 및 설치"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'torch',
        'torchvision',
        'opencv-python',
        'pillow',
        'numpy',
        'pydantic'
    ]
    
    logger.info("필수 패키지 확인 중...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✓ {package} 설치됨")
        except ImportError:
            logger.warning(f"✗ {package} 미설치 - 설치 중...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def check_models():
    """모델 파일 확인"""
    model_paths = [
        "cv-service/models/best_friged.pt",
        "cv-service/models/best_fri.pt",
        "cv-service/models/best.pt",
        "cv-service/models/yolo11s.pt"
    ]
    
    logger.info("모델 파일 확인 중...")
    
    for path in model_paths:
        if Path(path).exists():
            logger.info(f"✓ 모델 파일 발견: {path}")
            return True
    
    logger.error("✗ 모델 파일을 찾을 수 없습니다!")
    return False

def create_data_directory():
    """데이터 디렉토리 생성"""
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        logger.info("✓ data 디렉토리 생성됨")
    else:
        logger.info("✓ data 디렉토리 존재")

def run_server():
    """서버 실행"""
    logger.info("서버를 시작합니다...")
    logger.info("주소: http://192.168.0.19:8080")
    logger.info("종료하려면 Ctrl+C를 누르세요")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8080',
            '--reload'
        ])
    except KeyboardInterrupt:
        logger.info("\n서버를 종료합니다...")
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {e}")

def main():
    """메인 함수"""
    logger.info("MyPT 서버 시작 준비 중...")
    
    # 1. 필수 패키지 확인
    check_requirements()
    
    # 2. 모델 파일 확인
    if not check_models():
        logger.warning("모델 파일이 없어도 서버는 시작됩니다.")
    
    # 3. 데이터 디렉토리 생성
    create_data_directory()
    
    # 4. 서버 실행
    run_server()

if __name__ == "__main__":
    main()