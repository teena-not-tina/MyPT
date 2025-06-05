# -*- coding: utf-8 -*-
from dotenv import load_dotenv
import os
import sys

print("=" * 60)
print("Starting Food Detection API - Debug Version")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print("=" * 60)

load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import shutil
import traceback
import motor.motor_asyncio
from datetime import datetime
import numpy as np
import requests
import re
import json

print("\n--- Checking module imports ---")
try:
    from modules.yolo_detector import detect_objects, load_yolo_model
    print("✓ modules.yolo_detector imported successfully")
except ImportError as e:
    print(f"✗ Failed to import modules.yolo_detector: {e}")
    print("  Creating dummy functions...")
    def load_yolo_model(path):
        print(f"DUMMY: load_yolo_model called with {path}")
        return None
    def detect_objects(model, path, conf):
        print(f"DUMMY: detect_objects called")
        return [], None

try:
    from modules.ocr_processor import extract_text_with_ocr
    print("✓ modules.ocr_processor imported successfully")
except ImportError as e:
    print(f"✗ Failed to import modules.ocr_processor: {e}")
    def extract_text_with_ocr(path):
        return "DUMMY OCR TEXT"

try:
    from modules.gemini import analyze_text_with_gemini
    print("✓ modules.gemini imported successfully")
except ImportError as e:
    print(f"✗ Failed to import modules.gemini: {e}")
    def analyze_text_with_gemini(text, results):
        return "DUMMY ANALYSIS"

INGREDIENT_PATTERNS = [
    {
        "keywords": ["오렌지농축과즙", "오렌지과즙", "오렌지농축"],
        "volume": "ml",
        "result": "오렌지주스",
        "confidence": 0.95
    },
    {
        "keywords": ["아몬드추출액", "아몬드우유", "아몬드밀크"],
        "volume": "ml",
        "result": "아몬드밀크",
        "confidence": 0.95
    },
    {
        "keywords": ["원액두유", "분리대두단백", "대두농축액"],
        "volume": "ml",
        "result": "두유",
        "confidence": 0.95
    },
    {
        "keywords": ["우유", "전유", "저지방우유"],
        "volume": "ml",
        "result": "우유",
        "confidence": 0.98
    },
    {
        "keywords": ["사과과즙", "사과농축과즙"],
        "volume": "ml",
        "result": "사과주스",
        "confidence": 0.95
    },
    {
        "keywords": ["포도과즙", "포도농축과즙"],
        "volume": "ml",
        "result": "포도주스",
        "confidence": 0.95
    },
    {
        "keywords": ["토마토과즙", "토마토농축액"],
        "volume": "ml",
        "result": "토마토주스",
        "confidence": 0.95
    },
    {
        "keywords": ["백오이", "백색오이"],
        "result": "오이",
        "confidence": 0.90
    },
    {
        "keywords": ["무우", "무"],
        "result": "무",
        "confidence": 0.95
    },
    {
        "keywords": ["당근", "홍당무"],
        "result": "당근",
        "confidence": 0.95
    },
    {
        "keywords": ["양배추", "캐비지"],
        "result": "양배추",
        "confidence": 0.90
    },
    {
        "keywords": ["상추", "청상추"],
        "result": "상추",
        "confidence": 0.90
    },
    {
        "keywords": ["배추", "백배추", "절임배추"],
        "result": "배추",
        "confidence": 0.95
    },
    {
        "keywords": ["사과", "홍옥사과", "부사"],
        "result": "사과",
        "confidence": 0.95
    },
    {
        "keywords": ["배", "신고배"],
        "result": "배",
        "confidence": 0.95
    },
    {
        "keywords": ["바나나"],
        "result": "바나나",
        "confidence": 0.98
    },
    {
        "keywords": ["오렌지", "네이블오렌지"],
        "result": "오렌지",
        "confidence": 0.95
    },
    {
        "keywords": ["삼겹살", "돼지삼겹살"],
        "result": "삼겹살",
        "confidence": 0.95
    },
    {
        "keywords": ["닭가슴살", "닭고기"],
        "result": "닭가슴살",
        "confidence": 0.95
    },
    {
        "keywords": ["쇠고기", "한우"],
        "result": "쇠고기",
        "confidence": 0.95
    },
    {
        "keywords": ["연어", "훈제연어"],
        "result": "연어",
        "confidence": 0.95
    },
    {
        "keywords": ["요구르트", "요거트", "플레인요구르트"],
        "result": "요구르트",
        "confidence": 0.95
    },
    {
        "keywords": ["치즈", "슬라이스치즈", "모짜렐라"],
        "result": "치즈",
        "confidence": 0.95
    },
    {
        "keywords": ["버터", "무염버터"],
        "result": "버터",
        "confidence": 0.95
    },
    {
        "keywords": ["쌀", "백미", "현미"],
        "result": "쌀",
        "confidence": 0.98
    },
    {
        "keywords": ["라면", "즉석라면"],
        "result": "라면",
        "confidence": 0.95
    },
    {
        "keywords": ["스파게티", "파스타"],
        "result": "파스타",
        "confidence": 0.95
    },
    {
        "keywords": ["간장", "양조간장"],
        "result": "간장",
        "confidence": 0.95
    },
    {
        "keywords": ["고추장", "태양초고추장"],
        "result": "고추장",
        "confidence": 0.95
    },
    {
        "keywords": ["마요네즈", "마요"],
        "result": "마요네즈",
        "confidence": 0.95
    },
    {
        "keywords": ["케첩", "토마토케첩"],
        "result": "케챱",
        "confidence": 0.95
    }
]

def extract_keywords_from_ocr(ocr_text: str) -> List[str]:
    if not ocr_text or not isinstance(ocr_text, str):
        return []
    
    clean_text = re.sub(r'\s+', '', ocr_text)
    clean_text = re.sub(r'[^\w가-힣]', '', clean_text)
    clean_text = clean_text.lower()
    
    keywords = []
    
    for i in range(2, 5):
        for j in range(len(clean_text) - i + 1):
            word = clean_text[j:j+i]
            if len(word) >= 2 and word not in keywords:
                keywords.append(word)
    
    return keywords[:10]

def infer_ingredient_from_patterns(ocr_text: str) -> Optional[Dict]:
    if not ocr_text:
        return None
    
    normalized_text = ocr_text.lower().replace(' ', '')
    has_ml = 'ml' in normalized_text or '밀리리터' in normalized_text
    
    for pattern in INGREDIENT_PATTERNS:
        has_keyword = any(keyword.lower() in normalized_text for keyword in pattern["keywords"])
        
        if has_keyword:
            if pattern.get("volume") == "ml" and not has_ml:
                continue
            
            matched_keywords = [kw for kw in pattern["keywords"] if kw.lower() in normalized_text]
            
            return {
                "ingredient": pattern["result"],
                "confidence": pattern["confidence"],
                "matched_keywords": matched_keywords,
                "has_volume": has_ml,
                "source": "pattern_matching"
            }
    
    return None

def extract_ingredients_from_search_results(search_results: List[Dict], original_keywords: List[str]) -> List[Dict]:
    common_ingredients = [
        '오이', '당근', '무', '배추', '상추', '양배추', '브로콜리', '시금치', '고구마', '감자',
        '양파', '마늘', '생강', '대파', '쪽파', '부추', '고추', '파프리카', '토마토', '가지',
        '사과', '배', '바나나', '오렌지', '포도', '딸기', '수박', '참외', '멜론', '복숭아',
        '자두', '키위', '망고', '파인애플', '레몬', '라임', '체리', '블루베리',
        '쇠고기', '돼지고기', '닭고기', '삼겹살', '닭가슴살', '갈비', '등심', '안심',
        '연어', '고등어', '참치', '명태', '조기', '갈치', '삼치', '새우', '오징어', '문어',
        '우유', '요구르트', '치즈', '버터', '크림', '아이스크림',
        '오렌지주스', '사과주스', '포도주스', '토마토주스', '두유', '아몬드밀크', '코코넛밀크',
        '쌀', '현미', '보리', '밀', '라면', '우동', '파스타', '스파게티', '국수',
        '간장', '고추장', '된장', '마요네즈', '케챱', '식초', '설탕', '소금', '후추',
        '달걀', '계란', '두부', '김치', '김', '미역', '다시마'
    ]
    
    results = []
    
    all_text = ' '.join([
        f"{result.get('title', '')} {result.get('snippet', '')}" 
        for result in search_results
    ]).lower()
    
    for ingredient in common_ingredients:
        if ingredient in all_text:
            match_score = calculate_match_score(ingredient, original_keywords)
            
            if match_score > 0.3:
                results.append({
                    "name": ingredient,
                    "confidence": min(0.95, 0.7 + match_score * 0.25),
                    "keywords": original_keywords,
                    "match_score": match_score
                })
    
    return sorted(results, key=lambda x: x["confidence"], reverse=True)

def calculate_match_score(ingredient: str, keywords: List[str]) -> float:
    if not keywords:
        return 0
    
    total_score = 0
    ingredient_chars = list(ingredient)
    
    for keyword in keywords:
        keyword_chars = list(keyword)
        match_count = sum(1 for char in keyword_chars if char in ingredient_chars)
        
        score = match_count / max(len(keyword_chars), len(ingredient_chars))
        total_score = max(total_score, score)
    
    return total_score

async def search_similar_ingredients(keywords: List[str], query: str) -> Optional[Dict]:
    if not keywords:
        return None
    
    try:
        search_results = await perform_google_search(query)
        
        if not search_results:
            return None
        
        found_ingredients = extract_ingredients_from_search_results(search_results, keywords)
        
        if found_ingredients:
            return {
                "ingredient": found_ingredients[0]["name"],
                "confidence": found_ingredients[0]["confidence"],
                "matched_keywords": found_ingredients[0]["keywords"],
                "source": "web_search",
                "search_query": query,
                "total_results": len(search_results)
            }
    
    except Exception as e:
        print(f"Web search error: {e}")
    
    return None

async def enhanced_ocr_inference(ocr_text: str) -> Optional[Dict]:
    if not ocr_text or not ocr_text.strip():
        return None
    
    print(f"Enhanced OCR inference started: \"{ocr_text}\"")
    
    pattern_result = infer_ingredient_from_patterns(ocr_text)
    if pattern_result and pattern_result["confidence"] >= 0.85:
        print(f"Pattern matching success: {pattern_result}")
        return pattern_result
    
    keywords = extract_keywords_from_ocr(ocr_text)
    print(f"Extracted keywords: {keywords}")
    
    if keywords:
        search_terms = ' '.join(keywords[:3])
        search_query = f"{search_terms} 식재료 음식 재료"
        
        web_search_result = await search_similar_ingredients(keywords, search_query)
        if web_search_result and web_search_result["confidence"] >= 0.7:
            print(f"Web search success: {web_search_result}")
            return web_search_result
    
    if pattern_result:
        print(f"Pattern matching (low confidence): {pattern_result}")
        return pattern_result
    
    print(f"OCR inference failed: \"{ocr_text}\"")
    return None

def summarize_ocr_text(ocr_text: str) -> str:
    if not ocr_text:
        return ''
    
    keywords = extract_keywords_from_ocr(ocr_text)
    
    meaningful_keywords = [kw for kw in keywords if len(kw) >= 2][:3]
    
    return ' '.join(meaningful_keywords) if meaningful_keywords else ocr_text[:10]

async def perform_google_search(query: str) -> List[Dict]:
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        
        if not api_key or not search_engine_id:
            print("Google API key or Search Engine ID not set")
            return generate_mock_search_results(query)
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": 10,
            "lr": "lang_ko",
            "safe": "medium"
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": "google_search"
                })
            
            return results
        else:
            print(f"Google search API error: {response.status_code}")
            return generate_mock_search_results(query)
            
    except Exception as e:
        print(f"Google search API call failed: {e}")
        return generate_mock_search_results(query)

def generate_mock_search_results(query: str) -> List[Dict]:
    return [
        {
            "title": f"{query} - 네이버 백과사전",
            "snippet": f"{query}에 대한 상세한 정보와 영양성분을 확인하세요.",
            "url": "https://terms.naver.com",
            "source": "mock_search"
        },
        {
            "title": f"{query} 레시피 및 효능",
            "snippet": f"신선한 {query}의 선택법과 보관방법, 건강 효능을 소개합니다.",
            "url": "https://recipe.example.com",
            "source": "mock_search"
        },
        {
            "title": f"{query} 영양정보",
            "snippet": f"{query}의 칼로리, 단백질, 탄수화물 등 영양성분 정보입니다.",
            "url": "https://nutrition.example.com",
            "source": "mock_search"
        }
    ]

app = FastAPI(title="Food Detection API with Enhanced OCR Inference", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.19:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@192.168.0.199:27017")
DB_NAME = "test"
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "be-fit")

print("\n--- MongoDB Setup ---")
if MONGODB_URI:
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            retryWrites=True,
            retryReads=True,
            maxPoolSize=10,
            minPoolSize=1
        )
        
        db = client[DB_NAME]
        fridge_collection = db[COLLECTION_NAME]
        
        print(f"✓ MongoDB connection configured")
        print(f"  URI: {MONGODB_URI}")
        print(f"  Database: {DB_NAME}")
        print(f"  Collection: {COLLECTION_NAME}")
        
    except Exception as e:
        print(f"✗ MongoDB client creation failed: {e}")
        client = None
        db = None
        fridge_collection = None
else:
    print("✗ MONGODB_URI not set - MongoDB features disabled")
    client = None
    db = None
    fridge_collection = None

class Ingredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: Optional[float] = 0.8
    source: str = "analysis"
    bbox: Optional[List[float]] = None
    originalClass: Optional[str] = None
    ensemble_info: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class FridgeData(BaseModel):
    userId: str
    ingredients: List[Ingredient]
    timestamp: str
    totalCount: int
    totalTypes: int
    analysisMethod: Optional[str] = "ensemble"
    deviceInfo: Optional[str] = None
    
    class Config:
        from_attributes = True

class SimpleIngredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: float
    source: str

class SimpleFridgeData(BaseModel):
    userId: str
    ingredients: List[SimpleIngredient]

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    include_images: Optional[bool] = False
    safe_search: Optional[str] = "moderate"

class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    source: str

class IngredientValidationRequest(BaseModel):
    name: str
    ocr_context: Optional[str] = ""
    use_web_search: Optional[bool] = True

class V3IngredientData(BaseModel):
    name: Optional[str] = None
    ingredient: Optional[str] = None
    food: Optional[str] = None
    foodName: Optional[str] = None
    quantity: Optional[int] = 1
    count: Optional[int] = None
    amount: Optional[int] = None
    confidence: Optional[float] = 0.5
    source: Optional[str] = "v3_migration"

def convert_v3_to_current_format(v3_data):
    if not v3_data:
        return []
    
    converted_ingredients = []
    
    for idx, item in enumerate(v3_data):
        if isinstance(item, str):
            converted_ingredients.append({
                "id": idx + 1,
                "name": item,
                "quantity": 1,
                "confidence": 0.7,
                "source": "v3_text_migration"
            })
        elif isinstance(item, dict):
            name = (item.get("name") or 
                   item.get("ingredient") or 
                   item.get("food") or 
                   item.get("foodName") or 
                   "Unknown ingredient")
            
            quantity = (item.get("quantity") or 
                       item.get("count") or 
                       item.get("amount") or 1)
            
            converted_ingredients.append({
                "id": item.get("id", idx + 1),
                "name": name,
                "quantity": max(1, int(quantity)),
                "confidence": item.get("confidence", 0.5),
                "source": item.get("source", "v3_migration")
            })
    
    return converted_ingredients

def load_ensemble_models():
    models = {}
    model_paths = {
        'yolo11s': 'models/yolo11s.pt',
        'best': 'models/best.pt',
        'best_friged': 'models/best_friged.pt'
    }
    
    print("\n=== LOADING 3 YOLO ENSEMBLE MODELS ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir('.')}")
    
    print("\n--- Checking Dependencies ---")
    try:
        from ultralytics import YOLO
        print("✓ ultralytics library loaded successfully")
    except ImportError as e:
        print(f"✗ ultralytics library import failed: {e}")
        print("  Solution: pip install ultralytics")
        return models
    
    try:
        import torch
        print(f"✓ torch library loaded successfully (version: {torch.__version__})")
        if torch.cuda.is_available():
            print(f"  CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("  Running in CPU mode")
    except ImportError as e:
        print(f"✗ torch library import failed: {e}")
        print("  Solution: pip install torch")
        return models
    
    print("\n--- Checking Model Directory ---")
    models_dir = "models"
    if os.path.exists(models_dir):
        print(f"✓ models directory exists")
        try:
            files = os.listdir(models_dir)
            print(f"  Files in models directory: {files}")
            pt_files = [f for f in files if f.endswith('.pt')]
            print(f"  .pt model files: {pt_files}")
        except Exception as e:
            print(f"✗ Error reading models directory: {e}")
    else:
        print(f"✗ models directory does not exist!")
        print(f"  Solution: Create models folder and add model files")
        print(f"  Commands:")
        print(f"    mkdir models")
        print(f"    cd models")
        print(f"    wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11s.pt")
        return models
    
    print("\n--- Loading Individual Models ---")
    for model_name, model_path in model_paths.items():
        print(f"\n[{model_name}] Loading model...")
        print(f"  File path: {model_path}")
        
        try:
            if os.path.exists(model_path):
                print(f"  ✓ File exists")
                file_size = os.path.getsize(model_path)
                print(f"  File size: {file_size / (1024*1024):.1f} MB")
                
                if file_size < 1024 * 1024:
                    print(f"  ⚠️ Warning: File size too small ({file_size} bytes)")
                    print("    Model file may be corrupted")
                
                if os.access(model_path, os.R_OK):
                    print(f"  ✓ File read permission: OK")
                else:
                    print(f"  ✗ File read permission: DENIED")
                    continue
                
                print(f"  Loading model...")
                
                try:
                    print(f"    Attempting direct YOLO load...")
                    direct_model = YOLO(model_path)
                    print(f"    ✓ Direct YOLO load successful!")
                    
                    model = load_yolo_model(model_path)
                    
                    if model:
                        models[model_name] = model
                        print(f"  ✓ {model_name} model loaded successfully!")
                        print(f"    Model type: {type(model)}")
                    else:
                        print(f"  ✗ {model_name} model load failed: load_yolo_model returned None")
                        models[model_name] = direct_model
                        print(f"    Using direct YOLO load instead")
                        
                except Exception as direct_error:
                    print(f"  ✗ Direct YOLO load failed: {direct_error}")
                    print(f"    Error type: {type(direct_error).__name__}")
                    traceback.print_exc()
                    
            else:
                print(f"  ✗ File not found: {model_path}")
                dir_name = os.path.dirname(model_path)
                if os.path.exists(dir_name):
                    similar_files = [f for f in os.listdir(dir_name) if f.endswith('.pt')]
                    print(f"    .pt files in directory: {similar_files}")
                    
                    base_name = os.path.basename(model_path).replace('.pt', '')
                    similar = [f for f in similar_files if base_name.lower() in f.lower()]
                    if similar:
                        print(f"    Similar filenames: {similar}")
                    
        except Exception as e:
            print(f"  ✗ {model_name} model load error:")
            print(f"    Error type: {type(e).__name__}")
            print(f"    Error message: {str(e)}")
            traceback.print_exc()
    
    print(f"\n=== MODEL LOADING SUMMARY ===")
    print(f"Final result: {len(models)} models loaded")
    print(f"Loaded models: {list(models.keys())}")
    
    if len(models) == 0:
        print("\n⚠️ WARNING: No models loaded!")
        print("This will cause 500 errors on /api/detect endpoint")
        print("\nTroubleshooting steps:")
        print("1. Check if models/*.pt files exist")
        print("2. Ensure modules/yolo_detector.py exists and has load_yolo_model function")
        print("3. Install required packages: pip install ultralytics torch")
        print("4. Check file permissions: chmod 644 models/*.pt")
        
    elif len(models) < 3:
        print(f"\n⚠️ Warning: Only {len(models)} of 3 models loaded")
        print(f"Missing models: {[name for name in model_paths.keys() if name not in models]}")
    else:
        print("\n✓ All models loaded successfully!")
    
    return models

def calculate_iou(box1, box2):
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
    
    ensemble_stats = {}
    consensus_count = 0
    
    for detection in final_detections:
        count = detection['ensemble_count']
        if count not in ensemble_stats:
            ensemble_stats[count] = 0
        ensemble_stats[count] += 1
        
        if detection['ensemble_info']['is_consensus']:
            consensus_count += 1
    
    print(f"\nEnsemble statistics:")
    print(f"  - 1 model detection: {ensemble_stats.get(1, 0)}")
    print(f"  - 2 model consensus: {ensemble_stats.get(2, 0)}")
    print(f"  - 3 model consensus: {ensemble_stats.get(3, 0)}")
    print(f"  - Total consensus: {consensus_count} ({consensus_count/len(final_detections)*100:.1f}%)" if final_detections else "  - No detections")
    
    return final_detections, all_detections

print("\n" + "=" * 60)
print("LOADING MODELS")
print("=" * 60)
ensemble_models = load_ensemble_models()
print("=" * 60 + "\n")

print("\n--- Environment Variables Check ---")
print(f"CLOVA_OCR_API_URL set: {bool(os.environ.get('CLOVA_OCR_API_URL'))}")
print(f"CLOVA_SECRET_KEY set: {bool(os.environ.get('CLOVA_SECRET_KEY'))}")
print(f"GEMINI_API_KEY set: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"GOOGLE_API_KEY set: {bool(os.environ.get('GOOGLE_API_KEY'))}")
print(f"SEARCH_ENGINE_ID set: {bool(os.environ.get('SEARCH_ENGINE_ID'))}")
print(f"MONGODB_URI set: {bool(MONGODB_URI)}")

@app.get("/")
async def root():
    return {
        "message": "Food Detection API with Enhanced OCR Inference - DEBUG VERSION",
        "version": "4.0.0-debug",
        "status": "running",
        "debug_info": {
            "working_directory": os.getcwd(),
            "python_version": sys.version,
            "models_loaded": len(ensemble_models),
            "model_names": list(ensemble_models.keys()),
            "temp_dir_exists": os.path.exists("temp"),
            "modules_dir_exists": os.path.exists("modules"),
            "models_dir_exists": os.path.exists("models")
        },
        "features": [
            "3-Model YOLO Ensemble",
            "Enhanced OCR Inference",
            "Pattern Matching",
            "Web Search Integration",
            "MongoDB Storage",
            "V3 Data Migration"
        ],
        "ensemble_models": {
            "loaded_models": list(ensemble_models.keys()),
            "model_count": len(ensemble_models),
            "target_models": ["yolo11s", "best", "best_friged"],
            "ensemble_enabled": len(ensemble_models) > 1,
            "full_ensemble": len(ensemble_models) == 3
        },
        "mongodb_connected": fridge_collection is not None,
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri_host": MONGODB_URI.split('@')[1] if '@' in MONGODB_URI else "unknown"
        },
        "env_vars": {
            "clova_ocr": bool(os.environ.get('CLOVA_OCR_API_URL')),
            "clova_secret": bool(os.environ.get('CLOVA_SECRET_KEY')),
            "gemini_key": bool(os.environ.get('GEMINI_API_KEY')),
            "google_api_key": bool(os.environ.get('GOOGLE_API_KEY')),
            "search_engine_id": bool(os.environ.get('SEARCH_ENGINE_ID')),
            "mongodb_uri": bool(MONGODB_URI)
        }
    }

@app.post("/api/ocr")
async def extract_ocr_text(file: UploadFile = File(...)):
    try:
        print(f"\n=== OCR API Called ===")
        print(f"Filename: {file.filename}")
        print(f"Content-Type: {file.content_type}")
        
        if not file.content_type.startswith('image/'):
            print(f"ERROR: Invalid file type: {file.content_type}")
            raise HTTPException(status_code=422, detail=f"Only image files allowed. Current: {file.content_type}")
        
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        content = await file.read()
        with open(image_path, "wb") as f:
            f.write(content)
        print(f"File saved to: {image_path}")
        
        print(f"Extracting OCR text...")
        ocr_text = extract_text_with_ocr(image_path)
        print(f"OCR complete: {len(ocr_text) if ocr_text else 0} characters")
        
        try:
            os.remove(image_path)
        except:
            pass
        
        return {
            "text": ocr_text,
            "confidence": 0.85,
            "processing_time": 1.2,
            "language": "kor+eng",
            "method": "clova_ocr"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in extract_ocr_text:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR error: {str(e)}")

@app.post("/api/ocr/enhanced")
async def enhanced_ocr_analysis(file: UploadFile = File(...)):
    try:
        print(f"\n=== Enhanced OCR API Called ===")
        print(f"Filename: {file.filename}")
        
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=422, detail=f"Only image files allowed. Current: {file.content_type}")
        
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        content = await file.read()
        with open(image_path, "wb") as f:
            f.write(content)
        
        print(f"Step 1: OCR text extraction")
        ocr_text = extract_text_with_ocr(image_path)
        print(f"Extracted text: {ocr_text}")
        
        print(f"Step 2: Enhanced OCR inference")
        inference_result = await enhanced_ocr_inference(ocr_text)
        
        keywords = extract_keywords_from_ocr(ocr_text)
        summarized_text = summarize_ocr_text(ocr_text)
        
        try:
            os.remove(image_path)
        except:
            pass
        
        response = {
            "original_text": ocr_text,
            "keywords": keywords,
            "summarized_text": summarized_text,
            "inference_result": inference_result,
            "processing_steps": [
                "OCR text extraction",
                "Pattern matching analysis", 
                "Keyword extraction",
                "Web search validation" if inference_result and inference_result.get("source") == "web_search" else "Pattern-based inference",
                "Final result generation"
            ]
        }
        
        if inference_result:
            print(f"Enhanced OCR success: {inference_result['ingredient']} ({inference_result['confidence']*100:.1f}%)")
        else:
            print(f"Enhanced OCR inference failed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in enhanced_ocr_analysis:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhanced OCR analysis error: {str(e)}")

@app.post("/api/search")
async def web_search(request: SearchRequest):
    try:
        print(f"\n=== Web Search API Called ===")
        print(f"Query: {request.query}")
        
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Search query required")
        
        search_results = await perform_google_search(request.query)
        
        print(f"Search complete: {len(search_results)} results")
        
        return {
            "results": search_results[:request.max_results],
            "query": request.query,
            "total_results": len(search_results),
            "search_engine": "google_custom_search" if os.getenv("GOOGLE_API_KEY") else "mock_search"
        }
        
    except Exception as e:
        print(f"\nERROR in web_search:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Web search error: {str(e)}")

@app.post("/api/ingredient/validate")
async def validate_ingredient_name(request: IngredientValidationRequest):
    try:
        print(f"\n=== Ingredient Validation API Called ===")
        print(f"Name: {request.name}")
        
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Ingredient name required")
        
        if request.use_web_search and request.ocr_context:
            inference_result = await enhanced_ocr_inference(request.ocr_context)
            
            if inference_result:
                return {
                    "validated_name": inference_result["ingredient"],
                    "confidence": inference_result["confidence"],
                    "method": inference_result["source"],
                    "original_name": request.name,
                    "ocr_context": request.ocr_context,
                    "matched_keywords": inference_result.get("matched_keywords", [])
                }
        
        pattern_result = infer_ingredient_from_patterns(request.name)
        
        if pattern_result:
            return {
                "validated_name": pattern_result["ingredient"],
                "confidence": pattern_result["confidence"],
                "method": "pattern_matching",
                "original_name": request.name,
                "matched_keywords": pattern_result.get("matched_keywords", [])
            }
        
        return {
            "validated_name": request.name,
            "confidence": 0.5,
            "method": "no_validation",
            "original_name": request.name,
            "suggestions": []
        }
        
    except Exception as e:
        print(f"\nERROR in validate_ingredient_name:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ingredient validation error: {str(e)}")

@app.post("/api/detect")
async def detect_food(file: UploadFile = File(...), confidence: float = 0.5, use_ensemble: bool = True):
    try:
        print(f"\n{'='*60}")
        print("DETECTION API CALLED")
        print(f"{'='*60}")
        print(f"File: {file.filename}")
        print(f"Content-Type: {file.content_type}")
        print(f"Confidence: {confidence}")
        print(f"Use Ensemble: {use_ensemble}")
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
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"File saved to: {image_path}")
        print(f"File size: {os.path.getsize(image_path)} bytes")
        
        if use_ensemble and len(ensemble_models) > 1:
            print(f"\nUsing ensemble detection with {len(ensemble_models)} models")
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
                "models_loaded": list(ensemble_models.keys()),
                "model_count": len(ensemble_models),
                "file_name": file.filename if 'file' in locals() else "Unknown",
                "current_dir": os.getcwd()
            }
        }
        
        raise HTTPException(status_code=500, detail=error_response)

@app.post("/api/detect/single/{model_name}")
async def detect_food_single_model(model_name: str, file: UploadFile = File(...), confidence: float = 0.5):
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
        
        os.makedirs("temp", exist_ok=True)
        image_path = f"temp/{file.filename}"
        
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
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

@app.get("/api/models/info")
async def get_models_info():
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

@app.post("/api/detect/ensemble/custom")
async def detect_food_custom_ensemble(
    file: UploadFile = File(...), 
    confidence: float = 0.5,
    yolo11s_weight: float = 1.0,
    best_weight: float = 1.2,
    best_friged_weight: float = 1.1,
    iou_threshold: float = 0.5
):
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

@app.post("/api/analyze")
async def analyze_with_gemini(request_data: dict):
    try:
        print(f"\n=== Gemini Analysis API Called ===")
        
        text = request_data.get("text", "")
        detection_results = request_data.get("detection_results")
        
        print(f"Text length: {len(text)}")
        print(f"Has detection results: {detection_results is not None}")
        
        analysis = analyze_text_with_gemini(text, detection_results)
        print(f"Analysis complete")
        
        return {"analysis": analysis}
        
    except Exception as e:
        print(f"\nERROR in analyze_with_gemini:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini analysis error: {str(e)}")

@app.post("/api/fridge/save")
async def save_fridge_data(fridge_data: FridgeData):
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        print(f"\n=== Fridge Save API Called ===")
        print(f"User: {fridge_data.userId}")
        print(f"Ingredients: {fridge_data.totalTypes} types, {fridge_data.totalCount} items")
        
        ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]
        
        try:
            await client.admin.command('ping')
            print("MongoDB connection OK")
        except Exception as conn_err:
            print(f"MongoDB connection check failed: {conn_err}")
            raise HTTPException(status_code=503, detail="MongoDB connection unstable")
        
        current_time = datetime.now().isoformat()
        
        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "timestamp": fridge_data.timestamp,
            "totalCount": fridge_data.totalCount,
            "totalTypes": fridge_data.totalTypes,
            "analysisMethod": fridge_data.analysisMethod or "ensemble",
            "deviceInfo": fridge_data.deviceInfo or "web_app",
            "updatedAt": current_time
        }
        
        insert_only_document = {
            "createdAt": current_time
        }
        
        result = await fridge_collection.update_one(
            {"userId": fridge_data.userId},
            {
                "$set": update_document,
                "$setOnInsert": insert_only_document
            },
            upsert=True
        )
        
        print(f"Save complete. New document: {result.upserted_id is not None}")
        
        return {
            "success": True,
            "message": f"Fridge data successfully saved to {DB_NAME}.{COLLECTION_NAME}",
            "userId": fridge_data.userId,
            "totalTypes": fridge_data.totalTypes,
            "totalCount": fridge_data.totalCount,
            "isNew": result.upserted_id is not None,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "documentId": str(result.upserted_id) if result.upserted_id else "updated"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in save_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")

@app.post("/api/fridge/save-simple")
async def save_simple_fridge_data(fridge_data: SimpleFridgeData):
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        print(f"\n=== Simple Fridge Save API Called ===")
        print(f"User: {fridge_data.userId}")
        print(f"Ingredients: {len(fridge_data.ingredients)}")
        
        ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]
        
        try:
            await client.admin.command('ping')
            print("MongoDB connection OK")
        except Exception as conn_err:
            print(f"MongoDB connection check failed: {conn_err}")
            raise HTTPException(status_code=503, detail="MongoDB connection unstable")
        
        current_time = datetime.now().isoformat()
        
        insert_only_document = {
            "createdAt": current_time
        }
        
        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "updatedAt": current_time
        }
        
        result = await fridge_collection.update_one(
            {"userId": fridge_data.userId},
            {
                "$set": update_document,
                "$setOnInsert": insert_only_document
            },
            upsert=True
        )
        
        print(f"Simple save complete. New document: {result.upserted_id is not None}")
        
        return {
            "success": True,
            "message": f"Simplified fridge data successfully saved to {DB_NAME}.{COLLECTION_NAME}",
            "userId": fridge_data.userId,
            "totalIngredients": len(fridge_data.ingredients),
            "isNew": result.upserted_id is not None,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "documentId": str(result.upserted_id) if result.upserted_id else "updated",
                "format": "simplified"
            },
            "savedFields": ["userId", "ingredients", "createdAt"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in save_simple_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Simplified save error: {str(e)}")

@app.get("/api/fridge/load/{user_id}")
async def load_fridge_data(user_id: str):
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        print(f"\n=== Fridge Load API Called ===")
        print(f"User: {user_id}")
        
        fridge_data = await fridge_collection.find_one({"userId": user_id})
        
        if not fridge_data:
            print(f"No data found for user: {user_id}")
            return {
                "success": False,
                "message": "No saved fridge data found",
                "ingredients": [],
                "totalTypes": 0,
                "totalCount": 0,
                "storage": {
                    "database": DB_NAME,
                    "collection": COLLECTION_NAME
                }
            }
        
        fridge_data.pop("_id", None)
        
        print(f"Data loaded successfully")
        
        return {
            "success": True,
            "message": f"Data successfully loaded from {DB_NAME}.{COLLECTION_NAME}",
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            },
            **fridge_data
        }
    
    except Exception as e:
        print(f"\nERROR in load_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Load error: {str(e)}")

@app.get("/api/fridge/load-simple/{user_id}")
async def load_simple_fridge_data(user_id: str):
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        print(f"\n=== Simple Fridge Load API Called ===")
        print(f"User: {user_id}")
        
        fridge_data = await fridge_collection.find_one({"userId": user_id})
        
        if not fridge_data:
            print(f"No data found for user: {user_id}")
            return {
                "success": False,
                "message": "No saved fridge data found",
                "ingredients": []
            }
        
        fridge_data.pop("_id", None)
        
        simplified_data = {
            "userId": fridge_data.get("userId"),
            "ingredients": fridge_data.get("ingredients", []),
            "createdAt": fridge_data.get("createdAt")
        }
        
        print(f"Simple data loaded successfully")
        
        return {
            "success": True,
            "message": f"Simplified data successfully loaded from {DB_NAME}.{COLLECTION_NAME}",
            **simplified_data
        }
    
    except Exception as e:
        print(f"\nERROR in load_simple_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Simplified load error: {str(e)}")

@app.get("/api/fridge/load-v3/{user_id}")
async def load_v3_fridge_data(user_id: str):
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        print(f"\n=== V3 Fridge Load API Called ===")
        print(f"User: {user_id}")
        
        v3_collections = [
            f"{COLLECTION_NAME}_v3",
            f"{COLLECTION_NAME}_old", 
            "fridge_v3",
            "ingredients_v3",
            "food_data_v3"
        ]
        
        v3_data = None
        found_collection = None
        
        for collection_name in v3_collections:
            try:
                v3_collection = db[collection_name]
                data = await v3_collection.find_one({"userId": user_id})
                if data:
                    v3_data = data
                    found_collection = collection_name
                    break
            except Exception as e:
                print(f"Collection {collection_name} search failed: {e}")
                continue
        
        if not v3_data:
            current_data = await fridge_collection.find_one({"userId": user_id})
            if current_data:
                if "ingredients" in current_data and isinstance(current_data["ingredients"], list):
                    if current_data["ingredients"]:
                        print(f"Found data in current collection")
                        return {
                            "success": True,
                            "data": current_data["ingredients"],
                            "source": "current_format",
                            "collection": COLLECTION_NAME,
                            "message": "Returned current format data"
                        }
                
                v3_data = current_data
                found_collection = COLLECTION_NAME
        
        if not v3_data:
            return {
                "success": False,
                "message": "No v3 or previous format data found",
                "searched_collections": v3_collections + [COLLECTION_NAME]
            }
        
        v3_ingredients = None
        
        for field_name in ["ingredients", "data", "items", "foods", "detected_items"]:
            if field_name in v3_data and v3_data[field_name]:
                v3_ingredients = v3_data[field_name]
                break
        
        if not v3_ingredients:
            return {
                "success": False,
                "message": "No ingredient data found in v3 data",
                "available_fields": list(v3_data.keys()),
                "source_collection": found_collection
            }
        
        converted_data = convert_v3_to_current_format(v3_ingredients)
        
        print(f"V3 data conversion complete")
        print(f"  Original: {len(v3_ingredients)} items")
        print(f"  Converted: {len(converted_data)} items") 
        print(f"  Source: {found_collection}")
        
        return {
            "success": True,
            "data": converted_data,
            "source": "v3_migration",
            "collection": found_collection,
            "original_count": len(v3_ingredients),
            "converted_count": len(converted_data),
            "message": f"V3 data successfully converted ({found_collection})"
        }
        
    except Exception as e:
        print(f"\nERROR in load_v3_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"V3 data load error: {str(e)}")

@app.post("/api/fridge/migrate-v3/{user_id}")
async def migrate_v3_to_current(user_id: str):
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")
    
    try:
        print(f"\n=== V3 Migration API Called ===")
        print(f"User: {user_id}")
        
        v3_response = await load_v3_fridge_data(user_id)
        
        if not v3_response["success"]:
            return {
                "success": False,
                "message": "No v3 data to migrate",
                "details": v3_response
            }
        
        converted_data = v3_response["data"]
        
        current_time = datetime.now().isoformat()
        
        migration_document = {
            "userId": user_id,
            "ingredients": converted_data,
            "timestamp": current_time,
            "totalCount": sum(item["quantity"] for item in converted_data),
            "totalTypes": len(converted_data),
            "analysisMethod": "v3_migration",
            "deviceInfo": "migration_tool",
            "migrationInfo": {
                "sourceCollection": v3_response["collection"],
                "migrationDate": current_time,
                "originalCount": v3_response["original_count"],
                "convertedCount": v3_response["converted_count"]
            },
            "updatedAt": current_time,
            "createdAt": current_time
        }
        
        result = await fridge_collection.replace_one(
            {"userId": user_id},
            migration_document,
            upsert=True
        )
        
        print(f"V3 migration complete")
        print(f"  Converted items: {len(converted_data)}")
        print(f"  Save location: {DB_NAME}.{COLLECTION_NAME}")
        
        return {
            "success": True,
            "message": "V3 data successfully migrated to current format",
            "migrationInfo": {
                "userId": user_id,
                "sourceCollection": v3_response["collection"],
                "migratedItems": len(converted_data),
                "totalCount": migration_document["totalCount"],
                "totalTypes": migration_document["totalTypes"],
                "targetCollection": f"{DB_NAME}.{COLLECTION_NAME}",
                "migrationDate": current_time
            }
        }
        
    except Exception as e:
        print(f"\nERROR in migrate_v3_to_current:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")

@app.get("/health")
async def health_check():
    print(f"\n=== Health Check API Called ===")
    
    mongodb_status = "connected" if fridge_collection is not None else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0 - Enhanced OCR Inference + Web Search + 3-Model Ensemble - DEBUG",
        "features": [
            "3-Model YOLO Ensemble",
            "Enhanced OCR Inference with Pattern Matching",
            "Google Custom Search Integration", 
            "Ingredient Validation API",
            "MongoDB Storage",
            "V3 Data Migration",
            "Simple Save Format"
        ],
        "services": {
            "ensemble_models": {
                "target_models": ["yolo11s", "best", "best_friged"],
                "loaded_models": list(ensemble_models.keys()),
                "loaded_count": len(ensemble_models),
                "target_count": 3,
                "ensemble_ready": len(ensemble_models) > 1,
                "full_ensemble": len(ensemble_models) == 3
            },
            "mongodb": mongodb_status,
            "ocr": "configured" if os.environ.get('CLOVA_OCR_API_URL') else "not_configured",
            "gemini": "configured" if os.environ.get('GEMINI_API_KEY') else "not_configured",
            "google_search": "configured" if os.environ.get('GOOGLE_API_KEY') else "mock_mode",
            "enhanced_ocr": "available",
            "pattern_matching": "available",
            "web_search": "available",
            "v3_migration": "available",
            "simple_save": "available"
        },
        "mongodb_config": {
            "database": DB_NAME,
            "collection": COLLECTION_NAME,
            "uri": MONGODB_URI.replace("root:example", "***:***") if MONGODB_URI else None
        },
        "temp_dir_exists": os.path.exists("temp"),
        "missing_models": [name for name in ["yolo11s", "best", "best_friged"] if name not in ensemble_models],
        "enhanced_features": [
            "Pattern-based ingredient inference",
            "Google Custom Search integration",
            "Keyword extraction and summary",
            "Ingredient name validation API",
            "Enhanced debugging system"
        ],
        "debug_info": {
            "working_directory": os.getcwd(),
            "python_version": sys.version,
            "models_loaded": len(ensemble_models),
            "directories": {
                "models": os.path.exists("models"),
                "modules": os.path.exists("modules"),
                "temp": os.path.exists("temp")
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("STARTING ENHANCED FOOD DETECTION API - DEBUG VERSION")
    print("=" * 60)
    print(f"Server address: http://0.0.0.0:8080")
    print(f"API docs: http://0.0.0.0:8080/docs")
    print(f"Health check: http://0.0.0.0:8080/health")
    print(f"Target ensemble models: yolo11s.pt, best.pt, best_friged.pt")
    print(f"Loaded models: {list(ensemble_models.keys())} ({len(ensemble_models)}/3)")
    print(f"MongoDB connection: {'Success' if fridge_collection is not None else 'Failed'}")
    print(f"Save location: {DB_NAME}.{COLLECTION_NAME}")
    
    if len(ensemble_models) < 3:
        print(f"\n⚠️  WARNING: Only {len(ensemble_models)} of 3 models loaded")
        print("This will cause issues with ensemble detection!")
    
    if len(ensemble_models) == 0:
        print("\n❌ CRITICAL: No models loaded!")
        print("The /api/detect endpoint will return 500 errors!")
        print("\nTo fix this:")
        print("1. Create 'models' directory: mkdir models")
        print("2. Add model files: yolo11s.pt, best.pt, best_friged.pt")
        print("3. Create modules/yolo_detector.py with load_yolo_model function")
        print("4. Install dependencies: pip install ultralytics torch")
    
    print("\n" + "=" * 60)
    print("Server is starting...")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)