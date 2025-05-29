# 📁 cv-service/modules/ocr_processor.py
import requests
import json
import traceback
import os

CLOVA_OCR_API_URL = os.environ.get("CLOVA_OCR_API_URL")
CLOVA_SECRET_KEY = os.environ.get("CLOVA_SECRET_KEY")

def extract_text_with_ocr(image_path):
    """원본 OCR 함수 (작동하던 버전 기반)"""
    try:
        print(f"OCR 시작: {image_path}")
        print(f"API URL: {CLOVA_OCR_API_URL}")
        print(f"Secret Key 존재: {bool(CLOVA_SECRET_KEY)}")
        
        request_json = {
            'images': [
                {
                    'format': 'jpg',
                    'name': 'food'
                }
            ],
            'requestId': 'food-ocr-request',
            'version': 'V2',
            'timestamp': 0
        }

        # JSON을 UTF-8로 인코딩
        payload = {'message': json.dumps(request_json, ensure_ascii=False).encode('UTF-8')}
        
        # 이미지 파일 열기
        with open(image_path, 'rb') as f:
            file_data = f.read()
            print(f"이미지 파일 크기: {len(file_data)} bytes")
            
        # API 요청 헤더
        headers = {'X-OCR-SECRET': CLOVA_SECRET_KEY}
        
        # 멀티파트 폼 형식으로 데이터 생성
        files = [
            ('file', ('food.jpg', file_data, 'image/jpeg'))
        ]
        
        print("OCR API 요청 전송 중...")
        
        # API 요청 보내기 (타임아웃 추가)
        response = requests.post(
            CLOVA_OCR_API_URL, 
            headers=headers, 
            data=payload, 
            files=files,
            timeout=60  # 60초 타임아웃
        )
        
        print(f"OCR API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("OCR API 응답 성공")
            
            # OCR 결과에서 텍스트 추출
            extracted_text = []
            if 'images' in result and len(result['images']) > 0:
                if 'fields' in result['images'][0]:
                    for field in result['images'][0]['fields']:
                        if 'inferText' in field:
                            extracted_text.append(field['inferText'])
            
            full_text = ' '.join(extracted_text)
            print(f"OCR 추출 텍스트: {full_text}")
            return full_text
        else:
            print(f"OCR API 오류 - 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("OCR API 타임아웃 (60초)")
        return None
    except Exception as e:
        print(f"OCR 텍스트 추출 중 오류 발생: {e}")
        print(f"오류 세부 정보: {type(e).__name__}, {str(e)}")
        traceback.print_exc()
        return None