from flask import Flask, request, jsonify
from flask_cors import CORS

# ComfyUI 이미지 생성 함수 import 또는 같은 파일에 위치
from comfyui_generate import generate_image_from_comfyui  # 1단계 구현한 함수가 이 모듈에 있다고 가정

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3002"]}}, supports_credentials=True)

    @app.route("/api/generate-image", methods=["POST"])
    def generate_image():
        data = request.get_json()
        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        print(f"Received prompt: {prompt}")
        base64_img = generate_image_from_comfyui(prompt)
        if base64_img:
            return jsonify({"image_base64": base64_img})
        else:
            return jsonify({"error": "Image generation failed"}), 500

    return app
