# src/routes/chat.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.utils.comfyui_api import generate_image_from_comfyui
from src.config.db import get_mongo_collection
from pymongo import MongoClient  # 추가
import time
import traceback  # 추가
import threading  # 추가
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # 환경변수 로드

chat_bp = Blueprint('chat', __name__)

def restore_previous_image(user_id, image_data):
    """이전 이미を 30초 후에 복원하는 함수."""
    time.sleep(30)
    try:
        collection = get_mongo_collection('user_image')
        if collection is not None:
            collection.update_one(
                {'email': user_id},
                {
                    '$set': {
                        'food.image_data': image_data,
                        'food.updated_at': time.time()
                    }
                }
            )
            print(f"이전 이미지로 복원됨 (email: {user_id})")
    except Exception as e:
        print(f"이미지 복원 중 오류: {str(e)}")
        print(traceback.format_exc())

@chat_bp.route('/chat_and_generate', methods=['POST', 'OPTIONS'])
@cross_origin(
    origins=["http://localhost:3000", "http://localhost:3002"],
    methods=['POST', 'OPTIONS'],
    allow_headers=['Content-Type'],
    supports_credentials=True
)
def chat_and_generate():
    try:
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        data = request.get_json()
        user_input = data.get('message', '')
        user_id = data.get('user_id', 'default')

        print(f"받은 메시지: {user_input}")

        # GPT를 사용하여 한글 입력을 영어로 번역하고 프롬프트 생성
        client = OpenAI(api_key=api_key)
        
        # 음식에 대한 설명 생성
        food_description_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "음식의 특징을 한 문장으로 짧게 설명해주세요."},
                {"role": "user", "content": f"음식: {user_input}"}
            ]
        )
        
        food_description = food_description_response.choices[0].message.content
        
        # 이미지 생성을 위한 번역 및 프롬프트 생성
        translation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "한글로 입력된 음식 이름을 영어로 번역하고, 이미지 생성에 적합한 프롬프트를 생성해주세요."},
                {"role": "user", "content": f"음식: {user_input}"}
            ]
        )
        
        # 번역된 텍스트 추출
        translated_prompt = translation_response.choices[0].message.content
        print(f"번역된 프롬프트: {translated_prompt}")

        # 이미지 생성 전 메시지 응답
        initial_response = {
            "chat_response": f"{food_description}\n\n잠시만 기다려주세요, 관련된 캐릭터를 생성하고 있습니다...",
            "profile_image_b64": None,
            "status": "generating"
        }
        print("이미지 생성 시작...")

        # 이미지 생성 로직
        image_base64 = generate_image_from_comfyui(translated_prompt, user_id)
        
        # 캐릭터 설명 생성
        character_description_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "이 음식의 어떤 특징이 캐릭터에 반영되었는지 10단어 이내로 설명해주세요."},
                {"role": "user", "content": f"음식: {user_input}"}
            ]
        )
        
        character_description = character_description_response.choices[0].message.content
        
        # 최종 응답
        return jsonify({
            "chat_response": f"🍽️ {food_description}\n\n✨ {character_description}",
            "profile_image_b64": image_base64,
            "status": "completed"
        })

    except ValueError as ve:
        print(f"설정 오류: {str(ve)}")
        return jsonify({"error": str(ve)}), 500
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/test_env', methods=['GET'])
def test_env():
    api_key = os.getenv('OPENAI_API_KEY')
    return jsonify({
        "api_key_set": api_key is not None
    })
