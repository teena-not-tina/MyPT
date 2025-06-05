# src/routes/chat.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.utils.comfyui_api import generate_image_from_comfyui
from src.config.db import get_mongo_collection
from pymongo import MongoClient  # 추가
import time
import traceback  # 추가

chat_bp = Blueprint('chat', __name__)

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

        print(f"받은 메시지: {user_input}")  # 디버그용 로그 추가

        # 이미지 생성 시도
        try:
            image_base64 = generate_image_from_comfyui(user_input, user_id)
        except Exception as e:
            print(f"ComfyUI 이미지 생성 오류: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': '이미지 생성 중 오류가 발생했습니다.'
            }), 500

        if image_base64:
            try:
                # MongoDB 컬렉션 가져오기
                collection = get_mongo_collection()
                if collection:
                    # 이미지 저장
                    collection.update_one(
                        {'user_id': user_id},
                        {
                            '$set': {
                                'images.food': {
                                    'image_data': image_base64,
                                    'created_at': time.time()
                                }
                            }
                        },
                        upsert=True
                    )
                    print(f"이미지가 MongoDB에 저장됨 (user_id: {user_id})")
            except Exception as e:
                print(f"MongoDB 저장 오류: {str(e)}")
                print(traceback.format_exc())
        
        return jsonify({
            'success': True,
            'chat_response': '식단 이미지가 생성되었습니다.',
            'profile_image_b64': image_base64
        })

    except Exception as e:
        print(f"전체 처리 오류: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': '서버 처리 중 오류가 발생했습니다.'
        }), 500
