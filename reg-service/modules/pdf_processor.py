import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import easyocr
import pytesseract
import os
import tempfile
from typing import List, Tuple, Optional

class PDFProcessor:
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['ko', 'en'], gpu=True)  # CUDA 사용
        
    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        '''PDF에서 이미지 추출'''
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 페이지를 이미지로 변환 (고해상도)
                mat = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2배 확대
                img_data = mat.tobytes("png")
                
                # numpy 배열로 변환
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is not None:
                    images.append(img)
            
            doc.close()
            return images
            
        except Exception as e:
            raise RuntimeError(f"PDF 이미지 추출 실패: {str(e)}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        '''이미지 전처리 (OCR 정확도 향상)'''
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # 이진화
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def extract_text_with_easyocr(self, image: np.ndarray) -> str:
        '''EasyOCR을 사용한 텍스트 추출'''
        try:
            results = self.ocr_reader.readtext(image, detail=0)
            return " ".join(results)
        except Exception as e:
            print(f"EasyOCR 오류: {e}")
            return ""
    
    def extract_text_with_tesseract(self, image: np.ndarray) -> str:
        '''Tesseract를 사용한 텍스트 추출'''
        try:
            # PIL Image로 변환
            pil_image = Image.fromarray(image)
            text = pytesseract.image_to_string(
                pil_image, 
                lang='kor+eng',
                config='--oem 3 --psm 6'
            )
            return text
        except Exception as e:
            print(f"Tesseract 오류: {e}")
            return ""
    
    def process_pdf(self, pdf_path: str) -> str:
        '''PDF 전체 처리 파이프라인'''
        all_text = []
        
        # PDF에서 이미지 추출
        images = self.extract_images_from_pdf(pdf_path)
        
        for i, image in enumerate(images):
            print(f"페이지 {i+1} 처리 중...")
            
            # 이미지 전처리
            processed_img = self.preprocess_image(image)
            
            # 두 가지 OCR 방법 시도
            text_easyocr = self.extract_text_with_easyocr(processed_img)
            text_tesseract = self.extract_text_with_tesseract(processed_img)
            
            # 더 긴 텍스트 선택 (일반적으로 더 정확함)
            if len(text_easyocr) > len(text_tesseract):
                page_text = text_easyocr
            else:
                page_text = text_tesseract
            
            if page_text.strip():
                all_text.append(f"=== 페이지 {i+1} ===\\n{page_text}")
        
        return "\\n\\n".join(all_text)