import os
from flask import Blueprint, jsonify
from flask_cors import cross_origin

cleanup_bp = Blueprint('cleanup', __name__)

@cleanup_bp.route('/cleanup-images', methods=['POST'])
@cross_origin(origins=["http://localhost:3002"], supports_credentials=True)
def cleanup_images():
    try:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output'))
        
        # output 디렉토리의 모든 파일 삭제
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error: {file_path}를 삭제하는 중 오류 발생: {e}")
        
        return jsonify({"message": "이미지 정리 완료"}), 200
        
    except Exception as e:
        print(f"이미지 정리 중 오류 발생: {e}")
        return jsonify({"error": str(e)}), 500