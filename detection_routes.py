# detection_routes.py - 완전한 버전 (수정됨)

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import os
import shutil
import traceback
import json

# 🔧 새로운 모델 로더 import
from services.model_loader import get_enhanced_detector, get_loaded_models, debug_status

# 라우터 생성
detection_router = APIRouter()

@detection_router.post("/api/detect")
async def detect_food(
    file: UploadFile = File(...), 
    confidence: float = Form(0.5), 
    use_ensemble: bool = Form(True), 
    use_enhanced: bool = Form(True)
):
    """메인 음식 탐지 API"""
    try:
        print(f"\n{'='*60}")
        print("DETECTION API CALLED")
        print(f"{'='*60}")
        print(f"File: {file.filename}")
        print(f"Content-Type: {file.content_type}")
        print(f"Confidence: {confidence}")
        print(f"Use Ensemble: {use_ensemble}")
        print(f"{'='*60}")
        
        # 🔧 새로운 방식으로 모델 상태 확인
        detector = get_enhanced_detector()
        models = get_loaded_models()
        
        print(f"Models loaded: {list(models.keys())}")
        print(f"Model count: {len(models)}")

        if not models:
            debug_info = debug_status()
            print(f"DEBUG INFO: {debug_info}")
            
            error_detail = {
                "error": "No YOLO models loaded",
                "debug_info": {
                    "current_dir": os.getcwd(),
                    "models_dir_exists": os.path.exists("models"),
                    "models_files": os.listdir("models") if os.path.exists("models") else [],
                    "modules_dir_exists": os.path.exists("modules"),
                    "loaded_models": list(models.keys()),
                    "debug_status": debug_info,
                    "suggestions": [
                        "1. Check if models/*.pt files exist",
                        "2. Check if modules/yolo_detector.py exists", 
                        "3. Run: pip install ultralytics torch",
                        "4. Check file permissions: chmod 644 models/*.pt"
                    ]
                }
            }
            print(f"\nERROR DETAIL:")
            print(json.dumps(error_detail, indent=2))
            
            return JSONResponse(
                status_code=500,
                content=error_detail
            )
        
        if not detector:
            return JSONResponse(
                status_code=500,
                content={"error": "Enhanced detector not initialized"}
            )
        
        print("\nSaving uploaded file...")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        # 파일 저장 - Form 데이터 처리
        with open(image_path, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"File saved to: {image_path}")
        print(f"File size: {len(content)} bytes")

        # OCR 수행
        ocr_text = None
        try:
            from modules.ocr_processor import extract_text_with_ocr
            ocr_text = extract_text_with_ocr(image_path)
            print(f"OCR text extracted: {ocr_text[:50]}..." if ocr_text else "No OCR text")
        except Exception as e:
            print(f"OCR failed: {e}")

        if use_enhanced and detector:
            # Enhanced YOLO 사용
            print(f"🚀 Enhanced YOLO 분석 시작")
            result = detector.comprehensive_analysis(image_path, confidence, ocr_text)
            if ocr_text and result.get("success"):
                if not result.get("brand_info"):
                    result["brand_info"] = {}
                result["brand_info"]["ocr_text"] = ocr_text
                print(f"✅ OCR 텍스트를 brand_info에 추가: {ocr_text}")
            # 채소 전용 분석도 함께 호출
            try:
                vegetable_result = detector.enhanced_vegetable_analysis(image_path, confidence)
            except Exception as veg_error:
                print(f"채소 분석 실패: {veg_error}")
                vegetable_result = {"success": False}

            if result.get("success"):
                response = {
                    "detections": result["detections"],
                    "enhanced_info": {
                        "method": result.get("method", "enhanced"),
                        "analysis_stage": result.get("analysis_stage", "unknown"),
                        "color_analysis": result.get("color_analysis"),
                        "enhancement_info": result.get("enhancement_info", {}),
                        "brand_info": result.get("brand_info"),
                        "vegetable_predictions": vegetable_result.get("vegetable_analysis", {}).get("predicted_vegetables") if vegetable_result.get("success") else None,
                        "vegetable_color": vegetable_result.get("vegetable_analysis", {}).get("color_analysis", {}).get("primary_color") if vegetable_result.get("success") else None,
                        "vegetable_shape": vegetable_result.get("vegetable_analysis", {}).get("shape_analysis", {}).get("primary_shape") if vegetable_result.get("success") else None,
                        "vegetable_confidence": vegetable_result.get("vegetable_analysis", {}).get("confidence") if vegetable_result.get("success") else None
                    },
                    "ensemble_info": {
                        "models_used": list(models.keys()),
                        "total_detections": len(result["detections"]),
                        "enhanced_enabled": True
                    }
                }
                
                print(f"✅ Enhanced 분석 완료: {len(result['detections'])}개 객체")
                
                # 임시 파일 정리
                try:
                    os.remove(image_path)
                except:
                    pass
                
                return response
                
        # 앙상블 로직 (fallback) - 기본 YOLO 탐지만
        print(f"\nFallback to basic YOLO detection")
        try:
            from modules.yolo_detector import detect_objects
            
            # 첫 번째 사용 가능한 모델 사용
            model_name, model = next(iter(models.items()))
            print(f"Using model: {model_name}")
            
            detections, _ = detect_objects(model, image_path, confidence)
            
            response = {
                "detections": detections,
                "model_used": model_name,
                "ensemble_enabled": False,
                "available_models": list(models.keys()),
                "method": "basic_yolo"
            }
            
        except Exception as e:
            print(f"기본 탐지도 실패: {e}")
            response = {
                "detections": [],
                "error": f"모든 탐지 방법 실패: {str(e)}",
                "method": "failed"
            }
        
        print(f"\nDetection complete: {len(response.get('detections', []))} objects found")
        print(f"{'='*60}\n")
        
        # 임시 파일 정리
        try:
            os.remove(image_path)
        except:
            pass
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in detect_food:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        
        # 디버그 정보 수집
        try:
            debug_info = debug_status()
        except:
            debug_info = {"error": "debug_status failed"}
        
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_info": {
                "debug_status": debug_info,
                "file_name": getattr(file, 'filename', 'Unknown') if 'file' in locals() else "Unknown",
                "current_dir": os.getcwd()
            }
        }
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )

@detection_router.post("/api/detect/single/{model_name}")
async def detect_food_single_model(model_name: str, file: UploadFile = File(...), confidence: float = 0.5):
    """단일 모델 탐지 API"""
    # 🔧 새로운 방식으로 모델 가져오기
    models = get_loaded_models()
    
    if model_name not in models:
        available_models = list(models.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Model '{model_name}' not found. Available models: {available_models}"
        )
    
    try:
        print(f"\n=== Single Model Detection API Called ===")
        print(f"Model: {model_name}")
        print(f"File: {file.filename}")
        
        # 파일 저장
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"

        with open(image_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # OCR 추출 (선택적으로 사용 가능)
        ocr_text = None
        try:
            from modules.ocr_processor import extract_text_with_ocr
            ocr_text = extract_text_with_ocr(image_path)
            print(f"OCR text (optional): {ocr_text[:50]}...")
        except Exception as e:
            print(f"OCR failed (ignored in this API): {e}")

        # 모델 탐지 수행
        print(f"Detecting with {model_name} model...")
        from modules.yolo_detector import detect_objects
        model = models[model_name]
        detections, _ = detect_objects(model, image_path, confidence)
        print(f"Detection complete: {len(detections)} objects")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "detections": detections,
            "model_used": model_name,
            "total_detections": len(detections),
            "other_available_models": [m for m in models.keys() if m != model_name]
        }
        
    except Exception as e:
        print(f"\nERROR in detect_food_single_model:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{model_name} detection error: {str(e)}")

@detection_router.get("/api/models/info")
async def get_models_info():
    """모델 정보 API"""
    # 🔧 새로운 방식으로 모델 정보 가져오기
    models = get_loaded_models()
    debug_info = debug_status()
    
    print(f"\n=== Models Info API Called ===")
    
    model_info = {}
    target_models = ["yolo11s", "best", "best_friged"]
    
    for model_name in target_models:
        if model_name in models:
            try:
                model = models[model_name]
                model_info[model_name] = {
                    "loaded": True,
                    "model_type": str(type(model).__name__),
                    "available": True,
                    "status": "ready"
                }
            except Exception as e:
                model_info[model_name] = {
                    "loaded": False,
                    "error": str(e),
                    "available": False,
                    "status": "error"
                }
        else:
            model_info[model_name] = {
                "loaded": False,
                "available": False,
                "status": "not_found",
                "file_path": f"models/{model_name}.pt"
            }
    
    return {
        "target_models": target_models,
        "ensemble_models": model_info,
        "loaded_count": len(models),
        "target_count": len(target_models),
        "ensemble_ready": len(models) > 1,
        "full_ensemble": len(models) == 3,
        "missing_models": [name for name in target_models if name not in models],
        "debug_status": debug_info
    }

@detection_router.get("/api/models/debug")
async def get_debug_info():
    """디버깅 정보 API"""
    debug_info = debug_status()
    models = get_loaded_models()
    detector = get_enhanced_detector()
    
    return {
        "debug_status": debug_info,
        "models_available": list(models.keys()),
        "detector_available": detector is not None,
        "current_dir": os.getcwd(),
        "models_dir_exists": os.path.exists("models"),
        "models_files": os.listdir("models") if os.path.exists("models") else []
    }
