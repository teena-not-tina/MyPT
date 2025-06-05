# src/routes/auth.py (인증 관련 라우트)
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from src.config.db import get_mongo_collection
from datetime import datetime
import time

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': '이메일과 비밀번호는 필수입니다.'}), 400

        users = get_mongo_collection('users')
        
        # 이메일 중복 체크
        if users.find_one({'email': email}):
            return jsonify({'error': '이미 존재하는 이메일입니다.'}), 400

        # 비밀번호 해시화 및 사용자 저장
        user_data = {
            'email': email,
            'password': generate_password_hash(password),
            'created_at': time.time()
        }
        
        users.insert_one(user_data)
        print(f"새 사용자 등록: {email}")
        
        return jsonify({
            'message': '회원가입이 완료되었습니다.',
            'success': True
        }), 201

    except Exception as e:
        print(f"회원가입 오류: {str(e)}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': '이메일과 비밀번호는 필수입니다.'}), 400

        # users 컬렉션 가져오기
        users = get_mongo_collection('users')
        
        # MongoDB 연결 확인
        try:
            user = users.find_one({'email': email})
        except Exception as db_error:
            print(f"데이터베이스 조회 오류: {str(db_error)}")
            return jsonify({'error': '데이터베이스 연결 오류'}), 500

        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({'error': '비밀번호가 일치하지 않습니다.'}), 401

        return jsonify({
            'success': True,
            'user': {
                'email': user['email'],
                'id': str(user['_id'])
            }
        })

    except Exception as e:
        print(f"로그인 오류: {str(e)}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500

# 다른 인증 관련 라우트를 여기에 추가합니다.
