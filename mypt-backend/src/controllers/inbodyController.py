# src/controllers/inbodyController.py (백엔드 파일)
from flask import request, jsonify, Blueprint
from src.config.db import get_mongo_collection

# TODO: 인증 미들웨어 추가 필요 (현재는 누구나 접근 가능)
# 예시: JWT 토큰 확인 후 사용자 ID 추출하여 Inbody 데이터에 연결

def submit_inbody_data():
    data = request.get_json()
    
    # 필수 필드 유효성 검사
    required_fields = ['height', 'weight', 'bodyFat', 'muscleMass']
    for field in required_fields:
        if field not in data or not isinstance(data[field], (int, float)):
            return jsonify({"message": f"'{field}' is required and must be a number."}), 400

    height = data.get('height')
    weight = data.get('weight')
    body_fat = data.get('bodyFat')
    muscle_mass = data.get('muscleMass')

    # TODO: 실제 사용자 ID를 가져와서 저장해야 합니다.
    # 현재는 더미 사용자 ID를 사용합니다.
    # 로그인 토큰에서 사용자 ID를 추출하는 로직이 추가되어야 합니다.
    user_id = "dummy_user_id_123" # 실제 사용자 ID로 대체 필요

    inbody_collection = get_mongo_collection('inbody') # 'inbody' 컬렉션에 저장
    
    # 저장할 데이터 객체
    inbody_record = {
        'user_id': user_id,
        'height': height,
        'weight': weight,
        'bodyFat': body_fat,
        'muscleMass': muscle_mass,
        'timestamp': datetime.utcnow() # 데이터 저장 시간 기록
    }

    try:
        result = inbody_collection.insert_one(inbody_record)
        return jsonify({"message": "Inbody data submitted successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"message": "Failed to save inbody data", "error": str(e)}), 500

# 추가적으로 사용자별 인바디 데이터를 조회하는 함수를 만들 수 있습니다.
def get_user_inbody_data(user_id):
    inbody_collection = get_mongo_collection('inbody')
    # 특정 사용자의 최신 인바디 데이터 (예시)
    latest_inbody = inbody_collection.find({'user_id': user_id}).sort('timestamp', -1).limit(1)
    if latest_inbody:
        # ObjectId를 문자열로 변환하여 JSON 직렬화 가능하게 함
        latest_inbody['_id'] = str(latest_inbody['_id'])
        return jsonify(latest_inbody), 200
    return jsonify({"message": "No inbody data found for this user"}), 404

# 주의: datetime 모듈이 필요합니다.
from datetime import datetime