# src/routes/inbody.py (백엔드 파일)
from flask import Blueprint, request
from src.controllers.inbodyController import submit_inbody_data # 컨트롤러 임포트

inbody_bp = Blueprint('inbody', __name__)

# 인바디 정보 제출 API 엔드포인트
@inbody_bp.route('/submit', methods=['POST', 'OPTIONS'])
def submit():
    if request.method == 'OPTIONS':
        # CORS preflight 요청에 대한 빈 응답, 200 OK 리턴
        return '', 200
    return submit_inbody_data()
