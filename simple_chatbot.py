# simple_chatbot.py - OCR 결과 Gemini 분석 통합 버전
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

app = FastAPI(title="Simple Chatbot Webhook with Smart Display")

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

# Food Detection API 호출 - multipart/form-data 방식
async def analyze_image(image_base64: str) -> Dict:
    """이미지 분석 - 기존 /api/detect 엔드포인트 사용"""
    print(f"🔍 이미지 분석 시작... (크기: {len(image_base64)} bytes)")
    
    try:
        # Base64를 바이너리로 디코딩
        image_bytes = base64.b64decode(image_base64)
        
        # 가짜 파일명 생성
        filename = f"chatbot_image_{int(time.time())}.jpg"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"📡 API 호출: {FOOD_DETECTION_API}/api/detect")
            
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
                
                # 응답의 최상위 키들 확인
                print(f"🔍 API 응답 최상위 키: {list(api_result.keys())}")
                
                print(f"✅ 분석 성공: {len(api_result.get('detections', []))} 개 음식 감지")
                
                # OCR 결과 추출 - 내부 처리용
                ocr_text = None
                
                # 경로 1: enhanced_info.brand_info에서 OCR 텍스트 찾기
                try:
                    enhanced_info = api_result.get('enhanced_info', {})
                    if enhanced_info and isinstance(enhanced_info, dict):
                        brand_info = enhanced_info.get('brand_info')
                        if brand_info:
                            print(f"🔍 brand_info 발견!")
                            
                            # brand_info가 dict인 경우
                            if isinstance(brand_info, dict):
                                # 모든 키 출력
                                print(f"   키들: {list(brand_info.keys())}")
                                
                                # OCR 텍스트가 있는지 확인
                                if 'ocr_text' in brand_info and brand_info['ocr_text']:
                                    ocr_text = brand_info['ocr_text']
                                    print(f"✅ OCR 텍스트 발견 (ocr_text): {ocr_text[:50]}...")
                                
                                # detected_text 확인
                                elif 'detected_text' in brand_info:
                                    detected_texts = brand_info['detected_text']
                                    if isinstance(detected_texts, list) and detected_texts:
                                        ocr_text = detected_texts[0]  # 첫 번째 텍스트 사용
                                        print(f"✅ OCR 텍스트 발견 (detected_text): {len(detected_texts)}개")
                                    elif isinstance(detected_texts, str) and detected_texts:
                                        ocr_text = detected_texts
                                        print(f"✅ OCR 텍스트 발견 (detected_text): {detected_texts[:50]}...")
                            
                            # brand_info가 string인 경우
                            elif isinstance(brand_info, str) and brand_info:
                                ocr_text = brand_info
                                print(f"✅ OCR 텍스트 발견 (brand_info as string): {brand_info[:50]}...")
                        else:
                            print("⚠️ brand_info가 None이거나 비어있음")
                    else:
                        print("⚠️ enhanced_info가 없거나 dict가 아님")
                                
                except Exception as ocr_error:
                    print(f"⚠️ OCR 결과 추출 중 오류: {ocr_error}")
                    traceback.print_exc()
                
                # detections 포맷팅
                detections = api_result.get('detections', [])
                formatted_detections = []
                
                # 영어-한글 변환 매핑
                label_mapping = {
                    'eggplant': '가지',
                    'onion': '양파', 
                    'apple': '사과',
                    'bell_pepper': '피망',
                    'pepper': '고추',
                    'tomato': '토마토',
                    'potato': '감자',
                    'carrot': '당근',
                    'cabbage': '양배추',
                    'broccoli': '브로콜리',
                    'cucumber': '오이',
                    'lettuce': '상추',
                    'spinach': '시금치',
                    'radish': '무',
                    'garlic': '마늘',
                    'ginger': '생강',
                    'corn': '옥수수',
                    'mushroom': '버섯',
                    'pumpkin': '호박',
                    'sweet_potato': '고구마',
                    'banana': '바나나',
                    'orange': '오렌지',
                    'grape': '포도',
                    'strawberry': '딸기',
                    'watermelon': '수박',
                    'melon': '멜론',
                    'peach': '복숭아',
                    'pear': '배',
                    'cherry': '체리',
                    'mango': '망고',
                    'pineapple': '파인애플',
                    'milk': '우유',
                    'yogurt': '요거트',
                    'cheese': '치즈',
                    'egg': '계란',
                    'bread': '빵',
                    'rice': '쌀',
                    'noodle': '면',
                    'pasta': '파스타',
                    'meat': '고기',
                    'beef': '소고기',
                    'pork': '돼지고기',
                    'chicken': '닭고기',
                    'fish': '생선',
                    'shrimp': '새우'
                }
                
                for det in detections:
                    # 한글 이름 우선 사용
                    korean_name = det.get('korean_name')
                    label = det.get('label') or det.get('class') or det.get('name') or 'Unknown'
                    
                    # korean_name이 있으면 사용, 없으면 매핑 테이블에서 찾기
                    if korean_name and korean_name != label:
                        display_label = korean_name
                    elif label.lower() in label_mapping:
                        display_label = label_mapping[label.lower()]
                    else:
                        display_label = label
                    
                    confidence = det.get('confidence', 0)
                    
                    formatted_detections.append({
                        'label': display_label,  # 한글 라벨 사용
                        'confidence': confidence,
                        'bbox': det.get('bbox', []),
                        'original_label': label  # 원본 영어 라벨 보존
                    })
                
                # Gemini 분석 수행 (OCR 텍스트가 있을 경우)
                gemini_result = None
                if ocr_text:
                    print(f"\n🧠 Gemini 분석 시작...")
                    try:
                        # Gemini 모듈 import
                        from modules.gemini import analyze_text_with_gemini, check_if_food_product
                        
                        # 환경 변수 확인
                        gemini_key = os.environ.get("GEMINI_API_KEY")
                        if not gemini_key:
                            print("⚠️ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다")
                            print("   현재 환경 변수들:")
                            for key in os.environ.keys():
                                if 'GEMINI' in key or 'API' in key:
                                    print(f"   - {key}: {'설정됨' if os.environ.get(key) else '없음'}")
                        
                        # 먼저 식품인지 확인
                        is_food = check_if_food_product(ocr_text)
                        print(f"📋 식품 여부: {'식품' if is_food else '비식품'}")
                        
                        if is_food:
                            # 식품이면 상세 분석
                            gemini_result = analyze_text_with_gemini(ocr_text, detections)
                            if gemini_result:
                                print(f"✅ Gemini 분석 성공: {gemini_result}")
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
                                    elif brand:
                                        gemini_result = brand
                                        print(f"✅ 브랜드만 인식: {gemini_result}")
                                except Exception as pattern_error:
                                    print(f"❌ 브랜드 패턴 매칭 실패: {pattern_error}")
                            
                    except ImportError:
                        print("❌ Gemini 모듈을 찾을 수 없습니다")
                    except Exception as gemini_error:
                        print(f"❌ Gemini 분석 중 오류: {gemini_error}")
                        traceback.print_exc()
                
                # 결과 요약 출력
                print(f"\n📊 분석 결과 요약:")
                print(f"   - 탐지된 객체: {len(formatted_detections)}개")
                if ocr_text:
                    print(f"   - OCR 텍스트: 감지됨 (내부 처리용)")
                if gemini_result:
                    print(f"   - Gemini 분석: {gemini_result}")
                    print(f"   - 최종 표시: Gemini 결과만 표시 예정")
                else:
                    print(f"   - Gemini 분석: 없음")
                    print(f"   - 최종 표시: 모든 탐지 결과 표시 예정")
                
                # 최종 결과 구성
                result = {
                    'detections': formatted_detections,
                    'ocr_text': ocr_text,  # 원본 OCR 텍스트 (내부 처리용)
                    'gemini_analysis': gemini_result  # Gemini 분석 결과
                }
                
                return result
                
            else:
                error_detail = f"API 응답 오류: {response.status_code} - {response.text}"
                print(f"❌ {error_detail}")
                raise HTTPException(status_code=500, detail=error_detail)
                
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
        # 1. Gemini/브랜드 인식 성공 → 해당 제품명만 표시
        # 2. 인식 실패 → 일반 객체 탐지 결과 표시
        
        # Gemini 분석 결과가 있으면 추가
        if result.get("gemini_analysis"):
            response["food_name"] = result["gemini_analysis"]
            response["recognized_product"] = result["gemini_analysis"]
            
            # Gemini 분석 결과만을 detections로 설정 (다른 detection 결과 제거)
            gemini_detection = {
                "label": result["gemini_analysis"],  # 단순하게 제품명만
                "confidence": 1.0,  # 100% 신뢰도
                "bbox": [],
                "class": result["gemini_analysis"],  # class도 동일하게
                "korean_name": result["gemini_analysis"]
            }
            # detections를 Gemini 결과만으로 교체
            response["detections"] = [gemini_detection]
            print(f"🎯 Gemini 인식 결과만 표시: {result['gemini_analysis']}")
            print(f"   (기존 {len(result.get('detections', []))}개 detection 결과는 숨김)")
        
        # OCR 텍스트가 있지만 Gemini 분석이 없는 경우, 브랜드 패턴 매칭 시도
        elif result.get("ocr_text") and not result.get("gemini_analysis"):
            try:
                from modules.gemini import detect_brand_and_product
                brand, product = detect_brand_and_product(result["ocr_text"])
                if brand and product:
                    food_name = f"{brand} {product}"
                    response["food_name"] = food_name
                    response["recognized_product"] = food_name
                    
                    # 브랜드 패턴 매칭 결과만을 detections로 설정
                    brand_detection = {
                        "label": food_name,
                        "confidence": 0.9,  # 90% 신뢰도
                        "bbox": [],
                        "class": food_name,
                        "korean_name": food_name
                    }
                    response["detections"] = [brand_detection]
                    print(f"🔍 브랜드 패턴으로 인식: {food_name}")
                    print(f"   (기존 detection 결과는 숨김)")
                elif brand:  # 브랜드만 인식된 경우
                    response["food_name"] = brand
                    response["recognized_product"] = brand
                    
                    brand_only_detection = {
                        "label": f"{brand} 제품",
                        "confidence": 0.8,  # 80% 신뢰도
                        "bbox": [],
                        "class": brand,
                        "korean_name": f"{brand} 제품"
                    }
                    response["detections"] = [brand_only_detection]
                    print(f"🔍 브랜드만 인식: {brand}")
            except:
                pass
        
        print(f"✅ 응답 성공: {len(response['detections'])} 항목 표시")
        if "food_name" in response:
            print(f"🍽️ 인식된 제품: {response['food_name']}")
        if result.get("gemini_analysis"):
            print(f"   (Gemini 분석으로 인식 - 다른 탐지 결과는 표시하지 않음)")
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
        "version": "2.1",
        "features": [
            "Food Detection",
            "OCR Text Recognition", 
            "Gemini AI Analysis",
            "Smart Display (제품명 인식 시 해당 제품만 표시)"
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
    print("🤖 스마트 푸드 챗봇 Webhook 서버 v2.1")
    print(f"📡 Food Detection API: {FOOD_DETECTION_API}")
    print("=" * 50)
    print("✨ 주요 기능:")
    print("- 이미지에서 음식 객체 탐지")
    print("- OCR로 텍스트 인식")
    print("- Gemini AI로 제품명 분석")
    print("- 제품명 인식 시 해당 제품만 표시")
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
