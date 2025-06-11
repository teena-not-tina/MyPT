from fastapi import APIRouter
import asyncio
import json
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import aiofiles
from PIL import Image
import io
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import random
from bson.binary import Binary
import jwt
import base64
import traceback
import re
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()
security = HTTPBearer()

# MongoDB 설정
MONGO_URL = os.getenv("MONGODB_URL")
# MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.test  # MongoDB 데이터베이스 이름
collection = db.user_image

# ComfyUI 설정
COMFYUI_URL = "http://127.0.0.1:8188"
UPLOAD_DIR = "uploads"
BASE_IMAGES_DIR = "base_images"
OUTPUT_DIR = "outputs"

# 디렉토리 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BASE_IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# JWT 설정 (실제 환경에서는 환경변수로 관리)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰 검증"""
    try:
        if not credentials:
            logger.info("인증 정보 없음")
            raise HTTPException(status_code=401, detail="No credentials provided")
            
        token = credentials.credentials
        logger.info(f"받은 토큰: {token[:20]}...")  # 토큰 일부만 로깅
        
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                options={"verify_signature": True}
            )
            logger.info(f"디코딩된 페이로드: {payload}")
            
            user_id = payload.get("user_id")
            logger.info(f"추출된 user_id: {user_id}")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="user_id not found in token")
                
            return int(user_id)
            
        except jwt.ExpiredSignatureError:
            logger.error("토큰 만료됨")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"유효하지 않은 토큰: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token format")
            
    except Exception as e:
        logger.error(f"토큰 검증 에러: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# 7가지 다른 프롬프트 설정
STYLE_PROMPTS = [
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful, very round body, extremely chubby, soft pudgy belly, wide proportions, extra fluffy appearance, round cheeks, double chin, thick limbs, bouncy texture",
        "style_name": "very fat"
    },
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful, chubby body, round belly, soft curves, plump cheeks, thick arms and legs, cuddly appearance, slightly overweight, gentle roundness",
        "style_name": "fat"
    },
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful, slightly plump, soft body, small belly, gentle curves, adorable chubbiness, baby fat, rounded features",
        "style_name": "a little fat"
    },
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful",
        "style_name": "average"
    },
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful, slightly toned body, hint of muscles, athletic build, lean proportions, defined arms, sporty appearance, fit physique",
        "style_name": "slightly muscular"
    },
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful, muscular and well-defined chibi body, beige yellow shirt (perhaps a bit tight showing muscles), arms raised up in victory pose showing defined muscles",
        "style_name": "muscular"
    },
    {
        "positive": "simple cartoon character, cute chibi style, smiling face with dot eyes, small curved smile, beige yellow shirt, arms raised up in victory pose, cheerful expression, clean line art, black outlines, flat colors, pastel color palette, minimalist illustration, kawaii style, digital art, simple shading, wholesome character design, stick figure proportions, happy gesture, cel shading, white background, bright lighting, colorful, very muscular and bulky chibi body (like a chibi bodybuilder), beige yellow shirt straining over large muscles, arms raised up in victory pose showing exaggerated muscle definition",
        "style_name": "very muscular"
    }
]

NEGATIVE_PROMPT = "realistic, detailed, complex background, photographic, shadows, gradients, detailed anatomy, multiple characters, text, watermark, blurry, low quality, dark colors, scary, aggressive expression, lowres, extra limbs, deformed, mutated, sepia, monochrome, distorted proportions, worst quality, noisy, malformed, bad anatomy, ugly"

class GenerationRequest(BaseModel):
    base_image_name: str  # 베이스 이미지 파일명

class GenerationResult(BaseModel):
    user_id: str
    tag: str  # style_name을 tag로 사용
    image_data: bytes
    content_type: str
    created_at: datetime

class ComfyUIClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client_id = str(uuid.uuid4())
    
    async def upload_image(self, image_path: str, filename: str) -> str:
        """ComfyUI 서버에 이미지 업로드"""
        async with aiohttp.ClientSession() as session:
            with open(image_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('image', f, filename=filename)
                data.add_field('overwrite', 'true')
                
                async with session.post(f"{self.server_url}/upload/image", data=data) as response:
                    if response.status == 200:
                        return filename
                    else:
                        raise HTTPException(status_code=500, detail="Failed to upload image to ComfyUI")
    
    def create_workflow(self, user_image_filename: str, base_image_filename: str, 
                    positive_prompt: str, negative_prompt: str, seed: float) -> Dict[str, Any]:
        """워크플로우 JSON 생성 - 수정된 버전"""
        
        # seed를 정수로 변환
        seed = int(seed)
        
        workflow = {
            # LoadImage 노드 1 (유저 이미지 - IP-Adapter용)
            "36": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": user_image_filename
                }
            },
            # LoadImage 노드 2 (베이스 이미지 - ControlNet용)
            "10": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": base_image_filename
                }
            },
            # CheckpointLoader
            "14": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "dreamshaper_8.safetensors"
                }
            },
            # LoRA Loader
            "19": {
                "class_type": "LoraLoader",
                "inputs": {
                    "model": ["14", 0],
                    "clip": ["14", 1],
                    "lora_name": "arcane_offset.safetensors",
                    "strength_model": 1.0,
                    "strength_clip": 1.0
                }
            },
            # IP-Adapter 관련 노드들
            "35": {
                "class_type": "IPAdapterUnifiedLoader",
                "inputs": {
                    "model": ["19", 0],
                    "preset": "VIT-G (medium strength)"
                }
            },
            "34": {
                "class_type": "IPAdapterAdvanced",
                "inputs": {
                    "model": ["35", 0],
                    "ipadapter": ["35", 1],
                    "image": ["36", 0],
                    "weight": 0.7,
                    "weight_type": "linear",
                    "combine_embeds": "concat",
                    "start_at": 0.0,
                    "end_at": 1.0,
                    "embeds_scaling": "V only"
                }
            },
            # ControlNet 관련 노드들
            "21": {
                "class_type": "ControlNetLoader",
                "inputs": {
                    "control_net_name": "SD1.5\\control_v11p_sd15_canny_fp16.safetensors"
                }
            },
            "20": {
                "class_type": "Canny",
                "inputs": {
                    "image": ["10", 0],
                    "low_threshold": 0.4,
                    "high_threshold": 0.8
                }
            },
            "22": {
                "class_type": "ControlNetApplyAdvanced",
                "inputs": {
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "control_net": ["21", 0],
                    "image": ["20", 0],
                    "strength": 0.53,
                    "start_percent": 0.1,
                    "end_percent": 0.7
                }
            },
            # 텍스트 인코딩 노드들
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["19", 1],
                    "text": positive_prompt
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["19", 1],
                    "text": negative_prompt
                }
            },
            # 생성 관련 노드들
            "33": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                }
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["34", 0],
                    "positive": ["22", 0],
                    "negative": ["22", 1],
                    "latent_image": ["33", 0],
                    "seed": seed,
                    "control_after_generate": "fixed",
                    "steps": 25,
                    "cfg": 8.0,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "normal",
                    "denoise": 0.5
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["14", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["8", 0],
                    "filename_prefix": f"result_{seed}"
                }
            }
        }

        print("워크플로우 생성 완료")
        return workflow
        
    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """워크플로우를 ComfyUI 큐에 추가"""
        prompt_data = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        # JSON 직렬화 테스트
        try:
            json_str = json.dumps(prompt_data, indent=2)
            print("JSON 직렬화 성공")
            print(f"전송할 워크플로우 키: {list(workflow.keys())}")
        except Exception as e:
            print(f"JSON 직렬화 실패: {e}")
            raise HTTPException(status_code=500, detail=f"JSON serialization failed: {e}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.server_url}/prompt", json=prompt_data) as response:
                    response_text = await response.text()
                    print(f"ComfyUI 응답 status: {response.status}")
                    print(f"ComfyUI 응답 내용: {response_text}")
                    
                    if response.status == 200:
                        result = await response.json()
                        return result["prompt_id"]
                    else:
                        # 더 자세한 에러 정보 출력
                        try:
                            error_data = json.loads(response_text)
                            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                            error_details = error_data.get('error', {}).get('details', '')
                            print(f"ComfyUI Error: {error_msg}")
                            print(f"Error Details: {error_details}")
                            raise HTTPException(status_code=500, detail=f"ComfyUI Error: {error_msg} - {error_details}")
                        except json.JSONDecodeError:
                            raise HTTPException(status_code=500, detail=f"ComfyUI returned status {response.status}: {response_text}")
            except aiohttp.ClientError as e:
                print(f"Connection error: {e}")
                raise HTTPException(status_code=500, detail=f"Connection to ComfyUI failed: {e}")
    
    async def wait_for_completion(self, prompt_id: str) -> bool:
        """프롬프트 완료 대기"""
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/history/{prompt_id}") as response:
                    if response.status == 200:
                        history = await response.json()
                        if prompt_id in history:
                            return True
                    await asyncio.sleep(1)
    
    async def get_output_images(self, prompt_id: str) -> List[str]:
        """생성된 이미지 파일명 목록 반환"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/history/{prompt_id}") as response:
                if response.status == 200:
                    history = await response.json()
                    if prompt_id in history:
                        outputs = history[prompt_id].get("outputs", {})
                        images = []
                        for node_id, output in outputs.items():
                            if "images" in output:
                                for img in output["images"]:
                                    images.append(img["filename"])
                        return images
                return []

# ComfyUI 클라이언트 인스턴스
comfy_client = ComfyUIClient(COMFYUI_URL)

# 파일명을 안전하게 변환하는 함수 추가
def sanitize_filename(filename: str) -> str:
    """파일명에서 특수문자를 제거하고 안전한 파일명으로 변환"""
    # 이메일 주소의 @ 기호와 기타 특수문자를 언더스코어로 변경
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # 연속된 언더스코어를 하나로 축약
    safe_filename = re.sub(r'_+', '_', safe_filename)
    return safe_filename

    # ComfyUI 서버 상태 확인 함수 추가
async def check_comfyui_status():
    """ComfyUI 서버 상태 확인"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{COMFYUI_URL}/system_stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"ComfyUI 서버 상태: OK")
                    print(f"시스템 정보: {stats}")
                    return True
                else:
                    print(f"ComfyUI 서버 응답 오류: {response.status}")
                    return False
    except Exception as e:
        print(f"ComfyUI 서버 연결 실패: {e}")
        return False

@router.post("/upload-user-image")
async def upload_user_image(file: UploadFile = File(...), user_id: int = Depends(verify_token)):
    """사용자 이미지 업로드 (JWT 인증 적용)"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    file_extension = file.filename.split('.')[-1]
    safe_user_id = sanitize_filename(user_id)
    filename = f"{safe_user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()  # 파일 내용을 한 번만 읽음
    # 이미지 파일 검증
    try:
        Image.open(io.BytesIO(content)).verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file. Please upload a valid image.")

    # 검증 통과 후 저장
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    return {"message": "File uploaded successfully", "filename": filename}

@router.post("/generate-images")
async def generate_images(request: GenerationRequest, user_id: int = Depends(verify_token)):
    """7가지 스타일로 이미지 생성 (JWT 인증 적용)"""
    # ComfyUI 서버 상태 먼저 확인
    print("ComfyUI 서버 상태 확인 중...")
    if not await check_comfyui_status():
        raise HTTPException(status_code=503, detail="ComfyUI server is not available")

    generation_id = str(uuid.uuid4())
    user_image_filename = None
    base_image_path = os.path.join(BASE_IMAGES_DIR, request.base_image_name)
    
    # 베이스 이미지 존재 확인
    if not os.path.exists(base_image_path):
        raise HTTPException(status_code=404, detail="Base image not found")
    
    try:
        # test DB의 users 컬렉션에 user_id 문서가 없으면 생성
        # user_stats_db = client.test  # user_stats 데이터베이스
        # user_stat_col = user_stats_db.users  

        # existing_stat = await user_stat_col.find_one({"email": user_id})
        # if not existing_stat:
        #     now = datetime.now()
        #     await user_stat_col.insert_one({
        #         "email": user_id,
        #         "progress": 0,
        #         "level": 4,
        #         "created_at": now,
        #         "updated_at": now,
        #     })
        #     print(f"user_stat 컬렉션에 새 문서 생성: {user_id}")

        # 사용자 이미지 찾기 (특수문자가 제거된 파일명으로 검색)
        safe_user_id = sanitize_filename(user_id)
        user_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(safe_user_id)]
        if not user_files:
            raise HTTPException(status_code=404, detail="User image not found. Please upload an image first.")
        
        # 파일명에서 날짜시간 추출하여 가장 최근 파일 선택
        user_files.sort(reverse=True)
        user_image_filename = user_files[0]
        user_image_path = os.path.join(UPLOAD_DIR, user_image_filename)
        
        print(f"사용자 이미지: {user_image_filename}")
        print(f"베이스 이미지: {request.base_image_name}")
        
        # 이미지 파일이 실제로 존재하는지 확인
        if not os.path.exists(user_image_path):
            raise HTTPException(status_code=404, detail=f"User image file not found: {user_image_filename}")
        
        results = []
        seed = random.randint(0, 2**31 - 1)
        print(f"사용할 시드: {seed}")
        
        # 7가지 스타일로 각각 생성
        for i, style in enumerate(STYLE_PROMPTS):
            print(f"\n스타일 {i+1}/7 처리 중: {style['style_name']}")
            # 워크플로우 생성
            print("워크플로우 생성 중...")
            workflow = comfy_client.create_workflow(
                user_image_filename=user_image_filename,
                base_image_filename=request.base_image_name,
                positive_prompt=style["positive"],
                negative_prompt=NEGATIVE_PROMPT,
                seed=seed
            )

            # ComfyUI에 이미지들 업로드 - 업로드 성공 여부 확인
            print("이미지 업로드 중...")
            try:
                await comfy_client.upload_image(user_image_path, user_image_filename)
                print(f"사용자 이미지 업로드 완료: {user_image_filename}")
            except Exception as e:
                print(f"사용자 이미지 업로드 실패: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to upload user image: {e}")
            
            try:
                await comfy_client.upload_image(base_image_path, request.base_image_name)
                print(f"베이스 이미지 업로드 완료: {request.base_image_name}")
            except Exception as e:
                print(f"베이스 이미지 업로드 실패: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to upload base image: {e}")
            
            # ComfyUI에서 생성
            print("워크플로우 큐에 추가 중...")
            prompt_id = await comfy_client.queue_prompt(workflow)
            print(f"Prompt ID: {prompt_id}")
            
            print("생성 완료 대기 중...")
            await comfy_client.wait_for_completion(prompt_id)
            
            # 결과 이미지 파일명 가져오기
            output_images = await comfy_client.get_output_images(prompt_id)
            
            if output_images:
                result = {
                    "style_name": style["style_name"],
                    "prompt": style["positive"],
                    "seed": seed,
                    "output_filename": output_images[0],
                    "prompt_id": prompt_id
                }
                results.append(result)
                print(f"스타일 {i+1} 완료: {output_images[0]}")
            else:
                print(f"스타일 {i+1} 실패: 출력 이미지 없음")
        
        COMFY_OUTPUT_DIR = r"C:\Users\702-17\Documents\ComfyUI\output"  
        
        saved_images = {}
        for result in results:
            try:
                image_path = os.path.join(COMFY_OUTPUT_DIR, result["output_filename"])
                if os.path.exists(image_path):
                    async with aiofiles.open(image_path, 'rb') as f:
                        image_data = await f.read()
                    
                    # tag별로 이미지 정보 저장
                    saved_images[result["tag"] if "tag" in result else result["style_name"]] = {
                        "image_data": Binary(image_data),
                    }
            except Exception as e:
                print(f"Error saving image {result['output_filename']}: {str(e)}")
                traceback.print_exc()
                continue
        
        if saved_images:
            image_doc = {
                "user_id": user_id,
                "images": saved_images,
                "content_type": "image/png",
                "created_at": datetime.now()
            }
            insert_result = await collection.insert_one(image_doc)
            print(f"MongoDB에 저장 성공: {insert_result.inserted_id}")

        return {
            "generation_id": generation_id,
            "status": "completed",
            "mongodb_id": str(insert_result.inserted_id) if saved_images else None,
            "message": f"Successfully generated {len(saved_images)} images"
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/user/profile")
async def get_user_profile(user_id: int = Depends(verify_token)):
    """사용자 프로필 정보 조회"""
    try:
        # 사용자의 모든 생성된 이미지 수 조회
        total_images = await collection.count_documents({"user_id": user_id})
        
        # 가장 최근 생성 날짜 조회
        latest_creation = await collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        
        return {
            "user_id": user_id,
            "total_images": total_images,
            "latest_creation": latest_creation.get("created_at") if latest_creation else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    
# # 로그인 엔드포인트 (임시)
# @router.post("/api/auth/login")
# async def login(login_data: dict):
#     """로그인 처리 (임시)"""
#     # 실제로는 사용자 인증 로직이 들어가야 함
#     user_id = login_data.get("user_id")
#     password = login_data.get("password")
    
#     if not user_id or not password:
#         raise HTTPException(status_code=400, detail="User ID and password required")
    
#     # 여기서 실제 사용자 인증을 수행
#     # 예시로 간단히 처리
#     if password == "test":  # 실제 환경에서는 해시된 비밀번호 비교
#         # JWT 토큰 생성
#         token = jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm=ALGORITHM)
#         return {
#             "access_token": token,
#             "token_type": "bearer",
#             "user_id": user_id
#         }
#     else:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

# @router.get("/download-image/{filename}")
# async def download_image(filename: str):
#     """생성된 이미지 다운로드"""
#     # ComfyUI output 디렉토리에서 이미지 가져오기
#     comfy_output_dir = "ComfyUI/output"  # ComfyUI 설치 경로에 맞게 수정
#     image_path = os.path.join(comfy_output_dir, filename)
    
#     if os.path.exists(image_path):
#         async with aiofiles.open(image_path, 'rb') as f:
#             image_data = await f.read()
#             image_b64 = base64.b64encode(image_data).decode()
#             return {"image_data": image_b64}
#     else:
#         raise HTTPException(status_code=404, detail="Image not found")
