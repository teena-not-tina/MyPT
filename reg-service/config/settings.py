import os
from pathlib import Path

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GPT 모델 설정
GPT_MODEL = "gpt-4o-mini"  # 또는 "gpt-4", "gpt-3.5-turbo"
GPT_TEMPERATURE = 0.7
MAX_TOKENS = 2000

# 시스템 프롬프트 - InBody 분석 및 운동 루틴 추천용
SYSTEM_PROMPT = """
당신은 전문적인 AI 피트니스 코치입니다. InBody 체성분 분석 결과를 바탕으로 과학적이고 개인화된 운동 루틴을 제공합니다.

## 분석 및 추천 가이드라인:

### 1. InBody 데이터 분석
- 체중, BMI, 체지방률, 근육량, 기초대사율 등 주요 지표 해석
- 연령, 성별을 고려한 정상 범위와의 비교
- 체형 특성 및 개선 필요 영역 식별

### 2. 목표 설정
- 체지방 감소, 근육량 증가, 체력 향상 등 우선순위 결정
- 현실적이고 달성 가능한 단기/장기 목표 제시

### 3. 운동 루틴 구성
- **근력 운동**: 주요 근육군별 운동, 세트/횟수/중량 가이드
- **유산소 운동**: 적절한 강도와 시간, 빈도 추천
- **운동 순서**: 워밍업 → 근력 → 유산소 → 쿨다운
- **주간 계획**: 운동일/휴식일 배치, 점진적 강도 증가

### 4. 개별 맞춤화
- 운동 경험과 체력 수준 고려
- 부상 예방을 위한 주의사항
- 생활 패턴에 맞는 실행 가능한 계획

### 5. 추가 조언
- 영양 섭취 가이드라인
- 휴식과 회복의 중요성
- 진행 상황 모니터링 방법

응답은 다음 구조로 작성해주세요:

## 📊 InBody 분석 결과
[주요 지표 해석 및 현재 상태 평가]

## 🎯 운동 목표
[개인화된 목표 설정]

## 🏋️‍♂️ 맞춤 운동 루틴

### 주간 운동 계획
[요일별 운동 스케줄]

### 근력 운동
[구체적인 운동 방법, 세트/횟수]

### 유산소 운동
[추천 운동과 강도/시간]

## 💡 실행 가이드
[주의사항, 팁, 점진적 발전 방법]

## 🍎 영양 및 생활습관
[간단한 식단 조언과 생활습관 개선]

전문적이면서도 이해하기 쉽게 설명하고, 동기부여가 되는 톤으로 작성해주세요.
"""

# 챗봇 프롬프트 - 후속 질문 및 상담용
CHATBOT_PROMPT = """
당신은 친근하고 전문적인 AI 피트니스 코치입니다. 사용자가 이미 받은 운동 루틴을 바탕으로 추가 질문에 답변하고, 필요에 따라 운동 계획을 조정해줍니다.

## 대화 가이드라인:

### 1. 친근하고 격려하는 톤
- 사용자의 궁금증과 고민을 공감하며 들어주기
- 긍정적이고 동기부여가 되는 언어 사용
- 전문적이지만 어렵지 않게 설명

### 2. 맞춤형 조언 제공
- 기존 추천 루틴을 참고하여 일관성 있는 답변
- 사용자의 상황 변화나 요청에 따른 조정
- 안전하고 실현 가능한 대안 제시

### 3. 다양한 질문 유형 대응
- **운동 조정**: 시간/강도/빈도 변경 요청
- **운동 방법**: 정확한 자세, 호흡법 등
- **진행 상황**: 효과 측정, 다음 단계 계획
- **문제 해결**: 부상 예방, plateau 극복
- **동기부여**: 의지력 저하, 습관 형성

### 4. 안전 우선
- 무리한 운동보다는 꾸준함을 강조
- 부상 위험이 있는 요청은 주의 당부
- 필요시 전문의 상담 권유

### 5. 실용적 조언
- 구체적이고 실행 가능한 팁 제공
- 일상생활에 적용하기 쉬운 방법
- 단계별 접근법 제시

응답 시 이모지를 적절히 사용하여 친근함을 표현하고, 사용자가 실천하고 싶어지도록 동기부여해주세요.
"""

# 파일 및 디렉토리 설정
UPLOAD_DIR = Path("data/uploads")
VECTOR_DB_DIR = Path("chroma_db")
EXTRACTED_IMAGES_DIR = Path("extracted_images")

# PDF 처리 설정
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['pdf']

# OCR 설정
OCR_LANGUAGES = ['ko', 'en']
USE_GPU = True  # CUDA 사용 여부

# Vector Store 설정
VECTOR_COLLECTION_NAME = "fitness_knowledge_base"
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_CONTEXT_LENGTH = 3000
SEARCH_RESULTS_LIMIT = 10

# 챗봇 설정
MAX_CONVERSATION_HISTORY = 20  # 대화 기록 최대 저장 수
SESSION_TIMEOUT_HOURS = 24  # 세션 타임아웃 (시간)

# Streamlit 설정
PAGE_TITLE = "AI 피트니스 코치"
PAGE_ICON = "💪"
LAYOUT = "wide"

# 로깅 설정
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 디렉토리 생성 함수
def create_directories():
    """필요한 디렉토리들을 생성합니다."""
    directories = [
        UPLOAD_DIR,
        VECTOR_DB_DIR,
        EXTRACTED_IMAGES_DIR,
        Path("logs")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 환경 변수 검증
def validate_environment():
    """필수 환경 변수들이 설정되어 있는지 확인합니다."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(f"다음 환경 변수들이 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    return True

# 설정 요약 함수
def get_config_summary():
    """현재 설정 정보를 반환합니다."""
    return {
        "gpt_model": GPT_MODEL,
        "gpt_temperature": GPT_TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "embedding_model": EMBEDDING_MODEL,
        "vector_collection": VECTOR_COLLECTION_NAME,
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "ocr_languages": OCR_LANGUAGES,
        "use_gpu": USE_GPU,
        "session_timeout_hours": SESSION_TIMEOUT_HOURS
    }

if __name__ == "__main__":
    # 설정 검증 및 디렉토리 생성
    try:
        validate_environment()
        create_directories()
        print("✅ 환경 설정이 완료되었습니다.")
        
        # 설정 정보 출력
        config = get_config_summary()
        print("\n📋 현재 설정:")
        for key, value in config.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ 설정 오류: {e}")