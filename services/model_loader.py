# services/model_loader.py - 싱글톤 패턴으로 수정

import os
from modules.yolo_detector import load_yolo_model, EnhancedYOLODetector
import asyncio

# 전역 변수로 모델과 탐지기 캐시
_loaded_models = {}
_enhanced_detector = None

def load_ensemble_models():
    """3개 YOLO 앙상블 모델 로드"""
    global _loaded_models
    
    # 이미 로드된 경우 재사용
    if _loaded_models:
        print(f"✅ 기존 모델 캐시 사용: {len(_loaded_models)}개")
        return _loaded_models
    
    models = {}
    model_paths = {
        'yolo11s': 'models/yolo11s.pt',
        'best': 'models/best.pt',
        'best_friged': 'models/best_friged.pt'
    }
    
    print("\n=== LOADING 3 YOLO ENSEMBLE MODELS ===")
    print(f"Current working directory: {os.getcwd()}")
    
    for model_name, model_path in model_paths.items():
        try:
            abs_path = os.path.abspath(model_path)
            print(f"📦 YOLO 모델 로딩 시도: {abs_path}")
            
            if os.path.exists(abs_path):
                model = load_yolo_model(abs_path)
                if model:
                    models[model_name] = model
                    print(f"  ✓ {model_name} model loaded successfully!")
            else:
                print(f"  ✗ File not found: {abs_path}")
        except Exception as e:
            print(f"  ✗ {model_name} model load error: {e}")
    
    print(f"\n=== MODEL LOADING SUMMARY ===")
    print(f"Final result: {len(models)} models loaded")
    print(f"Loaded models: {list(models.keys())}")
    
    # 전역 캐시에 저장
    _loaded_models = models
    return models

def create_enhanced_detector(models=None):
    """Enhanced 탐지기 생성"""
    global _enhanced_detector, _loaded_models
    
    # 이미 생성된 경우 재사용
    if _enhanced_detector is not None:
        print(f"✅ 기존 탐지기 재사용")
        return _enhanced_detector
    
    # 모델이 전달되지 않은 경우 캐시에서 가져오기
    if models is None:
        if not _loaded_models:
            print("⚠️ 모델이 로드되지 않음. 새로 로드 시도...")
            load_ensemble_models()
        models = _loaded_models
    
    if models:
        _enhanced_detector = EnhancedYOLODetector(models)
        print(f"🚀 Enhanced YOLO 탐지기 초기화 완료")
        return _enhanced_detector
    
    print("❌ 탐지기 생성 실패: 모델이 없음")
    return None

def get_loaded_models():
    """로드된 모델 반환"""
    global _loaded_models
    if not _loaded_models:
        print("⚠️ 모델 캐시가 비어있음. 새로 로드 시도...")
        load_ensemble_models()
    return _loaded_models

def get_enhanced_detector():
    """Enhanced 탐지기 반환 (없으면 생성)"""
    global _enhanced_detector
    if _enhanced_detector is None:
        print("⚠️ 탐지기가 없음. 새로 생성 시도...")
        create_enhanced_detector()
    return _enhanced_detector

def debug_status():
    """디버깅용 상태 확인"""
    global _loaded_models, _enhanced_detector
    return {
        "models_count": len(_loaded_models),
        "model_names": list(_loaded_models.keys()),
        "detector_exists": _enhanced_detector is not None,
        "detector_models": len(_enhanced_detector.models) if _enhanced_detector else 0
    }

async def load_ensemble_models_async():
    """비동기 3개 YOLO 앙상블 모델 로드"""
    global _loaded_models
    
    if _loaded_models:
        print(f"✅ 기존 모델 캐시 사용: {len(_loaded_models)}개")
        return _loaded_models
    
    print("\n=== ASYNC LOADING 3 YOLO ENSEMBLE MODELS ===")
    
    # 동기 로딩을 별도 스레드에서 실행
    loop = asyncio.get_event_loop()
    models = await loop.run_in_executor(None, load_ensemble_models)
    
    print(f"✅ 비동기 모델 로딩 완료: {len(models)}개")
    return models
