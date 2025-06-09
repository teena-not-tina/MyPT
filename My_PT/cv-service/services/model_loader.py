# services/model_loader.py - 모델 로딩 서비스

import os
from modules.yolo_detector import load_yolo_model, EnhancedYOLODetector

def load_ensemble_models():
    """3개 YOLO 앙상블 모델 로드"""
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
            if os.path.exists(model_path):
                model = load_yolo_model(model_path)
                if model:
                    models[model_name] = model
                    print(f"  ✓ {model_name} model loaded successfully!")
            else:
                print(f"  ✗ File not found: {model_path}")
        except Exception as e:
            print(f"  ✗ {model_name} model load error: {e}")
    
    print(f"\n=== MODEL LOADING SUMMARY ===")
    print(f"Final result: {len(models)} models loaded")
    print(f"Loaded models: {list(models.keys())}")
    
    return models

def create_enhanced_detector(models):
    """Enhanced 탐지기 생성"""
    if models:
        enhanced_detector = EnhancedYOLODetector(models)
        print(f"🚀 Enhanced YOLO 탐지기 초기화 완료")
        return enhanced_detector
    return None