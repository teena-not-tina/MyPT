# chatbot_integrations.py - 다양한 챗봇 연동 예제

import requests
import base64
import asyncio
import aiohttp
from typing import Dict, Optional

# 1. 기본 Python 클래스 - 동기 버전
class FoodDetectionBot:
    """음식 인식 챗봇 클라이언트"""
    
    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url
        self.webhook_url = f"{api_url}/webhook/simple"
    
    def analyze_image_file(self, image_path: str, user_id: str = "bot_user") -> Dict:
        """로컬 이미지 파일 분석"""
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode()
            
            # API 호출
            response = requests.post(
                self.webhook_url,
                json={
                    "user_id": user_id,
                    "image_base64": image_base64,
                    "platform": "python_bot"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_image_url(self, image_url: str, user_id: str = "bot_user") -> Dict:
        """URL 이미지 분석"""
        try:
            response = requests.post(
                self.webhook_url,
                json={
                    "user_id": user_id,
                    "image_url": image_url,
                    "platform": "python_bot"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def format_response(self, result: Dict) -> str:
        """결과를 읽기 쉬운 텍스트로 포맷"""
        if "error" in result:
            return f"❌ 오류: {result['error']}"
        
        if result.get("status") != "success":
            return "❌ 분석 실패"
        
        text_parts = ["🍽️ 음식 인식 결과:\n"]
        
        # 감지된 음식
        detections = result.get("detections", [])
        if detections:
            text_parts.append("📌 감지된 음식:")
            for det in detections[:5]:
                confidence = det['confidence'] * 100
                text_parts.append(f"  • {det['label']} ({confidence:.1f}%)")
        else:
            text_parts.append("음식을 찾을 수 없습니다.")
        
        # OCR 결과
        ocr_results = result.get("ocr_results", [])
        if ocr_results:
            text_parts.append("\n📝 인식된 텍스트:")
            for ocr in ocr_results[:3]:
                text_parts.append(f"  • {ocr['text']}")
        
        return "\n".join(text_parts)


# 2. 비동기 버전 (Discord, Telegram 등에 유용)
class AsyncFoodDetectionBot:
    """비동기 음식 인식 챗봇 클라이언트"""
    
    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url
        self.webhook_url = f"{api_url}/webhook/simple"
    
    async def analyze_image_file(self, image_path: str, user_id: str = "async_bot") -> Dict:
        """비동기로 이미지 파일 분석"""
        try:
            # 이미지 읽기
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode()
            
            # 비동기 HTTP 요청
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json={
                        "user_id": user_id,
                        "image_base64": image_base64,
                        "platform": "async_bot"
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"API error: {response.status}"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_image_url(self, image_url: str, user_id: str = "async_bot") -> Dict:
        """비동기로 URL 이미지 분석"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json={
                    "user_id": user_id,
                    "image_url": image_url,
                    "platform": "async_bot"
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"API error: {response.status}"}


# # 3. Discord 봇 예제
# def create_discord_bot():
#     """Discord 봇 생성 예제"""
#     try:
#         import discord
#         from discord.ext import commands
        
#         bot = commands.Bot(command_prefix='!')
#         food_bot = AsyncFoodDetectionBot()
        
#         @bot.command(name='food')
#         async def analyze_food(ctx):
#             """!food 명령어로 이미지 분석"""
#             if not ctx.message.attachments:
#                 await ctx.send("🖼️ 이미지를 첨부해주세요!")
#                 return
            
#             attachment = ctx.message.attachments[0]
#             if not attachment.content_type.startswith('image/'):
#                 await ctx.send("❌ 이미지 파일만 분석 가능합니다!")
#                 return
            
#             # 처리 중 메시지
#             processing_msg = await ctx.send("🔍 이미지 분석 중...")
            
#             # 이미지 분석
#             result = await food_bot.analyze_image_url(
#                 attachment.url,
#                 user_id=str(ctx.author.id)
#             )
            
#             # 결과 전송
#             response_text = food_bot.format_response(result)
#             await processing_msg.edit(content=response_text)
        
#         return bot
    
#     except ImportError:
#         print("Discord.py가 설치되지 않았습니다: pip install discord.py")
#         return None


# # 4. Telegram 봇 예제
# def create_telegram_bot():
#     """Telegram 봇 생성 예제"""
#     try:
#         from telegram import Update
#         from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        
#         food_bot = FoodDetectionBot()
        
#         async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#             """사진 메시지 처리"""
#             await update.message.reply_text("🔍 이미지 분석 중...")
            
#             # 가장 큰 사진 가져오기
#             photo_file = await update.message.photo[-1].get_file()
            
#             # 임시 파일로 다운로드
#             import tempfile
#             with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
#                 await photo_file.download_to_drive(tmp_file.name)
                
#                 # 분석
#                 result = food_bot.analyze_image_file(
#                     tmp_file.name,
#                     user_id=str(update.effective_user.id)
#                 )
                
#                 # 결과 전송
#                 response_text = food_bot.format_response(result)
#                 await update.message.reply_text(response_text)
                
#                 # 임시 파일 삭제
#                 import os
#                 os.unlink(tmp_file.name)
        
#         # 봇 생성
#         application = Application.builder().token("YOUR_BOT_TOKEN").build()
#         application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
#         return application
    
#     except ImportError:
#         print("python-telegram-bot이 설치되지 않았습니다: pip install python-telegram-bot")
#         return None


# # 5. Streamlit 웹앱 예제
# def create_streamlit_app():
#     """Streamlit 웹앱 생성"""
#     try:
#         import streamlit as st
#         from PIL import Image
#         import io
        
#         st.title("🍽️ 음식 인식 챗봇")
#         st.write("음식 사진을 업로드하면 무엇인지 알려드립니다!")
        
#         # 파일 업로더
#         uploaded_file = st.file_uploader(
#             "이미지를 선택하세요",
#             type=['png', 'jpg', 'jpeg', 'webp']
#         )
        
#         if uploaded_file is not None:
#             # 이미지 표시
#             image = Image.open(uploaded_file)
#             st.image(image, caption='업로드된 이미지', use_column_width=True)
            
#             # 분석 버튼
#             if st.button('🔍 분석하기'):
#                 with st.spinner('분석 중...'):
#                     # base64로 변환
#                     buffered = io.BytesIO()
#                     image.save(buffered, format="JPEG")
#                     image_base64 = base64.b64encode(buffered.getvalue()).decode()
                    
#                     # API 호출
#                     bot = FoodDetectionBot()
#                     result = bot.analyze_image_file(image_base64, "streamlit_user")
                    
#                     # 결과 표시
#                     if result.get("status") == "success":
#                         st.success("분석 완료!")
                        
#                         # 감지된 음식
#                         if result.get("detections"):
#                             st.subheader("📌 감지된 음식")
#                             for det in result["detections"][:5]:
#                                 confidence = det['confidence'] * 100
#                                 st.write(f"• {det['label']} - {confidence:.1f}%")
                        
#                         # OCR 결과
#                         if result.get("ocr_results"):
#                             st.subheader("📝 인식된 텍스트")
#                             for ocr in result["ocr_results"][:3]:
#                                 st.write(f"• {ocr['text']}")
#                     else:
#                         st.error("분석 실패")
        
#     except ImportError:
#         print("Streamlit이 설치되지 않았습니다: pip install streamlit")


# # 6. 간단한 사용 예제
# if __name__ == "__main__":
#     # 기본 봇 생성
#     bot = FoodDetectionBot()
    
#     # 1. 로컬 이미지 분석
#     print("=== 로컬 이미지 분석 ===")
#     result = bot.analyze_image_file("test_food.jpg")
#     print(bot.format_response(result))
    
#     # 2. URL 이미지 분석
#     print("\n=== URL 이미지 분석 ===")
#     test_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400"
#     result = bot.analyze_image_url(test_url)
#     print(bot.format_response(result))
    
#     # 3. 비동기 버전 테스트
#     print("\n=== 비동기 버전 테스트 ===")
#     async def test_async():
#         async_bot = AsyncFoodDetectionBot()
#         result = await async_bot.analyze_image_url(test_url)
#         print(bot.format_response(result))
    
#     # asyncio.run(test_async())