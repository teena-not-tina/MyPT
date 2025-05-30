# import subprocess
# import threading
# import os
# import time
# from pathlib import Path
# import shutil

# BASE_DIR = Path(__file__).resolve().parent

# def run_backend():
#     os.chdir(BASE_DIR / "cv-service")
#     subprocess.run(["uvicorn", "main:app", "--reload", "--port", "8000"])

# def run_frontend():
#     os.chdir(BASE_DIR / "frontend")

#     # npm 경로 수동 지정
#     npm_path = shutil.which("npm") or "C:\\Program Files\\nodejs\\npm.cmd"
    
#     if os.path.exists(npm_path):
#         subprocess.run([npm_path, "start"], shell=True)
#     else:
#         print("❌ 'npm'을 찾을 수 없습니다. Node.js가 설치되어 있고 환경 변수에 등록되어 있는지 확인하세요.")

# if __name__ == "__main__":
#     threading.Thread(target=run_backend).start()
#     time.sleep(3)
#     threading.Thread(target=run_frontend).start()


# import subprocess
# import os
# from pathlib import Path
# import shutil

# BASE_DIR = Path(__file__).resolve().parent

# def run_frontend():
#     os.chdir(BASE_DIR / "frontend")
    
#     # npm 경로 수동 지정
#     npm_path = shutil.which("npm") or "C:\\Program Files\\nodejs\\npm.cmd"
        
#     if os.path.exists(npm_path):
#         subprocess.run([npm_path, "start"], shell=True)
#     else:
#         print("❌ 'npm'을 찾을 수 없습니다. Node.js가 설치되어 있고 환경 변수에 등록되어 있는지 확인하세요.")

# if __name__ == "__main__":
#     run_frontend()
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# React 빌드 파일 서빙
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path != "" and os.path.exists(os.path.join('frontend/build', path)):
        return send_from_directory('frontend/build', path)
    else:
        return send_from_directory('frontend/build', 'index.html')

# API 라우트들
from main import *  # 기존 API 라우트 import

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)