# src/controllers/authController.py (인증 로직)
from src.models.User import User  # 경로 확인
# from src.utils.passwordHasher import hash_password, check_password # 필요 시 임포트
from src.config.db import get_mongo_collection # MongoDB 컬렉션 가져오기 예시
from werkzeug.security import generate_password_hash, check_password_hash # Flask 내장 해싱
from flask import Flask, request, jsonify # jsonify를 여기에 추가합니다.

def register_user(email, password):
    try:
        # 이미 존재하는 이메일인지 확인
        if User.find_by_email(email):
            return jsonify({"error": "이미 존재하는 이메일입니다"}), 400
            
        # 새 사용자 생성
        user = User(email=email, password_hash=password)
        user.save()
        
        return jsonify({"message": "회원가입이 성공적으로 완료되었습니다"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def authenticate_user(email, password):
    try:
        user = User.find_by_email(email)
        
        if not user:
            return jsonify({"error": "존재하지 않는 이메일입니다"}), 404
            
        if user['password'] != password:
            return jsonify({"error": "비밀번호가 일치하지 않습니다"}), 401
            
        return jsonify({
            "message": "로그인 성공",
            "user": {
                "email": user['email']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 다른 인증 로직을 여기에 추가합니다.
