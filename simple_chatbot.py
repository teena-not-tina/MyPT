# simple_chatbot.py - OCR 결과 Gemini 분석 통합 버전 (함수 분리)
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import base64
from typing import Dict, Any, List, Optional
import asyncio
import traceback
from io import BytesIO
import time
import json
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드 (반드시 다른 import보다 먼저!)
load_dotenv()

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Simple Chatbot Webhook with Duplicate Counting")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Food Detection API URL
FOOD_DETECTION_API = "http://localhost:8000"

# 요청 모델
class ImageMessage(BaseModel):
    user_id: str
    image_url: str = None
    image_base64: str = None
    platform: str = "generic"

# 영어-한글 변환 매핑 (상수로 분리)
LABEL_MAPPING = {
    'eggplant': '가지', 'onion': '양파', 'apple': '사과', 'bell_pepper': '피망',
    'pepper': '고추', 'tomato': '토마토', 'potato': '감자', 'carrot': '당근',
    'cabbage': '양배추', 'broccoli': '브로콜리', 'cucumber': '오이', 'lettuce': '상추',
    'spinach': '시금치', 'radish': '무', 'garlic': '마늘', 'ginger': '생강',
    'corn': '옥수수', 'mushroom': '버섯', 'pumpkin': '호박', 'sweet_potato': '고구마',
    'banana': '바나나', 'orange': '오렌지', 'grape': '포도', 'strawberry': '딸기',
    'watermelon': '수박', 'melon': '멜론', 'peach': '복숭아', 'pear': '배',
    'cherry': '체리', 'mango': '망고', 'pineapple': '파인애플', 'milk': '우유',
    'yogurt': '요거트', 'cheese': '치즈', 'egg': '계란', 'bread': '빵',
    'bred': '빵', 'rice': '쌀', 'noodle': '면', 'pasta': '파스타',
    'meat': '고기', 'beef': '소고기', 'pork': '돼지고기', 'chicken': '닭고기',
    'fish': '생선', 'shrimp': '새우', 'avocado': '아보카도', 'can': '캔',
    'blueberries': '블루베리', 'blueberry': '블루베리'
}

def extract_ocr_text(api_result: Dict) -> Optional[str]:
    """API 응답에서 OCR 텍스트 추출"""
    try:
        enhanced_info = api_result.get('enhanced_info', {})
        if not enhanced_info or not isinstance(enhanced_info, dict):
            print("⚠️ enhanced_info가 없거나 dict가 아님")
            return None
            
        brand_info = enhanced_info.get('brand_info')
        if not brand_info:
            print("⚠️ brand_info가 None이거나 비어있음")
            return None
        
        print(f"🔍 brand_info 발견!")
        
        # brand_info가 dict인 경우
        if isinstance(brand_info, dict):
            print(f"   키들: {list(brand_info.keys())}")
            
            # OCR 텍스트가 있는지 확인
            if 'ocr_text' in brand_info and brand_info['ocr_text']:
                ocr_text = brand_info['ocr_text']
                print(f"✅ OCR 텍스트 발견 (ocr_text): {ocr_text[:50]}...")
                return ocr_text
            
            # detected_text 확인
            elif 'detected_text' in brand_info:
                detected_texts = brand_info['detected_text']
                if isinstance(detected_texts, list) and detected_texts:
                    ocr_text = detected_texts[0]  # 첫 번째 텍스트 사용
                    print(f"✅ OCR 텍스트 발견 (detected_text): {len(detected_texts)}개")
                    return ocr_text
                elif isinstance(detected_texts, str) and detected_texts:
                    print(f"✅ OCR 텍스트 발견 (detected_text): {detected_texts[:50]}...")
                    return detected_texts
        
        # brand_info가 string인 경우
        elif isinstance(brand_info, str) and brand_info:
            print(f"✅ OCR 텍스트 발견 (brand_info as string): {brand_info[:50]}...")
            return brand_info
            
    except Exception as ocr_error:
        print(f"⚠️ OCR 결과 추출 중 오류: {ocr_error}")
        traceback.print_exc()
    
    return None

def format_detections_with_duplicates(detections: List[Dict]) -> List[Dict]:
    """탐지 결과 포맷팅 및 중복 집계"""
    # 중복 집계를 위한 딕셔너리
    label_counts = {}
    label_confidences = {}
    
    for det in detections:
        # 한글 이름 우선 사용
        korean_name = det.get('korean_name')
        label = det.get('label') or det.get('class') or det.get('name') or 'Unknown'
        
        # korean_name이 있으면 사용, 없으면 매핑 테이블에서 찾기
        if korean_name and korean_name != label:
            display_label = korean_name
        elif label.lower() in LABEL_MAPPING:
            display_label = LABEL_MAPPING[label.lower()]
        else:
            display_label = label
        
        confidence = det.get('confidence', 0)
        
        # 중복 집계
        if display_label in label_counts:
            label_counts[display_label] += 1
            # 최대 신뢰도 유지
            if confidence > label_confidences[display_label]:
                label_confidences[display_label] = confidence
        else:
            label_counts[display_label] = 1
            label_confidences[display_label] = confidence
    
    # 집계된 결과를 formatted_detections로 변환
    formatted_detections = []
    for label, count in label_counts.items():
        # 개수가 2개 이상이면 라벨에 개수 표시
        if count > 1:
            display_label = f"{label} ({count}개)"
        else:
            display_label = label
        
        formatted_det = {
            'label': display_label,  # 개수가 포함된 라벨
            'confidence': label_confidences[label],
            'count': count,
            'bbox': [],
            'original_label': label  # 원본 라벨 보존
        }
        formatted_detections.append(formatted_det)
    
    # 신뢰도 순으로 정렬
    formatted_detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    # 중복 집계 통계 출력
    duplicate_items = {k: v for k, v in label_counts.items() if v > 1}
    if duplicate_items:
        print(f"\n📦 중복 항목 발견:")
        for label, count in duplicate_items.items():
            print(f"   - {label}: {count}개")
    
    print(f"\n📊 신뢰도 상위 5개 항목:")
    for det in formatted_detections[:5]:
        print(f"   - {det['label']}: {det['confidence']:.1%}")
    
    return formatted_detections

async def call_food_detection_api(image_base64: str) -> Dict:
    """Food Detection API 호출"""
    print(f"📡 API 호출: {FOOD_DETECTION_API}/api/detect")
    
    # Base64를 바이너리로 디코딩
    image_bytes = base64.b64decode(image_base64)
    
    # 가짜 파일명 생성
    filename = f"chatbot_image_{int(time.time())}.jpg"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # multipart/form-data로 전송
        files = {
            'file': (filename, BytesIO(image_bytes), 'image/jpeg')
        }
        data = {
            'confidence': '0.5',
            'use_ensemble': 'true',
            'use_enhanced': 'true'
        }
        
        response = await client.post(
            f"{FOOD_DETECTION_API}/api/detect",
            files=files,
            data=data
        )
        
        print(f"📨 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            api_result = response.json()
            print(f"🔍 API 응답 최상위 키: {list(api_result.keys())}")
            print(f"✅ 분석 성공: {len(api_result.get('detections', []))} 개 음식 감지")
            return api_result
        else:
            error_detail = f"API 응답 오류: {response.status_code} - {response.text}"
            print(f"❌ {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)

def analyze_with_gemini(ocr_text: str, detections: List[Dict]) -> Optional[str]:
    """Gemini 분석 수행"""
    if not ocr_text:
        return None
        
    print(f"\n🧠 Gemini 분석 시작...")
    try:
        # Gemini 모듈 import
        from modules.gemini import analyze_text_with_gemini, check_if_food_product
        
        # 환경 변수 확인
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            print("⚠️ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다")
            return None
        
        # 먼저 식품인지 확인
        is_food = check_if_food_product(ocr_text)
        print(f"📋 식품 여부: {'식품' if is_food else '비식품'}")
        
        if is_food:
            # 식품이면 상세 분석
            gemini_result = analyze_text_with_gemini(ocr_text, detections)
            if gemini_result:
                print(f"✅ Gemini 분석 성공: {gemini_result}")
                return gemini_result
            else:
                print("⚠️ Gemini 분석 결과 없음")
        else:
            print("ℹ️ 식품이 아니므로 Gemini 분석 생략")
            # API 키가 없어서 실패한 경우, 브랜드 패턴으로 다시 시도
            if not os.environ.get("GEMINI_API_KEY"):
                print("🔄 브랜드 패턴 매칭으로 재시도...")
                try:
                    from modules.gemini import detect_brand_and_product
                    brand, product = detect_brand_and_product(ocr_text)
                    if brand and product:
                        gemini_result = f"{brand} {product}"
                        print(f"✅ 브랜드 패턴 매칭 성공: {gemini_result}")
                        return gemini_result
                    elif brand:
                        print(f"✅ 브랜드만 인식: {brand}")
                        return brand
                except Exception as pattern_error:
                    print(f"❌ 브랜드 패턴 매칭 실패: {pattern_error}")
                    
    except ImportError:
        print("❌ Gemini 모듈을 찾을 수 없습니다")
    except Exception as gemini_error:
        print(f"❌ Gemini 분석 중 오류: {gemini_error}")
        traceback.print_exc()
    
    return None

def try_brand_pattern_matching(ocr_text: str) -> Optional[str]:
    """브랜드 패턴 매칭 시도 (Gemini 분석 실패 시 폴백)"""
    if not ocr_text:
        return None
        
    try:
        from modules.gemini import detect_brand_and_product
        brand, product = detect_brand_and_product(ocr_text)
        
        if brand and product:
            result = f"{brand} {product}"
            print(f"🔍 브랜드 패턴으로 인식: {result}")
            return result
        elif brand:
            print(f"🔍 브랜드만 인식: {brand}")
            return brand
            
    except Exception:
        pass
    
    return None

# Food Detection API 호출 - 분리된 버전
async def analyze_image(image_base64: str) -> Dict:
    """이미지 분석 - 메인 오케스트레이션 함수"""
    print(f"🔍 이미지 분석 시작... (크기: {len(image_base64)} bytes)")
    
    try:
        # 1. Food Detection API 호출
        api_result = await call_food_detection_api(image_base64)
        
        # 2. OCR 결과 추출
        ocr_text = extract_ocr_text(api_result)
        
        # 3. detections 포맷팅 및 중복 집계
        detections = api_result.get('detections', [])
        formatted_detections = format_detections_with_duplicates(detections)
        
        # 4. Gemini 분석 수행 (OCR 텍스트가 있을 경우)
        gemini_result = analyze_with_gemini(ocr_text, detections)
        
        # 5. Gemini 분석 실패 시 브랜드 패턴 매칭 시도
        if not gemini_result and ocr_text:
            gemini_result = try_brand_pattern_matching(ocr_text)
        
        # 6. 결과 요약 출력
        print(f"\n📊 분석 결과 요약:")
        print(f"   - 원본 탐지 객체: {len(detections)}개")
        print(f"   - 중복 집계 후: {len(formatted_detections)}개")
        if ocr_text:
            print(f"   - OCR 텍스트: 감지됨 (내부 처리용)")
        if gemini_result:
            print(f"   - Gemini 분석: {gemini_result}")
            print(f"   - 최종 표시: 제품명 + 모든 탐지 결과")
        else:
            print(f"   - Gemini 분석: 없음")
            print(f"   - 최종 표시: 모든 탐지 결과")
        
        # 7. 최종 결과 구성
        result = {
            'detections': formatted_detections,
            'ocr_text': ocr_text,  # 원본 OCR 텍스트 (내부 처리용)
            'gemini_analysis': gemini_result  # Gemini 분석 결과
        }
        
        return result
        
    except Exception as e:
        error_msg = f"예상치 못한 오류: {type(e).__name__} - {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

# 이미지 URL에서 base64로 변환
async def download_image(image_url: str) -> str:
    """이미지 다운로드 및 base64 변환"""
    print(f"🌐 이미지 다운로드: {image_url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        return base64.b64encode(response.content).decode()

@app.post("/webhook/simple")
async def simple_webhook(message: ImageMessage):
    """범용 웹훅 - 즉시 처리"""
    print(f"\n{'='*50}")
    print(f"📥 새 요청: user_id={message.user_id}, platform={message.platform}")
    
    try:
        # 이미지 준비
        if message.image_url:
            image_base64 = await download_image(message.image_url)
        else:
            image_base64 = message.image_base64
            print(f"📷 Base64 이미지 수신 (크기: {len(image_base64)} bytes)")
        
        # 분석 실행
        result = await analyze_image(image_base64)
        
        # 기존 형식의 응답 (프론트엔드 호환성 유지)
        response = {
            "status": "success",
            "user_id": message.user_id,
            "detections": result.get("detections", []),
            "ocr_results": []  # OCR 결과를 빈 배열로 설정하여 표시하지 않음
        }
        
        # 표시 정책:
        # 1. Gemini/브랜드 인식 성공 → 제품명을 맨 위에 추가하고 모든 결과 표시
        # 2. 인식 실패 → 일반 객체 탐지 결과만 표시
        
        # Gemini 분석 결과가 있으면 추가
        if result.get("gemini_analysis"):
            response["food_name"] = result["gemini_analysis"]
            response["recognized_product"] = result["gemini_analysis"]
            
            # Gemini 분석 결과를 detections 맨 앞에 추가 (기존 결과 유지)
            gemini_detection = {
                "label": result["gemini_analysis"],  # 단순하게 제품명만
                "confidence": 1.0,  # 100% 신뢰도
                "bbox": [],
                "class": result["gemini_analysis"],  # class도 동일하게
                "korean_name": result["gemini_analysis"],
                "count": 1,  # 개수 정보 추가
                "original_label": result["gemini_analysis"]
            }
            # detections 맨 앞에 삽입 (기존 결과는 유지)
            response["detections"].insert(0, gemini_detection)
            print(f"🎯 Gemini 인식 결과를 맨 앞에 추가: {result['gemini_analysis']}")
            print(f"   (총 {len(response['detections'])}개 항목 표시)")
        
        # OCR 텍스트가 있지만 Gemini 분석이 없는 경우, 브랜드 패턴 매칭 시도
        elif result.get("ocr_text") and not result.get("gemini_analysis"):
            brand_result = try_brand_pattern_matching(result["ocr_text"])
            if brand_result:
                response["food_name"] = brand_result
                response["recognized_product"] = brand_result
                
                # 브랜드 패턴 매칭 결과를 detections 맨 앞에 추가
                brand_detection = {
                    "label": brand_result if not brand_result.endswith("제품") else brand_result,
                    "confidence": 0.9 if " " in brand_result else 0.8,  # 제품명 포함 시 높은 신뢰도
                    "bbox": [],
                    "class": brand_result,
                    "korean_name": brand_result,
                    "count": 1,
                    "original_label": brand_result
                }
                response["detections"].insert(0, brand_detection)
                print(f"🔍 브랜드 패턴으로 인식: {brand_result}")
                print(f"   (총 {len(response['detections'])}개 항목 표시)")
        
        print(f"✅ 응답 성공: {len(response['detections'])} 항목 표시")
        if "food_name" in response:
            print(f"🍽️ 인식된 제품: {response['food_name']}")
            print(f"   (제품명 + 일반 탐지 결과 모두 표시)")
        print(f"{'='*50}\n")
        
        return response
    
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ 예상치 못한 오류: {error_msg}")
        print(traceback.format_exc())
        print(f"{'='*50}\n")
        
        return {
            "status": "error",
            "message": error_msg,
            "detections": [],
            "ocr_results": []  # 오류 시에도 빈 배열 반환
        }

@app.get("/")
async def root():
    """헬스체크"""
    return {
        "status": "running",
        "version": "2.3",
        "features": [
            "Food Detection",
            "OCR Text Recognition", 
            "Gemini AI Analysis",
            "All Items Display with Duplicate Counting",
            "Smart Grouping (중복 항목 개수 표시)"
        ],
        "endpoints": [
            "/webhook/simple - 이미지 분석 및 텍스트 인식",
            "/test - 연결 테스트"
        ]
    }

@app.get("/test")
async def test_connection():
    """Food Detection API 연결 테스트"""
    print("🔧 연결 테스트 시작...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FOOD_DETECTION_API}/")
            api_status = response.status_code == 200
            print(f"✅ Food Detection API 상태: {'연결됨' if api_status else '연결 실패'}")
            
            # 모델 정보도 확인
            models_response = await client.get(f"{FOOD_DETECTION_API}/api/models/info")
            models_info = models_response.json() if models_response.status_code == 200 else {}
            
            # Gemini 모듈 확인
            gemini_available = False
            try:
                from modules.gemini import test_gemini_setup
                gemini_available = test_gemini_setup()
            except:
                pass
            
            return {
                "chatbot_status": "ok",
                "food_detection_api": api_status,
                "api_response": response.status_code,
                "models_loaded": models_info.get("loaded_count", 0),
                "ensemble_ready": models_info.get("ensemble_ready", False),
                "gemini_available": gemini_available
            }
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {type(e).__name__}")
        return {
            "chatbot_status": "ok",
            "food_detection_api": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🤖 스마트 푸드 챗봇 Webhook 서버 v2.3")
    print(f"📡 Food Detection API: {FOOD_DETECTION_API}")
    print("=" * 50)
    print("✨ 주요 기능:")
    print("- 이미지에서 음식 객체 탐지")
    print("- OCR로 텍스트 인식")
    print("- Gemini AI로 제품명 분석")
    print("- 제품명 인식 시 맨 위에 표시 + 모든 탐지 결과 함께 표시")
    print("- 중복된 항목은 개수로 표시 (예: 사과 (3개))")
    print("- 식품/비식품 자동 구분")
    print("=" * 50)
    print("엔드포인트:")
    print("- http://localhost:8001/webhook/simple")
    print("- http://localhost:8001/test (연결 테스트)")
    print("=" * 50)
    
    # 시작 시 연결 테스트
    import requests
    try:
        test_response = requests.get(f"{FOOD_DETECTION_API}/", timeout=2)
        if test_response.status_code == 200:
            print("✅ Food Detection API 연결 확인됨!")
        else:
            print("⚠️  Food Detection API 응답 이상")
    except:
        print("❌ Food Detection API에 연결할 수 없습니다!")
        print("   main.py가 실행 중인지 확인하세요.")
    
    # Gemini 설정 확인
    try:
        from modules.gemini import test_gemini_setup
        if test_gemini_setup():
            print("✅ Gemini API 설정 확인됨!")
        else:
            print("⚠️  Gemini API 설정 필요")
    except:
        print("❌ Gemini 모듈을 찾을 수 없습니다!")
    
    print("=" * 50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
