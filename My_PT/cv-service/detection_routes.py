# detection_routes.py - 완전한 버전

from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
import traceback
import json

# 라우터 생성
detection_router = APIRouter()

@detection_router.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.5, use_ensemble: bool = True, use_enhanced: bool = True):
    """메인 음식 탐지 API"""
    try:
        print(f"\n{'='*60}")
        print("DETECTION API CALLED")
        print(f"{'='*60}")
        print(f"File: {file.filename}")
        print(f"Content-Type: {file.content_type}")
        print(f"Confidence: {confidence}")
        print(f"Use Ensemble: {use_ensemble}")
        
        # 전역 변수들 가져오기
        import main
        ensemble_models = main.ensemble_models
        enhanced_detector = main.enhanced_detector
        
        from modules.yolo_detector import detect_objects
        from modules.ocr_processor import extract_text_with_ocr
        
        print(f"Models loaded: {list(ensemble_models.keys())}")
        print(f"Model count: {len(ensemble_models)}")

        if not ensemble_models:
            error_detail = {
                "error": "No YOLO models loaded",
                "debug_info": {
                    "current_dir": os.getcwd(),
                    "models_dir_exists": os.path.exists("models"),
                    "models_files": os.listdir("models") if os.path.exists("models") else [],
                    "modules_dir_exists": os.path.exists("modules"),
                    "loaded_models": list(ensemble_models.keys()),
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
            raise HTTPException(status_code=500, detail=error_detail)
        
        print("\nSaving uploaded file...")
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        # 파일 저장
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"File saved to: {image_path}")
        print(f"File size: {os.path.getsize(image_path)} bytes")

        # OCR 수행
        ocr_text = None
        try:
            ocr_text = extract_text_with_ocr(image_path)
        except Exception as e:
            print(f"OCR failed: {e}")

        if use_enhanced and enhanced_detector:
            # Enhanced YOLO 사용
            print(f"🚀 Enhanced YOLO 분석 시작")
            result = enhanced_detector.comprehensive_analysis(image_path, confidence, ocr_text)
            
            # 채소 전용 분석도 함께 호출
            vegetable_result = enhanced_detector.enhanced_vegetable_analysis(image_path, confidence)

            if result["success"]:
                response = {
                    "detections": result["detections"],
                    "enhanced_info": {
                        "method": result.get("method", "enhanced"),
                        "analysis_stage": result.get("analysis_stage", "unknown"),
                        "color_analysis": result.get("color_analysis"),
                        "enhancement_info": result.get("enhancement_info", {}),
                        "brand_info": result.get("brand_info"),
                        "vegetable_predictions": vegetable_result.get("vegetable_analysis", {}).get("predicted_vegetables"),
                        "vegetable_color": vegetable_result.get("vegetable_analysis", {}).get("color_analysis", {}).get("primary_color"),
                        "vegetable_shape": vegetable_result.get("vegetable_analysis", {}).get("shape_analysis", {}).get("primary_shape"),
                        "vegetable_confidence": vegetable_result.get("vegetable_analysis", {}).get("confidence")
                    },
                    "ensemble_info": {
                        "models_used": list(ensemble_models.keys()),
                        "total_detections": len(result["detections"]),
                        "enhanced_enabled": True
                    }
                }
                
                print(f"✅ Enhanced 분석 완료: {len(result['detections'])}개 객체")
                return response
                
        # 앙상블 로직 (fallback)
        if use_ensemble and len(ensemble_models) > 1:
            print(f"\nUsing ensemble detection with {len(ensemble_models)} models")
            
            # 앙상블 함수 import
            from utils.ensemble import detect_objects_ensemble
            
            detections, model_results = detect_objects_ensemble(ensemble_models, image_path, confidence)
            
            consensus_detections = [d for d in detections if d['ensemble_info']['is_consensus']]
            single_detections = [d for d in detections if not d['ensemble_info']['is_consensus']]
            
            response = {
                "detections": detections,
                "ensemble_info": {
                    "models_used": list(ensemble_models.keys()),
                    "total_detections": len(detections),
                    "consensus_detections": len(consensus_detections),
                    "single_detections": len(single_detections),
                    "consensus_rate": f"{len(consensus_detections)/len(detections)*100:.1f}%" if detections else "0%",
                    "individual_results": {
                        model_name: len(results) for model_name, results in model_results.items()
                    },
                    "ensemble_ready": len(ensemble_models) == 3
                }
            }
        else:
            model_name, model = next(iter(ensemble_models.items()))
            print(f"\nUsing single model: {model_name}")
            detections, _ = detect_objects(model, image_path, confidence)
            
            response = {
                "detections": detections,
                "model_used": model_name,
                "ensemble_enabled": False,
                "available_models": list(ensemble_models.keys())
            }
        
        print(f"\nDetection complete: {len(detections)} objects found")
        print(f"{'='*60}\n")
        
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
        
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_info": {
                "models_loaded": list(main.ensemble_models.keys()) if hasattr(main, 'ensemble_models') else [],
                "model_count": len(main.ensemble_models) if hasattr(main, 'ensemble_models') else 0,
                "file_name": file.filename if 'file' in locals() else "Unknown",
                "current_dir": os.getcwd()
            }
        }
        
        raise HTTPException(status_code=500, detail=error_response)

@detection_router.post("/api/detect/single/{model_name}")
async def detect_food_single_model(model_name: str, file: UploadFile = File(...), confidence: float = 0.5):
    """단일 모델 탐지 API"""
    import main
    ensemble_models = main.ensemble_models
    
    from modules.yolo_detector import detect_objects
    from modules.ocr_processor import extract_text_with_ocr
    
    if model_name not in ensemble_models:
        available_models = list(ensemble_models.keys())
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
            shutil.copyfileobj(file.file, f)

        # OCR 추출 (선택적으로 사용 가능)
        ocr_text = None
        try:
            ocr_text = extract_text_with_ocr(image_path)
            print(f"OCR text (optional): {ocr_text[:50]}...")
        except Exception as e:
            print(f"OCR failed (ignored in this API): {e}")

        # 모델 탐지 수행
        print(f"Detecting with {model_name} model...")
        model = ensemble_models[model_name]
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
            "other_available_models": [m for m in ensemble_models.keys() if m != model_name]
        }
        
    except Exception as e:
        print(f"\nERROR in detect_food_single_model:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{model_name} detection error: {str(e)}")

@detection_router.post("/api/detect/ensemble/custom")
async def detect_food_custom_ensemble(
    file: UploadFile = File(...), 
    confidence: float = 0.5,
    yolo11s_weight: float = 1.0,
    best_weight: float = 1.2,
    best_friged_weight: float = 1.1,
    iou_threshold: float = 0.5
):
    """커스텀 앙상블 가중치 탐지 API"""
    import main
    ensemble_models = main.ensemble_models
    
    from utils.ensemble import ensemble_detections
    from modules.yolo_detector import detect_objects
    
    if not ensemble_models:
        raise HTTPException(status_code=500, detail="YOLO models not loaded")
    
    try:
        print(f"\n=== Custom Ensemble Detection API Called ===")
        print(f"File: {file.filename}")
        
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        custom_weights = {
            'yolo11s': yolo11s_weight,
            'best': best_weight,
            'best_friged': best_friged_weight
        }
        
        print(f"Custom weights: {custom_weights}")
        print(f"IoU threshold: {iou_threshold}")
        
        all_detections = {}
        for model_name, model in ensemble_models.items():
            try:
                detections, _ = detect_objects(model, image_path, confidence)
                all_detections[model_name] = detections
                print(f"{model_name}: {len(detections)} detections")
            except Exception as e:
                print(f"{model_name} error: {e}")
                all_detections[model_name] = []
        
        final_detections = ensemble_detections(
            all_detections, 
            iou_threshold=iou_threshold, 
            confidence_weights=custom_weights
        )
        
        print(f"Custom ensemble complete: {len(final_detections)} final objects")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "detections": final_detections,
            "custom_ensemble_info": {
                "weights_used": custom_weights,
                "iou_threshold": iou_threshold,
                "models_used": list(ensemble_models.keys()),
                "total_detections": len(final_detections),
                "individual_results": {
                    model_name: len(results) for model_name, results in all_detections.items()
                }
            }
        }
        
    except Exception as e:
        print(f"\nERROR in detect_food_custom_ensemble:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Custom ensemble error: {str(e)}")

@detection_router.get("/api/models/info")
async def get_models_info():
    """모델 정보 API"""
    import main
    ensemble_models = main.ensemble_models
    
    print(f"\n=== Models Info API Called ===")
    
    model_info = {}
    target_models = ["yolo11s", "best", "best_friged"]
    
    for model_name in target_models:
        if model_name in ensemble_models:
            try:
                model = ensemble_models[model_name]
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
        "loaded_count": len(ensemble_models),
        "target_count": len(target_models),
        "ensemble_ready": len(ensemble_models) > 1,
        "full_ensemble": len(ensemble_models) == 3,
        "missing_models": [name for name in target_models if name not in ensemble_models]
    }