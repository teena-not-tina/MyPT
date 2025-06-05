# src/routes/chat.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.utils.comfyui_api import generate_image_from_comfyui
from src.config.db import get_mongo_collection
from pymongo import MongoClient  # 추가
import time
import traceback  # 추가
import threading  # 추가

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
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        user_id = data.get('user_id', 'default')

        print(f"받은 메시지: {user_input}")

        try:
            # 기존 이미지 확인
            collection = get_mongo_collection('user_image')
            existing_doc = collection.find_one({'email': user_id})
            default_image = None
            
            if existing_doc and 'food' in existing_doc:
                default_image = existing_doc['food']['image_data']

            # 새 이미지 생성
            image_base64 = generate_image_from_comfyui(user_input, user_id)
            
            if collection is not None:
                # 이미지 저장
                collection.update_one(
                    {'email': user_id},
                    {
                        '$set': {
                            'food': {
                                'image_data': image_base64,
                                'created_at': time.time(),
                                'updated_at': time.time(),
                                'previous_image': default_image  # 이전 이미지 저장
                            }
                        }
                    },
                    upsert=True
                )
                print(f"이미지가 MongoDB에 저장됨 (email: {user_id})")

                # 30초 후 이전 이미지로 복원하는 스레드 시작
                if default_image:
                    restore_thread = threading.Thread(
                        target=restore_previous_image,
                        args=(user_id, default_image)
                    )
                    restore_thread.daemon = True
                    restore_thread.start()

            return jsonify({
                'success': True,
                'chat_response': '이미지가 생성되었습니다.',
                'profile_image_b64': image_base64
            })

        except Exception as e:
            print(f"처리 중 오류: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': '이미지 처리 중 오류가 발생했습니다.'
            }), 500

    except Exception as e:
        print(f"전체 처리 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }), 500
