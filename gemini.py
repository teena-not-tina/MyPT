# 📁 cv-service/modules/gemini.py
import os
import requests
import json
import traceback

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def analyze_text_with_gemini(text, detection_results=None):
    """원본 Gemini 함수 (작동하던 버전 기반)"""
    if not text or text.strip() == "":
        print("분석할 텍스트가 없습니다.")
        return None
    
    try:
        print(f"Gemini 분석 시작 - 텍스트 길이: {len(text)}")
        print(f"API Key 존재: {bool(GEMINI_API_KEY)}")
        
        # 탐지 결과가 있으면 컨텍스트에 포함
        detection_context = ""
        if detection_results and len(detection_results) > 0:
            detected_classes = [det['class'] for det in detection_results if det['class'] != 'other']
            if detected_classes:
                detection_context = f"\n\n참고: 이미지에서 다음 식품들이 탐지되었습니다: {', '.join(detected_classes)}"
            else:
                detection_context = "\n\n참고: 이미지에서 알려진 식품이 탐지되지 않았습니다."
        
        # 기본 프롬프트
        prompt = f"""식품의 포장지를 OCR로 추출한 텍스트를 분석해서 어떤 식품인지 추론해주세요.

추출된 텍스트: {text}{detection_context}

분석 결과를 간단하고 명확하게 답변해주세요."""
        
        request_data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 200
            }
        }
        
        # API 요청 헤더
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        # API 요청 데이터를 JSON으로 직접 직렬화하여 인코딩 문제 방지
        json_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
        
        print("Gemini API 요청 전송 중...")
        
        # API 요청 보내기 (data 파라미터 사용)
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            data=json_data,
            timeout=30  # 30초 타임아웃
        )
        
        print(f"Gemini API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        inference_result = content['parts'][0]['text']
                        print(f"Gemini API 추론 결과: {inference_result}")
                        return inference_result
        
        print(f"Gemini API 오류 - 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        return None
        
    except requests.exceptions.Timeout:
        print("Gemini API 타임아웃 (30초)")
        return None
    except Exception as e:
        print(f"Gemini API 분석 중 오류 발생: {e}")
        print(f"오류 세부 정보: {type(e).__name__}, {str(e)}")
        traceback.print_exc()
        return None