# src/utils/gpt_api.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_gpt_response(user_message):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """당신은 식단 추천 전문가입니다. 
                사용자의 음식 섭취에 대해 분석하고 건강한 식단을 추천해주세요."""},
                {"role": "user", "content": user_message}
            ]
        )
        
        # 챗봇 응답
        chat_response = response.choices[0].message.content
        
        # 이미지 생성을 위한 프롬프트
        image_prompt = f"A cute cartoon avatar with {user_message}, health food theme, cheerful expression"
        
        return chat_response, image_prompt
        
    except Exception as e:
        print(f"GPT API 오류: {str(e)}")
        raise Exception("GPT 응답 생성 중 오류가 발생했습니다.")
