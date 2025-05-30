# cv-service/main.py - 최종 병합 버전 (바나나 코드 제거)
from dotenv import load_dotenv
import os

# .env 파일 로드 (가장 먼저 실행)
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import traceback
import cv2
import numpy as np
import openai
import base64
from io import BytesIO
from PIL import Image

# 기존 팀원 모듈들 (그대로 유지)
from modules.yolo_detector1 import detect_objects, load_yolo_model
from modules.ocr_processor1 import (
    extract_text_with_ocr,           # 팀원 기본 함수
    extract_text_enhanced,           # 내 향상된 함수
    get_nutrition_analysis,          # 영양 분석
    get_cooking_analysis,           # 요리 분석
    get_complete_analysis,          # 완전 분석
    get_ocr_status                  # 상태 확인
)
from modules.gemini import analyze_text_with_gemini

# FastAPI 앱 생성
app = FastAPI(title="Food Detection API", version="2.0.0")

# CORS 설정 강화
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.19:3000",
        "*"  # 개발 중에만 사용
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# YOLO 모델 로드
print("YOLO 모델 로딩 중...")
model = load_yolo_model()
print("✅ YOLO 모델 로드 성공" if model else "❌ YOLO 모델 로드 실패")

# 환경 변수 확인
print(f"CLOVA_OCR_API_URL 설정: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY 설정: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY 설정: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"OPENAI_API_KEY 설정: {bool(os.environ.get('OPENAI_API_KEY'))}")

@app.get("/")
async def root():
    return {
        "message": "Food Detection API - Enhanced Version",
        "version": "2.0.0",
        "status": "running",
        "model_loaded": model is not None,
        "env_vars": {
            "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
            "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
            "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
            "openai_key": bool(os.environ.get('OPENAI_API_KEY'))
        },
        "available_features": [
            "basic_yolo_detection",
            "smart_yolo_detection", 
            "basic_ocr",
            "enhanced_ocr_with_gemini",
            "nutrition_analysis",
            "cooking_suggestions",
            "complete_integrated_analysis"
        ]
    }

# 🔸 기존 엔드포인트 1: 기본 YOLO 탐지 (팀원 코드)
@app.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.5):
    """기본 YOLO 식품 탐지"""
    if model is None:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"📁 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"🔍 YOLO 탐지 시작 (신뢰도: {confidence})")
        detections, _ = detect_objects(model, image_path, confidence)
        print(f"✅ 탐지 완료: {len(detections)}개 객체")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "success": True,
            "detections": detections,
            "method": "basic_yolo",
            "total_count": len(detections)
        }
        
    except Exception as e:
        print(f"❌ 탐지 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"탐지 오류: {str(e)}")

# 🆕 스마트 YOLO 탐지 (GPT 검증 포함)
@app.post("/api/detect-smart")
async def detect_smart(file: UploadFile = File(...), confidence: float = 0.5):
    """🧠 스마트 YOLO 탐지 (GPT 검증 포함)"""
    if model is None:
        raise HTTPException(status_code=500, detail="YOLO 모델이 로드되지 않았습니다")
    
    try:
        print(f"🧠 스마트 탐지 시작: {file.filename}")
        image_bytes = await file.read()
        
        # 1단계: 기본 YOLO 탐지
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        print(f"🔍 YOLO 탐지 시작 (신뢰도: {confidence})")
        detections, _ = detect_objects(model, image_path, confidence)
        print(f"✅ YOLO 탐지 완료: {len(detections)}개 객체")
        
        # 2단계: 품질 검증 (의심스러운 결과 체크)
        is_suspicious = check_detection_quality(detections)
        
        # 3단계: GPT 검증 (필요시)
        final_detections = detections
        verification_used = False
        gpt_response = ""
        
        if is_suspicious and os.getenv("OPENAI_API_KEY"):
            print("🤔 품질 검증 필요 → GPT 검증 시작")
            
            try:
                gpt_result = verify_with_gpt_general(image_path, detections)
                
                if gpt_result.get("success"):
                    gpt_response = gpt_result.get("gpt_raw_response", "")
                    
                    if gpt_result.get("needs_correction"):
                        final_detections = gpt_result.get("corrected_detections", detections)
                        verification_used = True
                        print("✅ GPT 검증 완료 → 결과 교정됨")
                    else:
                        print("✅ GPT 검증 완료 → 원본 결과 유지")
                        
            except Exception as gpt_error:
                print(f"⚠️ GPT 검증 중 오류: {gpt_error}")
        
        # 정리
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "success": True,
            "detections": final_detections,
            "method": "smart_yolo",
            "verification": {
                "quality_check": is_suspicious,
                "gpt_used": verification_used,
                "gpt_response": gpt_response
            },
            "counts": {
                "original": len(detections),
                "final": len(final_detections)
            },
            "confidence_threshold": confidence
        }
        
    except Exception as e:
        print(f"❌ 스마트 탐지 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"스마트 탐지 오류: {str(e)}")

# 🔸 기존 엔드포인트 2: 기본 OCR (팀원 코드)
@app.post("/api/ocr")
async def extract_ocr_text(file: UploadFile = File(...)):
    """기본 OCR 텍스트 추출"""
    try:
        print(f"📁 OCR 파일 업로드: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"📄 OCR 텍스트 추출 시작")
        ocr_text = extract_text_with_ocr(image_path)
        print(f"✅ OCR 완료: {len(ocr_text) if ocr_text else 0}자")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "success": bool(ocr_text),
            "text": ocr_text,
            "method": "basic_ocr"
        }
        
    except Exception as e:
        print(f"❌ OCR 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR 오류: {str(e)}")

# 🆕 향상된 OCR (Gemini 분석 포함)
@app.post("/api/ocr-enhanced")
async def extract_ocr_enhanced(
    file: UploadFile = File(...), 
    use_gemini: bool = True,
    analysis_type: str = "complete"
):
    """향상된 OCR (선택적 Gemini 분석 포함)"""
    try:
        print(f"🔍 향상된 OCR 시작: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 분석 타입에 따른 처리
        if analysis_type == "nutrition":
            result = get_nutrition_analysis(image_path)
        elif analysis_type == "cooking":
            result = get_cooking_analysis(image_path)
        elif analysis_type == "complete":
            result = get_complete_analysis(image_path)
        else:
            # 기본 OCR + 선택적 Gemini
            analysis_types = ["food_name", "nutrition_info"] if use_gemini else None
            result = extract_text_enhanced(image_path, use_gemini, analysis_types)
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        print(f"❌ 향상된 OCR 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"향상된 OCR 오류: {str(e)}")

# 🆕 영양 분석 전용 엔드포인트
@app.post("/api/nutrition-analysis")
async def analyze_nutrition(file: UploadFile = File(...)):
    """영양 성분 분석 특화"""
    try:
        print(f"🥗 영양 분석 시작: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        result = get_nutrition_analysis(image_path)
        
        try:
            os.remove(image_path)
        except:
            pass
        
        # 영양 정보를 구조화해서 반환
        if result['success'] and 'nutrition_info' in result.get('analyses', {}):
            nutrition_text = result['analyses']['nutrition_info']
            
            # 간단한 파싱 (칼로리, 탄수화물 등 추출)
            parsed_nutrition = parse_nutrition_text(nutrition_text)
            result['parsed_nutrition'] = parsed_nutrition
        
        return result
        
    except Exception as e:
        print(f"❌ 영양 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=f"영양 분석 오류: {str(e)}")

# 🆕 요리 추천 전용 엔드포인트
@app.post("/api/cooking-suggestions")
async def get_cooking_suggestions(file: UploadFile = File(...)):
    """요리법 및 레시피 추천"""
    try:
        print(f"👨‍🍳 요리 추천 시작: {file.filename}")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        result = get_cooking_analysis(image_path)
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        print(f"❌ 요리 추천 오류: {e}")
        raise HTTPException(status_code=500, detail=f"요리 추천 오류: {str(e)}")

# 🔸 기존 엔드포인트 3: Gemini 분석 (팀원 코드)
@app.post("/api/analyze")
async def analyze_with_gemini(request_data: dict):
    """Gemini AI 분석"""
    try:
        text = request_data.get("text", "")
        detection_results = request_data.get("detection_results")
        
        print(f"🧠 Gemini 분석 시작 - 텍스트 길이: {len(text)}")
        analysis = analyze_text_with_gemini(text, detection_results)
        print(f"✅ Gemini 분석 완료")
        
        return {"analysis": analysis}
        
    except Exception as e:
        print(f"❌ Gemini 분석 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini 분석 오류: {str(e)}")

# 🚀 완전 통합 분석 엔드포인트 (핵심 기능)
@app.post("/api/analyze-complete")
async def analyze_complete(
    file: UploadFile = File(...), 
    confidence: float = 0.5,
    include_cooking: bool = True,
    include_nutrition: bool = True
):
    """🚀 완전 통합 분석: 스마트 YOLO + 향상된 OCR + Gemini"""
    try:
        print(f"🚀 완전 통합 분석 시작: {file.filename}")
        
        # 파일을 여러 번 사용하기 위해 바이트로 저장
        file_content = await file.read()
        
        # 1단계: 스마트 YOLO 탐지
        print("1️⃣ 스마트 YOLO 탐지 수행 중...")
        from io import BytesIO
        temp_file = UploadFile(filename=file.filename, file=BytesIO(file_content))
        smart_detection_result = await detect_smart(temp_file, confidence)
        
        # 2단계: 향상된 OCR 분석
        print("2️⃣ 향상된 OCR 분석 수행 중...")
        temp_file = UploadFile(filename=file.filename, file=BytesIO(file_content))
        
        # 분석 타입 결정
        analysis_type = "complete"
        if include_nutrition and include_cooking:
            analysis_type = "complete"
        elif include_nutrition:
            analysis_type = "nutrition"
        elif include_cooking:
            analysis_type = "cooking"
        
        ocr_result = await extract_ocr_enhanced(temp_file, use_gemini=True, analysis_type=analysis_type)
        
        # 3단계: Gemini 종합 분석 (기존 방식)
        print("3️⃣ Gemini 종합 분석 수행 중...")
        gemini_data = {
            "text": ocr_result.get("ocr_text", "") or ocr_result.get("text", ""),
            "detection_results": smart_detection_result.get("detections", []),
            "analysis_type": "complete_integrated_analysis",
            "prompt": f"""다음 정보를 바탕으로 종합적인 식품 분석을 해주세요:

YOLO 탐지 결과: {smart_detection_result.get("detections", [])}
OCR 텍스트: {ocr_result.get("ocr_text", "")}

🔍 **종합 분석 요청사항**:
1. 탐지된 식품들의 정확한 식별
2. 영양학적 가치 평가
3. 추천 조리법 및 레시피
4. 보관 및 구매 팁
5. 건강상 주의사항

📋 **출력 형식**:
🍎 식품 목록: [탐지된 식품들]
📊 영양 정보: [주요 영양소]
👨‍🍳 추천 요리: [3가지 요리법]
💡 생활 팁: [보관법, 구매 팁]
⚠️ 주의사항: [건강상 고려사항]

종합적으로 분석해주세요."""
        }
        
        gemini_result = await analyze_with_gemini(gemini_data)
        
        # 4단계: 결과 통합 및 요약
        detected_foods = [det.get('class', 'Unknown') for det in smart_detection_result.get("detections", [])]
        ocr_analyses = ocr_result.get("analyses", {})
        
        # 최종 결과 구성
        final_result = {
            "success": True,
            "analysis_type": "complete_integrated",
            "timestamp": os.environ.get("TZ", "UTC"),
            
            # 각 단계별 결과
            "results": {
                "smart_detection": smart_detection_result,
                "enhanced_ocr": ocr_result,
                "gemini_analysis": gemini_result
            },
            
            # 통합 요약
            "summary": {
                "detected_foods": detected_foods,
                "food_count": len(detected_foods),
                "ocr_text_length": len(ocr_result.get("ocr_text", "")),
                "gpt_verification_used": smart_detection_result.get("verification", {}).get("gpt_used", False),
                "enhanced_features_used": {
                    "smart_yolo": True,
                    "enhanced_ocr": True,
                    "nutrition_analysis": include_nutrition,
                    "cooking_suggestions": include_cooking
                }
            },
            
            # 구조화된 분석 결과
            "structured_analysis": {
                "food_name": ocr_analyses.get("food_name", ""),
                "nutrition_info": ocr_analyses.get("nutrition_info", ""),
                "main_ingredients": ocr_analyses.get("main_ingredients", ""),
                "cooking_methods": ocr_analyses.get("cooking_method", ""),
                "recipe_suggestions": ocr_analyses.get("recipe_suggestions", "")
            }
        }
        
        print(f"✅ 완전 통합 분석 완료: {len(detected_foods)}개 식품 탐지")
        return final_result
        
    except Exception as e:
        print(f"❌ 완전 통합 분석 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"완전 통합 분석 오류: {str(e)}")

# 🔧 시스템 상태 확인 엔드포인트
@app.get("/api/system-status")
async def get_system_status():
    """시스템 전체 상태 확인"""
    yolo_status = bool(model)
    ocr_status = get_ocr_status()
    
    return {
        "system_health": "healthy",
        "components": {
            "yolo_model": {
                "status": "active" if yolo_status else "inactive",
                "available": yolo_status
            },
            "ocr_system": ocr_status,
            "apis": {
                "openai_gpt": bool(os.getenv("OPENAI_API_KEY")),
                "gemini": bool(os.getenv("GEMINI_API_KEY")),
                "clova_ocr": bool(os.getenv("CLOVA_SECRET_KEY"))
            }
        },
        "available_endpoints": [
            "/api/detect (기본 YOLO)",
            "/api/detect-smart (스마트 YOLO + GPT)",
            "/api/ocr (기본 OCR)",
            "/api/ocr-enhanced (향상된 OCR + Gemini)",
            "/api/nutrition-analysis (영양 분석)",
            "/api/cooking-suggestions (요리 추천)",
            "/api/analyze (Gemini 분석)",
            "/api/analyze-complete (완전 통합 분석)"
        ]
    }

# 🔍 보조 함수들
def check_detection_quality(detections):
    """탐지 결과 품질 검사 (바나나 관련 코드 제거)"""
    if not detections:
        return True  # 아무것도 탐지 안됨
    
    quality_issues = []
    
    # 1. 평균 신뢰도가 낮음
    confidences = [d.get('confidence', 0) for d in detections]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    if avg_confidence < 0.6:
        quality_issues.append("평균 신뢰도 낮음")
    
    # 2. 같은 객체가 과도하게 많음
    from collections import Counter
    detected_classes = [d.get('class', '').lower() for d in detections]
    class_counts = Counter(detected_classes)
    for item, count in class_counts.items():
        if count >= 5:  # 5개 이상이면 의심
            quality_issues.append(f"{item}이 {count}개로 과다")
    
    # 3. 신뢰도 편차가 큼
    if confidences and len(confidences) > 1:
        confidence_std = np.std(confidences)
        if confidence_std > 0.3:
            quality_issues.append("신뢰도 편차 큼")
    
    print(f"🔍 품질 검사 결과: {quality_issues}")
    return len(quality_issues) >= 1

def verify_with_gpt_general(image_path, yolo_detections):
    """일반적인 GPT 검증 (바나나 특화 코드 제거)"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "OpenAI API 키가 설정되지 않음"}
        
        # 이미지를 base64로 변환
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # YOLO 결과 요약
        yolo_summary = []
        for det in yolo_detections:
            yolo_summary.append(f"{det.get('class', '알수없음')} (신뢰도: {det.get('confidence', 0):.2f})")
        
        prompt = f"""
🔍 식품 탐지 결과를 검증해주세요.

YOLO 탐지 결과: {', '.join(yolo_summary)}

이미지를 보고 다음을 확인해주세요:
1. 위 탐지 결과가 정확한가요?
2. 실제로 보이는 식품은 무엇인가요?
3. 개수는 정확한가요?

💡 **검증 기준**:
- 색상과 형태가 일치하는지 확인
- 객체의 개수가 정확한지 확인
- 일반적이지 않은 조합인지 확인

간단하게 답변해주세요:
- "정확함" 또는 "부정확함"
- 부정확하다면 올바른 식품명과 개수를 알려주세요
"""

        # OpenAI API 호출
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        gpt_response = response.choices[0].message.content.strip()
        print(f"🧠 GPT 검증 응답: {gpt_response}")
        
        # 응답 분석
        needs_correction = "부정확" in gpt_response or "틀렸" in gpt_response or "잘못" in gpt_response
        
        corrected_detections = yolo_detections  # 기본값은 원본 유지
        
        # 교정이 필요한 경우 간단한 처리
        if needs_correction:
            print("🔄 GPT가 교정 필요하다고 판단함")
            # 여기서는 원본을 유지하되, 신뢰도를 낮춤
            corrected_detections = []
            for det in yolo_detections:
                corrected_det = det.copy()
                corrected_det['confidence'] = corrected_det.get('confidence', 1.0) * 0.7  # 신뢰도 감소
                corrected_det['gpt_verified'] = False
                corrected_detections.append(corrected_det)
        
        return {
            "success": True,
            "needs_correction": needs_correction,
            "corrected_detections": corrected_detections,
            "gpt_raw_response": gpt_response
        }
        
    except Exception as e:
        print(f"❌ GPT 검증 오류: {e}")
        return {"success": False, "error": str(e)}

def parse_nutrition_text(nutrition_text):
    """영양 정보 텍스트 파싱"""
    try:
        import re
        
        parsed = {}
        
        # 칼로리 추출
        calorie_match = re.search(r'칼로리[:\s]*(\d+)', nutrition_text)
        if calorie_match:
            parsed['calories'] = f"{calorie_match.group(1)}kcal"
        
        # 탄수화물 추출
        carb_match = re.search(r'탄수화물[:\s]*(\d+)', nutrition_text)
        if carb_match:
            parsed['carbohydrates'] = f"{carb_match.group(1)}g"
        
        # 단백질 추출
        protein_match = re.search(r'단백질[:\s]*(\d+)', nutrition_text)
        if protein_match:
            parsed['protein'] = f"{protein_match.group(1)}g"
        
        # 지방 추출
        fat_match = re.search(r'지방[:\s]*(\d+)', nutrition_text)
        if fat_match:
            parsed['fat'] = f"{fat_match.group(1)}g"
        
        return parsed
        
    except Exception as e:
        print(f"⚠️ 영양 정보 파싱 실패: {e}")
        return {}

# 🔸 기존 헬스체크 엔드포인트들 (팀원 코드 유지)
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": os.environ.get("TZ", "UTC"),
        "model_status": "loaded" if model else "error",
        "temp_dir_exists": os.path.exists("temp"),
        "enhanced_features": {
            "smart_yolo": bool(os.environ.get("OPENAI_API_KEY")),
            "enhanced_ocr": True,
            "nutrition_analysis": bool(os.environ.get("GEMINI_API_KEY")),
            "cooking_suggestions": bool(os.environ.get("GEMINI_API_KEY"))
        }
    }

@app.get("/debug/env")
async def debug_env():
    """환경 변수 상태 확인 (디버깅용)"""
    return {
        "clova_ocr_url": bool(os.environ.get('CLOVA_OCR_API_URL')),
        "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
        "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
        "openai_key": bool(os.environ.get('OPENAI_API_KEY')),
        "working_directory": os.getcwd(),
        "temp_directory": os.path.exists("temp"),
        "model_loaded": model is not None,
        "ocr_system_status": get_ocr_status()
    }

# 🆕 기능 테스트 엔드포인트
@app.post("/api/test-features")
async def test_all_features(file: UploadFile = File(...)):
    """🧪 모든 기능 테스트"""
    try:
        print("🧪 전체 기능 테스트 시작")
        
        # 기본 탐지 테스트
        basic_result = await detect_food(file, 0.5)
        
        # 스마트 탐지 테스트  
        smart_result = await detect_smart(file, 0.5)
        
        # OCR 테스트
        ocr_result = await extract_ocr_text(file)
        
        return {
            "test_type": "feature_comparison",
            "results": {
                "basic_yolo": {
                    "success": basic_result.get("success", False),
                    "count": len(basic_result.get("detections", []))
                },
                "smart_yolo": {
                    "success": smart_result.get("success", False),
                    "count": len(smart_result.get("detections", [])),
                    "gpt_used": smart_result.get("verification", {}).get("gpt_used", False)
                },
                "ocr": {
                    "success": ocr_result.get("success", False),
                    "text_length": len(ocr_result.get("text", ""))
                }
            },
            "recommendations": [
                "완전 통합 분석(/api/analyze-complete)을 사용하면 모든 기능을 한번에 사용할 수 있습니다.",
                "영양 분석만 필요하면 /api/nutrition-analysis를 사용하세요.",
                "요리 추천만 필요하면 /api/cooking-suggestions를 사용하세요."
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기능 테스트 오류: {str(e)}")

# 🆕 API 사용 가이드 엔드포인트
@app.get("/api/guide")
async def get_api_guide():
    """API 사용 가이드"""
    return {
        "api_guide": {
            "version": "2.0.0",
            "description": "통합된 식품 분석 API",
            
            "quick_start": {
                "basic_detection": "POST /api/detect - 기본 YOLO 탐지",
                "smart_detection": "POST /api/detect-smart - GPT 검증 포함",
                "complete_analysis": "POST /api/analyze-complete - 모든 기능 통합"
            },
            
            "endpoints": {
                "detection": {
                    "/api/detect": "기본 YOLO 식품 탐지",
                    "/api/detect-smart": "스마트 YOLO (GPT 검증 포함)"
                },
                "ocr": {
                    "/api/ocr": "기본 OCR 텍스트 추출",
                    "/api/ocr-enhanced": "향상된 OCR (Gemini 분석 포함)"
                },
                "specialized": {
                    "/api/nutrition-analysis": "영양 성분 분석",
                    "/api/cooking-suggestions": "요리법 및 레시피 추천",
                    "/api/analyze": "Gemini AI 분석"
                },
                "integrated": {
                    "/api/analyze-complete": "완전 통합 분석 (추천)"
                }
            },
            
            "parameters": {
                "confidence": "YOLO 신뢰도 임계값 (0.1-0.9, 기본값: 0.5)",
                "use_gemini": "Gemini 분석 사용 여부 (true/false)",
                "analysis_type": "분석 타입 (nutrition/cooking/complete)",
                "include_cooking": "요리 추천 포함 여부",
                "include_nutrition": "영양 분석 포함 여부"
            },
            
            "response_format": {
                "success": "요청 성공 여부",
                "detections": "탐지된 객체 목록",
                "text": "OCR 추출 텍스트", 
                "analyses": "Gemini 분석 결과",
                "method": "사용된 분석 방법"
            },
            
            "examples": {
                "basic_detection": {
                    "request": "POST /api/detect",
                    "files": {"file": "image.jpg"},
                    "params": {"confidence": 0.5}
                },
                "complete_analysis": {
                    "request": "POST /api/analyze-complete", 
                    "files": {"file": "image.jpg"},
                    "params": {
                        "confidence": 0.5,
                        "include_cooking": True,
                        "include_nutrition": True
                    }
                }
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 통합 서버 시작 중...")
    print("📋 사용 가능한 기능:")
    print("   🔸 기본 기능:")
    print("     - /api/detect (기본 YOLO)")
    print("     - /api/ocr (기본 OCR)")  
    print("     - /api/analyze (Gemini 분석)")
    print("   🆕 향상된 기능:")
    print("     - /api/detect-smart (스마트 YOLO + GPT)")
    print("     - /api/ocr-enhanced (향상된 OCR + Gemini)")
    print("     - /api/nutrition-analysis (영양 분석)")
    print("     - /api/cooking-suggestions (요리 추천)")
    print("   🚀 통합 기능:")
    print("     - /api/analyze-complete (완전 통합 분석)")
    print("   🔧 유틸리티:")
    print("     - /api/system-status (시스템 상태)")
    print("     - /api/test-features (기능 테스트)")
    print("     - /api/guide (사용 가이드)")
    print(f"📋 API 문서: http://0.0.0.0:8000/docs")
    print(f"📖 사용 가이드: http://0.0.0.0:8000/api/guide")
    uvicorn.run(app, host="0.0.0.0", port=8000)