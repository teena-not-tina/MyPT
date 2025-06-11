# ocr_routes.py - OCR 관련 라우터들

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import traceback

# 라우터 생성
ocr_router = APIRouter()

class IngredientValidationRequest(BaseModel):
    name: str
    ocr_context: Optional[str] = ""
    use_web_search: Optional[bool] = True

@ocr_router.post("/api/ocr")
async def extract_ocr_text(file: UploadFile = File(...)):
    """OCR 텍스트 추출 API - main.py에서 그대로 이동"""
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
        from modules.ocr_processor import extract_text_with_ocr
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

@ocr_router.post("/api/ocr/enhanced")
async def enhanced_ocr_analysis(file: UploadFile = File(...)):
    """향상된 OCR 분석 API - main.py에서 그대로 이동"""
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
        from modules.ocr_processor import extract_text_with_ocr
        ocr_text = extract_text_with_ocr(image_path)
        print(f"Extracted text: {ocr_text}")
        
        print(f"Step 2: Enhanced OCR inference")
        from main import enhanced_ocr_inference, extract_keywords_from_ocr, summarize_ocr_text
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

@ocr_router.post("/api/ingredient/validate")
async def validate_ingredient_name(request: IngredientValidationRequest):
    """재료명 검증 API - main.py에서 그대로 이동"""
    try:
        print(f"\n=== Ingredient Validation API Called ===")
        print(f"Name: {request.name}")
        
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Ingredient name required")
        
        from main import enhanced_ocr_inference, infer_ingredient_from_patterns
        
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