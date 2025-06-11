# [🍽️ 터미널 음식 캐릭터 생성 및 저장 프로그램]
import os
import requests
import json
import time
import base64
import threading
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS 추가

# [🔗 MongoDB 연결 정보]
MONGO_URI = "mongodb://root:example@192.168.0.199:27017/?authSource=admin"
DB_NAME = "test"

app = Flask(__name__)
CORS(app)  # CORS 활성화

def delete_food_data(user_id):
    # [⏳ 60초 후 food 필드 삭제]
    try:
        time.sleep(60)
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db.user_image
        result = collection.update_one(
            {'email': user_id},
            {'$unset': {'food': 1}}
        )
        if result.modified_count > 0:
            print(f"MongoDB: food 데이터 삭제 완료 (email: {user_id})")
    except Exception as e:
        print(f"MongoDB 삭제 오류: {str(e)}")
    finally:
        client.close()

def save_food_image(user_id, image_base64, previous_image=None):
    # [💾 이미지 MongoDB 저장 및 60초 후 삭제 스레드]
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db.user_image
        current_time = datetime.now(timezone.utc)
        update_data = {
            'food': {
                'image_data': image_base64,
                'created_at': current_time,
                'updated_at': current_time,
                'expires_at': current_time + timedelta(seconds=60)
            }
        }
        if previous_image:
            update_data['food']['previous_image'] = previous_image
        result = collection.update_one(
            {'email': user_id},
            {'$set': update_data},
            upsert=True
        )
        delete_thread = threading.Thread(
            target=delete_food_data,
            args=(user_id,)
        )
        delete_thread.daemon = True
        delete_thread.start()
        print(f"MongoDB: 이미지 {'업데이트' if result.matched_count else '저장'} 완료 (email: {user_id}, 60초 후 삭제 예정)")
        return True
    except Exception as e:
        print(f"MongoDB 저장 오류: {str(e)}")
        return False
    finally:
        client.close()

def generate_image_from_comfyui(prompt, user_id="test@mail.com"):
    # [🎨 ComfyUI로 이미지 생성 및 저장]
    try:
        COMFYUI_API_URL = os.getenv('COMFYUI_API_URL', 'http://localhost:8188')
        start_time = time.time()
        comfyui_output = os.path.abspath(r'C:\Users\702-18\ComfyUI_Stable\ComfyUI_windows_portable\ComfyUI\output')
        print(f"이미지 생성 시작 - 프롬프트: {prompt}")
        # [📋 JSON 파일에서 워크플로우 로드]
        workflow_path = os.path.join(os.path.dirname(__file__), 'workflows', 'my_comfyui_workflow.json')
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        food_prompt = f"""
            (masterpiece:1.2), (best quality:1.2), ultra detailed,
            cute SD chibi character made of {prompt}, 
            {prompt} as main theme, {prompt}-shaped body parts,
            melted {prompt} texture skin, {prompt} details,
            food mascot character, appetizing and kawaii,
            anime style, big head small body,
            professional food photo lighting
        """
        negative_prompt = """
            ugly, deformed, disfigured, mutated, blurry,
            bad anatomy, incorrect proportions, 
            low quality, worst quality, 
            text, watermark, signature, copyright,
            extra limbs, missing limbs, floating limbs,
            malformed hands, duplicate bodies, multiple characters,
            poorly drawn face, bad perspective,
            oversaturated, overexposed
        """
        workflow["2"]["inputs"]["text"] = food_prompt.strip().replace('\n', ' ')
        workflow["3"]["inputs"]["text"] = negative_prompt.strip().replace('\n', ' ')
        workflow["5"]["inputs"].update({
            "seed": int(time.time()) % 1000000000,
            "steps": 30,
            "cfg": 8.0,
            "sampler_name": "euler_ancestral",
            "scheduler": "karras",
            "denoise": 0.5
        })
        print(f"[사용된 프롬프트]: {food_prompt.strip()}")
        print(f"[사용된 네거티브 프롬프트]: {negative_prompt.strip()}")
        response = requests.post(f"{COMFYUI_API_URL}/prompt", json={"prompt": workflow})
        if not response.ok:
            raise Exception(f"ComfyUI API 오류: {response.status_code}")
        prompt_id = response.json()['prompt_id']
        print(f"프롬프트 전송 완료. ID: {prompt_id}")
        max_attempts = 300
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{COMFYUI_API_URL}/history/{prompt_id}")
                if not response.ok:
                    print(f"History API 응답 오류: {response.status_code}")
                    time.sleep(1)
                    continue
                history = response.json()
                if prompt_id in history and 'outputs' in history[prompt_id]:
                    try:
                        client = MongoClient(MONGO_URI)
                        db = client[DB_NAME]
                        collection = db.user_image
                        user_doc = collection.find_one({'email': user_id})
                        previous_image = None
                        if user_doc and 'food' in user_doc:
                            previous_image = user_doc['food']['image_data']
                            print(f"기존 이미지 데이터 찾음 (email: {user_id})")
                    except Exception as db_error:
                        print(f"MongoDB 조회 오류: {str(db_error)}")
                    finally:
                        client.close()
                    output_files = os.listdir(comfyui_output)
                    if output_files:
                        latest_file = max([f for f in output_files if f.endswith('.png')],
                                        key=lambda x: os.path.getctime(os.path.join(comfyui_output, x)))
                        with open(os.path.join(comfyui_output, latest_file), 'rb') as image_file:
                            new_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                            if save_food_image(user_id, new_image_base64, previous_image):
                                elapsed_time = time.time() - start_time
                                print(f"이미지 생성 및 저장 완료! 소요 시간: {elapsed_time:.1f}초")
                                return new_image_base64
            except Exception as e:
                print(f"이미지 처리 중 오류: {str(e)}")
            print(f"이미지 생성 대기 중... {attempt+1}/{max_attempts}초")
            time.sleep(1)
        raise Exception("이미지 생성 시간 초과")
    except Exception as e:
        print(f"전체 프로세스 오류: {str(e)}")
        raise e

@app.route('/generate-food', methods=['POST'])
def generate_food():
    try:
        data = request.get_json()
        if not data or 'food' not in data:
            return jsonify({'error': 'food 파라미터가 필요합니다'}), 400
        
        food = data.get('food')
        print(f"API 요청 받음: {food}")
        
        image_base64 = generate_image_from_comfyui(food)
        return jsonify({'image_base64': image_base64})
    except Exception as e:
        print(f"API 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Food Generator API is running'})

def main():
    # [📝 사용자 입력 → 이미지 생성 → DB 저장 전체 흐름]
    try:
        while True:
            food_name = input("\n생성할 음식 이름을 입력하세요 (종료하려면 'q' 입력): ")
            if food_name.lower() == 'q':
                print("프로그램을 종료합니다.")
                break
            if not food_name.strip():
                print("음식 이름을 입력해주세요!")
                continue
            print(f"\n'{food_name}' 캐릭터 이미지 생성 중...")
            try:
                image_base64 = generate_image_from_comfyui(food_name)
                if image_base64:
                    print("✨ 이미지 생성 성공!")
                    print("💾 MongoDB(test.user_image.food)에 저장되었습니다.")
                    print("⏳ 60초 후 자동으로 삭제됩니다.")
                else:
                    print("❌ 이미지 생성 실패")
            except Exception as e:
                print(f"오류 발생: {str(e)}")
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {str(e)}")

if __name__ == "__main__":
    # 명령행 인자 확인
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        print("🚀 Flask 서버 모드로 시작합니다...")
        print("📍 API 엔드포인트: http://localhost:5000/generate-food")
        print("🏥 헬스체크: http://localhost:5000/health")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("🎮 터미널 모드로 시작합니다...")
        print("💡 Flask 서버로 실행하려면: python food_generator.py --server")
        main()