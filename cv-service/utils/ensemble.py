# utils/ensemble.py - 앙상블 관련 함수들

import traceback
from typing import Dict, List
from modules.yolo_detector import detect_objects

def calculate_iou(box1, box2):
    """IoU 계산"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)
    
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0
    
    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0

def ensemble_detections(detections_dict, iou_threshold=0.5, confidence_weights=None):
    """앙상블 탐지 결과 통합"""
    if not detections_dict:
        return []
    
    if confidence_weights is None:
        confidence_weights = {
            'yolo11s': 1.1,
            'best': 1.1,
            'best_friged': 0.8
        }
    
    all_detections = []
    
    for model_name, detections in detections_dict.items():
        model_weight = confidence_weights.get(model_name, 1.0)
        
        for detection in detections:
            weighted_confidence = detection['confidence'] * model_weight
            
            enhanced_detection = {
                **detection,
                'confidence': weighted_confidence,
                'original_confidence': detection['confidence'],
                'model_source': model_name,
                'model_weight': model_weight
            }
            all_detections.append(enhanced_detection)
    
    all_detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    final_detections = []
    
    for current_detection in all_detections:
        should_keep = True
        current_bbox = current_detection['bbox']
        
        for kept_detection in final_detections:
            kept_bbox = kept_detection['bbox']
            
            if (current_detection['class'] == kept_detection['class'] and 
                calculate_iou(current_bbox, kept_bbox) > iou_threshold):
                should_keep = False
                
                if 'ensemble_sources' not in kept_detection:
                    kept_detection['ensemble_sources'] = [kept_detection['model_source']]
                    kept_detection['ensemble_confidences'] = [kept_detection['original_confidence']]
                    kept_detection['ensemble_weights'] = [kept_detection['model_weight']]
                
                kept_detection['ensemble_sources'].append(current_detection['model_source'])
                kept_detection['ensemble_confidences'].append(current_detection['original_confidence'])
                kept_detection['ensemble_weights'].append(current_detection['model_weight'])
                
                weighted_sum = sum(conf * weight for conf, weight in 
                                 zip(kept_detection['ensemble_confidences'], kept_detection['ensemble_weights']))
                weight_sum = sum(kept_detection['ensemble_weights'])
                kept_detection['confidence'] = weighted_sum / weight_sum if weight_sum > 0 else kept_detection['confidence']
                kept_detection['ensemble_count'] = len(kept_detection['ensemble_sources'])
                
                break
        
        if should_keep:
            current_detection['ensemble_sources'] = [current_detection['model_source']]
            current_detection['ensemble_confidences'] = [current_detection['original_confidence']]
            current_detection['ensemble_weights'] = [current_detection['model_weight']]
            current_detection['ensemble_count'] = 1
            final_detections.append(current_detection)
    
    for detection in final_detections:
        detection['ensemble_info'] = {
            'models_used': detection['ensemble_sources'],
            'individual_confidences': dict(zip(detection['ensemble_sources'], detection['ensemble_confidences'])),
            'model_weights': dict(zip(detection['ensemble_sources'], detection['ensemble_weights'])),
            'ensemble_count': detection['ensemble_count'],
            'final_confidence': detection['confidence'],
            'is_consensus': detection['ensemble_count'] >= 2
        }
    
    return final_detections

def detect_objects_ensemble(models, image_path, confidence=0.5, ensemble_weights=None):
    """3모델 앙상블 탐지"""
    if not models:
        raise ValueError("No models loaded")
    
    print(f"\n--- Starting 3-model ensemble detection ---")
    print(f"Image: {image_path}")
    print(f"Confidence threshold: {confidence}")
    print(f"Models available: {list(models.keys())}")
    
    all_detections = {}
    total_detections = 0
    
    for model_name, model in models.items():
        try:
            print(f"\n  [{model_name}] Detecting...")
            detections, _ = detect_objects(model, image_path, confidence)
            all_detections[model_name] = detections
            total_detections += len(detections)
            print(f"  [{model_name}] Found {len(detections)} objects")
        except Exception as e:
            print(f"  [{model_name}] ERROR: {e}")
            traceback.print_exc()
            all_detections[model_name] = []

    print(f"\nTotal raw detections: {total_detections} objects (before ensemble)")
    
    if ensemble_weights is None:
        ensemble_weights = {
            'yolo11s': 1.0,
            'best': 1.1,
            'best_friged': 0.9
        }
    
    final_detections = ensemble_detections(all_detections, confidence_weights=ensemble_weights)
    
    print(f"Ensemble complete: {len(final_detections)} final objects")
    
    return final_detections, all_detections