from flask import Flask, request, jsonify
from flask_cors import CORS
from src.routes.auth import auth_bp
from src.routes.chat import chat_bp
from src.routes.inbody import inbody_bp
from dotenv import load_dotenv
from src.config.db import test_connection  # 추가
import os
import traceback

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://localhost:3002"],
            "methods": ["OPTIONS", "POST", "GET"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(inbody_bp, url_prefix='/api/inbody')  # 여기에 추가

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

# 이하 생략
