import os
import requests
import base64
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import traceback
import time

load_dotenv()

app = Flask(__name__, static_folder='../frontend/dist', template_folder='../frontend/dist')
CORS(app)

# --- 설정값 ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COMFYUI_API_URL = os.getenv("COMFYUI_API_URL", "http://localhost:8188")
# ---------------------------------------------

# ComfyUI 워크플로우 JSON 파일 로드
try:
    with open('comfyui_workflow.json', 'r', encoding='utf-8') as f:
        COMFYUI_WORKFLOW = json.loads(f.read())
except FileNotFoundError:
    print("Error: comfyui_workflow.json not found. Please create it in the backend folder.")
    COMFYUI_WORKFLOW = {}
except json.JSONDecodeError as e:
    print(f"Error decoding comfyui_workflow.json: {e}")
    COMFYUI_WORKFLOW = {}

# 기존 React 앱 서빙 라우트
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/chat_and_generate', methods=['POST'])
def chat_and_generate():
    data = request.json
    user_meal_message = data.get('message')
    user_openai_api_key = data.get('api_key') # 개발용, 실제 서비스에서는 보안 고려

    print("\n--- Request received ---")
    print(f"User message: {user_meal_message}")
    print(f"API Key received (from frontend): {'Present' if user_openai_api_key else 'Not Present'}")
    print(f"Using OPENAI_API_KEY from .env: {OPENAI_API_KEY is not None}")

    if not user_meal_message:
        return jsonify({"error": "메시지를 입력해주세요."}), 400
    if not (OPENAI_API_KEY or user_openai_api_key):
        return jsonify({"error": "OpenAI API 키가 설정되지 않았습니다."}), 400
    if not COMFYUI_WORKFLOW:
        return jsonify({"error": "ComfyUI 워크플로우를 로드할 수 없습니다. comfyui_workflow.json 파일을 확인하세요."}), 500

    openai_client = OpenAI(api_key=user_openai_api_key or OPENAI_API_KEY)

    try:
        # 1. GPT-4o-mini에게 음식 정보 기반으로 이미지 생성 프롬프트 요청
        print("Attempting to get GPT response...")
        messages = [
            {"role": "system", "content": """당신은 유용한 챗봇이자 이미지 프롬프트 생성 전문가입니다.
사용자가 오늘 먹은 음식을 알려주면, 그 음식에 대한 재미있는 설명을 해주고,
동시에 다음 형식에 맞춰 Stable Diffusion 이미지 프롬프트 (긍정 프롬프트와 부정 프롬프트) 및
초기 프로필 이미지 파일명을 JSON으로 생성해주세요.

**중요**: 프로필 이미지 파일명은 ComfyUI 서버의 `input` 폴더에 미리 저장된 파일명이어야 합니다.
예시 프로필 이미지 파일명은 'base_character.png' 또는 'profile_template.jpg' 등으로 가정합니다.
사용자의 입력에 따라 파일명을 변경할 필요는 없지만, 프롬프트 생성 시 참고하세요.

생성된 이미지 프롬프트는 기존 캐릭터에 음식을 결합하는 형태여야 합니다.

예시 출력:
{
  "chat_response": "와! [음식 이름]을 드셨군요! 정말 맛있었겠어요!",
  "image_positive_prompt": "a cute chibi character, with a body made of [음식 이름], small limbs, big head, full body, holding [음식 아이템], cartoon style, vibrant colors, clean lines, studio lighting, highly detailed",
  "image_negative_prompt": "ugly, deformed, blurry, text, watermark, bad anatomy",
  "initial_image_filename": "ComfyUI_00409_.png" // ComfyUI 워크플로우에 이미 지정되어 있음
}
"""
            },
            {"role": "user", "content": f"오늘 먹은 음식: {user_meal_message}"}
        ]

        gpt_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.7
        )

        response_content = gpt_response.choices[0].message.content
        parsed_gpt_data = json.loads(response_content)
        print("Successfully got and parsed GPT response.")
        print(f"GPT Response content (first 200 chars): {response_content[:200]}...")

        chat_response_text = parsed_gpt_data.get("chat_response", "음식에 대해 알려주셔서 감사합니다.")
        image_positive_prompt = parsed_gpt_data.get("image_positive_prompt")
        image_negative_prompt = parsed_gpt_data.get("image_negative_prompt")

        if not image_positive_prompt or not image_negative_prompt:
            print("Error: Could not get valid image prompts from GPT.")
            return jsonify({"error": "이미지 생성 프롬프트를 얻을 수 없습니다."}), 500

        print(f"Generated Positive Prompt: {image_positive_prompt}")
        print(f"Generated Negative Prompt: {image_negative_prompt}")

        # 2. ComfyUI 워크플로우 동적 수정
        modified_workflow = COMFYUI_WORKFLOW.copy()
        print("ComfyUI workflow copied.")

        if "2" in modified_workflow and "inputs" in modified_workflow["2"] and "text" in modified_workflow["2"]["inputs"]:
            modified_workflow["2"]["inputs"]["text"] = image_positive_prompt
        else:
            print("Warning: Positive CLIPTextEncode node (ID 2) not found or malformed in workflow.")

        if "3" in modified_workflow and "inputs" in modified_workflow["3"] and "text" in modified_workflow["3"]["inputs"]:
            modified_workflow["3"]["inputs"]["text"] = image_negative_prompt
        else:
            print("Warning: Negative CLIPTextEncode node (ID 3) not found or malformed in workflow.")

        comfyui_payload = {
            "prompt": modified_workflow,
            "client_id": "my_chatbot_client_v2"
        }

        print(f"Sending request to ComfyUI API at {COMFYUI_API_URL}/prompt")
        comfyui_headers = {"Content-Type": "application/json"}
        comfyui_response = requests.post(f"{COMFYUI_API_URL}/prompt", headers=comfyui_headers, json=comfyui_payload)
        comfyui_response.raise_for_status()
        print("Successfully sent prompt to ComfyUI. Waiting for execution...")

        response_data = comfyui_response.json()
        prompt_id = response_data['prompt_id']
        print(f"ComfyUI prompt_id received: {prompt_id}")

        generated_image_b64 = None
        MAX_RETRIES = 150   # 이 값은 이미 수정하셨을 겁니다.
        RETRY_DELAY = 1

        for i in range(MAX_RETRIES):
            history_url = f"{COMFYUI_API_URL}/history?prompt_id={prompt_id}"
            print(f"Attempt {i+1}/{MAX_RETRIES}: Requesting history from: {history_url}")

            try:
                response = requests.get(history_url, timeout=10) # 요청 타임아웃 추가
                response.raise_for_status() # HTTP 오류 발생 시 예외 처리

                history_data = response.json()

                # prompt_id가 history_data의 최상위 키로 직접 존재하므로 이렇게 변경합니다.
                if prompt_id in history_data:
                    print(f"Prompt ID {prompt_id} found in history data after {i+1} attempts.")
                    # 이제 outputs는 history_data[prompt_id] 바로 아래에 있습니다.
                    outputs = history_data[prompt_id]['outputs']
                    if '7' in outputs and 'images' in outputs['7']:
                        print("SaveImage node (ID 7) and images found in outputs.")
                        for image_info in outputs['7']['images']:
                            filename = image_info['filename']
                            subfolder = image_info['subfolder']
                            type_ = image_info['type']
                            print(f"Image info: filename={filename}, subfolder={subfolder}, type={type_}")

                            image_data_url = f"{COMFYUI_API_URL}/view?filename={filename}&subfolder={subfolder}&type={type_}"
                            print(f"Requesting image data from: {image_data_url}")
                            image_data_response = requests.get(image_data_url)
                            image_data_response.raise_for_status()
                            print("Successfully retrieved image data.")

                            generated_image_b64 = base64.b64encode(image_data_response.content).decode('utf-8')
                            print(f"Image data encoded to Base64. Length: {len(generated_image_b64)} bytes")
                            break # 첫 번째 이미지 정보를 찾으면 루프 종료
                    else:
                        print(f"Warning: No images found in SaveImage node (ID 7) output for prompt_id {prompt_id} after {i+1} attempts.")
                    break # 프롬프트 ID를 찾았으니 재시도 루프 종료
                else:
                    print(f"Prompt ID {prompt_id} not yet found in history. Retrying in {RETRY_DELAY} seconds...")

            except requests.exceptions.Timeout:
                print(f"Request to ComfyUI /history timed out (attempt {i+1}). Retrying...")
            except requests.exceptions.RequestException as e:
                print(f"Error requesting ComfyUI history (attempt {i+1}): {e}. Retrying...")
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from ComfyUI /history response (attempt {i+1}). Retrying...")
                # 오류 디버깅을 위해 응답 원문 일부 출력
                print(f"Raw response (decoding failed): {response.text[:200]}...")

            time.sleep(RETRY_DELAY)

        if not generated_image_b64:
            print(f"Error: Prompt ID {prompt_id} was not found in history after {MAX_RETRIES} attempts.")
            generated_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            chat_response_text += " (이미지 생성에 실패했습니다.)"
            print("Fallback to transparent pixel image.")

        print("Returning final JSON response.")
        return jsonify({
            "chat_response": chat_response_text,
            "profile_image_b64": generated_image_b64
        })

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ComfyUI API: {e}")
        traceback.print_exc()
        return jsonify({"error": f"이미지 생성 서버에 연결할 수 없습니다: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        print(f"Error parsing GPT/ComfyUI response JSON: {e}")
        traceback.print_exc()
        return jsonify({"error": f"응답 데이터 처리 중 오류 발생: {str(e)}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exc()
        return jsonify({"error": f"예상치 못한 오류 발생: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)