# src/middlewares/authMiddleware.py (인증 미들웨어)
from flask import request, jsonify
# import jwt # JWT 라이브러리 필요 시
# from src.config.index import config # 설정 가져오기

def protect_route(f):
    # 이 함수는 JWT 토큰을 검증하여 보호된 라우트에 대한 접근을 제어합니다.
    # 예시:
    # @app.route('/protected')
    # @protect_route
    # def protected_resource():
    #     return jsonify({"message": "You accessed a protected resource!"})
    def wrapper(*args, **kwargs):
        # if 'Authorization' not in request.headers:
        #     return jsonify({'message': 'Authorization token missing'}), 401
        # token = request.headers['Authorization'].split(' ')[1]
        # try:
        #     data = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
        #     request.user = data['user_id'] # 사용자 ID를 request 객체에 추가
        # except Exception as e:
        #     return jsonify({'message': 'Token is invalid or expired'}), 401
        return f(*args, **kwargs)
    return wrapper
