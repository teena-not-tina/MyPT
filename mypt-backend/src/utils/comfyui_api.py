import os
import requests
import json
import time
import base64
import shutil
from dotenv import load_dotenv
from pymongo import MongoClient

MONGO_URI = "mongodb://root:example@192.168.0.199:27017/?authSource=admin"
DB_NAME = "test"

def save_food_image(user_id, image_base64):
    try:
        client = MongoClient(MONGO_URI)
        db = client["test"]  # test 데이터베이스 사용
        collection = db.user_image  # user_image 컬렉션
        
        # 이미지 데이터 저장
        result = collection.update_one(
            {'user_id': user_id},  # user_id로 문서 찾기
            {
                '$set': {
                    'food': {  # food 필드에 저장
                        'image_data': image_base64,
                        'created_at': time.time()
                    }
                }
            },
            upsert=True  # 문서가 없으면 새로 생성
        )
        print(f"MongoDB test.user_image 컬렉션에 이미지 저장 성공 (user_id: {user_id})")
        return True
    except Exception as e:
        print(f"MongoDB 저장 오류: {str(e)}")
        return False

def generate_image_from_comfyui(prompt, user_id="test@mail.com"):
    try:
        COMFYUI_API_URL = os.getenv('COMFYUI_API_URL', 'http://localhost:8188')
        start_time = time.time()
        
        # ComfyUI 출력 경로와 백엔드 출력 경로 설정
        comfyui_output = os.path.abspath(r'C:\Users\702-18\ComfyUI_Stable\ComfyUI_windows_portable\ComfyUI\output')
        backend_output = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output'))
        
        # 출력 디렉토리가 존재하는지 확인하고 없으면 생성
        os.makedirs(comfyui_output, exist_ok=True)
        os.makedirs(backend_output, exist_ok=True)
        
        print(f"ComfyUI 출력 경로: {comfyui_output}")
        print(f"백엔드 출력 경로: {backend_output}")
        
        # 워크플로우 파일 로드
        workflow_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workflows', 'my_comfyui_workflow.json')
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # 프롬프트 조합
        food_prompt = f"cute chibi character with {prompt} body, small limbs, big head, full body"
        
        # 긍정적 프롬프트 강화
        positive_prompt = f"""
            masterpiece, best quality, highly detailed, 
            cute chibi character, kawaii, big eyes, 
            {prompt} body, {prompt} themed, 
            food character, delicious looking,
            small limbs, big head, full body, 
            chibi proportions, food mascot,
            vibrant colors, appetizing
        """
        
        # 부정적 프롬프트 강화
        negative_prompt = """
            ugly, deformed, blurry, bad anatomy, 
            bad proportions, poorly drawn, 
            text, watermark, logo, 
            extra limbs, missing limbs,
            low quality, worst quality,
            mutated, distorted, disfigured
        """
        
        # 워크플로우에 프롬프트 적용
        workflow["2"]["inputs"]["text"] = positive_prompt.strip().replace('\n', ' ')
        workflow["3"]["inputs"]["text"] = negative_prompt.strip().replace('\n', ' ')
        
        # 랜덤 시드 설정으로 다양한 결과 생성
        workflow["5"]["inputs"]["seed"] = int(time.time()) % 1000000000
        
        print(f"적용된 긍정 프롬프트: {positive_prompt.strip()}")
        print(f"적용된 부정 프롬프트: {negative_prompt.strip()}")
        
        # 워크플로우 실행
        response = requests.post(f"{COMFYUI_API_URL}/prompt", json={
            "prompt": workflow
        })
        
        if not response.ok:
            raise Exception(f"ComfyUI API 오류: {response.status_code}")
            
        prompt_id = response.json()['prompt_id']
        print(f"워크플로우 시작됨 - 프롬프트 ID: {prompt_id}")
        
        # 진행 상태 표시 변수
        start_time = time.time()
        
        # 이미지 생성 대기 및 복사
        max_attempts = 180
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{COMFYUI_API_URL}/history/{prompt_id}")
                if not response.ok:
                    print(f"History API 응답 오류: {response.status_code}")
                    time.sleep(1)
                    continue

                history = response.json()
                
                if prompt_id in history and 'outputs' in history[prompt_id]:
                    outputs = history[prompt_id]['outputs']
                    
                    # ComfyUI의 output 디렉토리 스캔
                    output_files = os.listdir(comfyui_output)
                    if output_files:  # 파일이 있으면
                        latest_file = max([f for f in output_files if f.endswith('.png')],
                                        key=lambda x: os.path.getctime(os.path.join(comfyui_output, x)))
                        
                        comfyui_image_path = os.path.join(comfyui_output, latest_file)
                        backend_image_path = os.path.join(backend_output, latest_file)
                        
                        print(f"최신 이미지 파일 발견: {comfyui_image_path}")
                        
                        # 이미지 복사
                        shutil.copy2(comfyui_image_path, backend_image_path)
                        print(f"이미지 복사 완료: {backend_image_path}")
                        
                        # 이미지를 base64로 변환
                        with open(backend_image_path, 'rb') as image_file:
                            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                            
                            # MongoDB에 저장
                            if save_food_image(user_id, image_base64):
                                elapsed_time = time.time() - start_time
                                print(f"이미지 생성 및 저장 완료! 소요 시간: {elapsed_time:.1f}초")
                                return image_base64
                    
            except Exception as e:
                print(f"이미지 처리 중 오류 발생: {str(e)}")
                print(f"오류 발생 위치:\n{traceback.format_exc()}")
            
            print(f"이미지 생성 대기 중... {attempt+1}/{max_attempts}초")
            time.sleep(1)
            
        raise Exception("이미지 생성 시간 초과")
            
    except Exception as e:
        print(f"전체 프로세스 오류: {str(e)}")
        raise e
