# modules/ocr_processor.py
import requests
import json
import traceback
import os

CLOVA_OCR_API_URL = os.environ.get("CLOVA_OCR_API_URL")
CLOVA_SECRET_KEY = os.environ.get("CLOVA_SECRET_KEY")

def extract_text_with_ocr(image_path):
    """CLOVA OCR API를 사용한 텍스트 추출"""
    try:
        print(f"📄 OCR 시작: {image_path}")
        print(f"🔗 API URL: {CLOVA_OCR_API_URL}")
        print(f"🔑 Secret Key 존재: {bool(CLOVA_SECRET_KEY)}")
        
        # 환경 변수 확인
        if not CLOVA_OCR_API_URL or not CLOVA_SECRET_KEY:
            print("❌ CLOVA OCR API 설정이 없습니다")
            print("   환경 변수를 확인하세요: CLOVA_OCR_API_URL, CLOVA_SECRET_KEY")
            return None
        
        # 이미지 파일 존재 확인
        if not os.path.exists(image_path):
            print(f"❌ 이미지 파일이 없습니다: {image_path}")
            return None
        
        # 요청 JSON 구성
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
        
        # 이미지 파일 읽기
        with open(image_path, 'rb') as f:
            file_data = f.read()
            print(f"📊 이미지 파일 크기: {len(file_data)} bytes")
            
        # API 요청 헤더
        headers = {'X-OCR-SECRET': CLOVA_SECRET_KEY}
        
        # 멀티파트 폼 형식으로 데이터 생성
        files = [
            ('file', ('food.jpg', file_data, 'image/jpeg'))
        ]
        
        print("📤 OCR API 요청 전송 중...")
        
        # API 요청 보내기 (타임아웃 추가)
        response = requests.post(
            CLOVA_OCR_API_URL, 
            headers=headers, 
            data=payload, 
            files=files,
            timeout=60  # 60초 타임아웃
        )
        
        print(f"📥 OCR API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OCR API 응답 성공")
            
            # OCR 결과에서 텍스트 추출
            extracted_text = []
            if 'images' in result and len(result['images']) > 0:
                image_result = result['images'][0]
                
                if 'fields' in image_result:
                    print(f"📝 감지된 텍스트 필드 수: {len(image_result['fields'])}")
                    
                    for i, field in enumerate(image_result['fields']):
                        if 'inferText' in field:
                            text = field['inferText']
                            confidence = field.get('inferConfidence', 0)
                            print(f"   {i+1}. {text} (신뢰도: {confidence:.3f})")
                            extracted_text.append(text)
                else:
                    print("📝 인식된 텍스트 필드가 없습니다")
            
            full_text = ' '.join(extracted_text)
            print(f"📄 OCR 추출 완료: {len(full_text)}자")
            print(f"📝 추출된 텍스트: {full_text}")
            
            return full_text if full_text.strip() else None
            
        else:
            print(f"❌ OCR API 오류 - 상태 코드: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📋 오류 상세: {error_detail}")
            except:
                print(f"📋 응답 내용: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ OCR API 타임아웃 (60초)")
        return None
    except requests.exceptions.ConnectionError:
        print("🌐 OCR API 연결 오류")
        return None
    except requests.exceptions.RequestException as e:
        print(f"📡 OCR API 요청 오류: {e}")
        return None
    except FileNotFoundError:
        print(f"📂 이미지 파일을 찾을 수 없습니다: {image_path}")
        return None
    except Exception as e:
        print(f"❌ OCR 텍스트 추출 중 예상치 못한 오류: {e}")
        print(f"🔍 오류 세부 정보: {type(e).__name__}, {str(e)}")
        traceback.print_exc()
        return None

def test_ocr_setup():
    """OCR 설정 테스트"""
    print("🧪 OCR 설정 테스트")
    print(f"   CLOVA_OCR_API_URL: {bool(CLOVA_OCR_API_URL)}")
    print(f"   CLOVA_SECRET_KEY: {bool(CLOVA_SECRET_KEY)}")
    
    if CLOVA_OCR_API_URL and CLOVA_SECRET_KEY:
        print("✅ OCR 설정이 완료되었습니다")
        return True
    else:
        print("❌ OCR 설정이 누락되었습니다")
        print("   .env 파일에 다음을 추가하세요:")
        print("   CLOVA_OCR_API_URL=your_api_url")
        print("   CLOVA_SECRET_KEY=your_secret_key")
        return False

if __name__ == "__main__":
    # 테스트 코드
    print("🧪 OCR 프로세서 모듈 테스트")
    
    # 설정 테스트
    test_ocr_setup()
    
    # 테스트 이미지가 있다면 OCR 테스트
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        print(f"🖼️ 테스트 이미지로 OCR 테스트: {test_image}")
        result = extract_text_with_ocr(test_image)
        if result:
            print(f"✅ OCR 테스트 성공: {result}")
        else:
            print("❌ OCR 테스트 실패")
    else:
        print("❌ 테스트 이미지가 없습니다")