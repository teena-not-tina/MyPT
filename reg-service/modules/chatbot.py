from modules.routine_generator import AIAnalyzer
from typing import List, Dict, Optional
import json
import uuid
from datetime import datetime

class FitnessChatbot:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.analyzer = AIAnalyzer()
        self.messages: List[Dict[str, str]] = []
        self.recommendation_generated = False
        self.inbody_data = None
        self.created_at = datetime.now()
        
    def add_message(self, role: str, content: str) -> Dict[str, str]:
        """메시지 추가"""
        message = {
            "role": role, 
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        return message
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """채팅 기록 반환"""
        return self.messages.copy()
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, str]]:
        """최근 메시지 반환"""
        return self.messages[-limit:] if self.messages else []
    
    def clear_chat_history(self):
        """채팅 기록 초기화"""
        self.messages = []
        self.recommendation_generated = False
        self.inbody_data = None
        print(f"💬 세션 {self.session_id} 채팅 기록이 초기화되었습니다.")
    
    def _build_context_prompt(self, user_input: str) -> str:
        """컨텍스트를 포함한 프롬프트 생성"""
        # 기본 컨텍스트
        context = "당신은 전문적인 AI 피트니스 코치입니다.\n\n"
        
        # InBody 데이터가 있는 경우 추가
        if self.inbody_data:
            context += f"사용자의 InBody 데이터:\n{self.inbody_data}\n\n"
        
        # 최근 대화 기록 추가 (최대 5개)
        recent_messages = self.get_recent_messages(5)
        if recent_messages:
            context += "최근 대화 기록:\n"
            for msg in recent_messages:
                role_name = "사용자" if msg["role"] == "user" else "AI 코치"
                context += f"{role_name}: {msg['content']}\n"
            context += "\n"
        
        # 현재 질문
        context += f"현재 사용자 질문: {user_input}\n\n"
        context += "위 정보를 바탕으로 친근하고 전문적으로 답변해주세요."
        
        return context
    
    def handle_user_input(self, user_input: str) -> str:
        """사용자 입력 처리"""
        try:
            if not self.recommendation_generated:
                return "먼저 InBody PDF를 업로드하고 분석을 완료해주세요."
            
            print(f"👤 사용자 입력: {user_input}")
            
            # 사용자 메시지 추가
            self.add_message("user", user_input)
            
            # 컨텍스트를 포함한 프롬프트 생성
            context_prompt = self._build_context_prompt(user_input)
            
            # AI 응답 생성 (1개 인자만 전달)
            print("🤖 AI 응답 생성 중...")
            response = self.analyzer.chat_with_bot(context_prompt)
            
            # AI 응답 추가
            self.add_message("assistant", response)
            
            print(f"🤖 AI 응답: {response[:100]}...")
            return response
            
        except Exception as e:
            error_msg = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            print(f"❌ {error_msg}")
            self.add_message("assistant", error_msg)
            return error_msg
    
    def process_inbody_analysis(self, inbody_text: str) -> Optional[str]:
        """InBody 분석 처리"""
        try:
            print("📊 InBody 데이터 분석 시작...")
            print(f"📝 입력 데이터 길이: {len(inbody_text)} 문자")
            
            # InBody 데이터 저장
            self.inbody_data = inbody_text
            
            # AI 분석 수행
            recommendation = self.analyzer.analyze_inbody_data(inbody_text)
            
            if recommendation:
                print("✅ InBody 분석 완료!")
                print(f"📋 추천 내용 길이: {len(recommendation)} 문자")
                
                # 추천 결과를 메시지로 추가
                self.add_message("assistant", recommendation)
                self.recommendation_generated = True
                
                return recommendation
            else:
                error_msg = "InBody 분석에 실패했습니다."
                print(f"❌ {error_msg}")
                self.add_message("assistant", error_msg)
                return None
                
        except Exception as e:
            error_msg = f"InBody 분석 중 오류 발생: {str(e)}"
            print(f"❌ {error_msg}")
            self.add_message("assistant", error_msg)
            return None
    
    def get_session_info(self) -> Dict:
        """세션 정보 반환"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "recommendation_generated": self.recommendation_generated,
            "message_count": len(self.messages),
            "has_inbody_data": self.inbody_data is not None
        }
    
    def export_chat_history(self) -> str:
        """채팅 기록을 JSON 문자열로 내보내기"""
        export_data = {
            "session_info": self.get_session_info(),
            "messages": self.messages,
            "inbody_data_length": len(self.inbody_data) if self.inbody_data else 0
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def import_chat_history(self, json_data: str) -> bool:
        """JSON 문자열에서 채팅 기록 가져오기"""
        try:
            data = json.loads(json_data)
            self.messages = data.get("messages", [])
            self.recommendation_generated = data.get("session_info", {}).get("recommendation_generated", False)
            print("✅ 채팅 기록을 성공적으로 가져왔습니다.")
            return True
        except Exception as e:
            print(f"❌ 채팅 기록 가져오기 실패: {str(e)}")
            return False

# 멀티 세션 관리를 위한 매니저 클래스
class ChatbotSessionManager:
    def __init__(self):
        self.sessions: Dict[str, FitnessChatbot] = {}
        print("🎯 ChatbotSessionManager 초기화 완료")
    
    def create_session(self, session_id: str = None) -> FitnessChatbot:
        """새 세션 생성"""
        chatbot = FitnessChatbot(session_id)
        self.sessions[chatbot.session_id] = chatbot
        print(f"🆕 새 세션 생성: {chatbot.session_id}")
        return chatbot
    
    def get_session(self, session_id: str) -> Optional[FitnessChatbot]:
        """세션 가져오기"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"🗑️  세션 삭제: {session_id}")
            return True
        return False
    
    def get_all_sessions(self) -> Dict[str, Dict]:
        """모든 세션 정보 반환"""
        return {
            session_id: chatbot.get_session_info() 
            for session_id, chatbot in self.sessions.items()
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """오래된 세션 정리"""
        from datetime import timedelta
        current_time = datetime.now()
        
        to_delete = []
        for session_id, chatbot in self.sessions.items():
            if current_time - chatbot.created_at > timedelta(hours=max_age_hours):
                to_delete.append(session_id)
        
        for session_id in to_delete:
            self.delete_session(session_id)
        
        if to_delete:
            print(f"🧹 {len(to_delete)}개의 오래된 세션을 정리했습니다.")

# API용 편의 함수들
def create_chatbot_session(session_id: str = None) -> FitnessChatbot:
    """새 챗봇 세션 생성"""
    return FitnessChatbot(session_id)

def analyze_inbody_and_chat(inbody_text: str, session_id: str = None) -> Dict:
    """InBody 분석 및 챗봇 세션 생성"""
    chatbot = FitnessChatbot(session_id)
    recommendation = chatbot.process_inbody_analysis(inbody_text)
    
    return {
        "success": recommendation is not None,
        "session_id": chatbot.session_id,
        "recommendation": recommendation,
        "session_info": chatbot.get_session_info()
    }

def chat_with_session(session_id: str, message: str, sessions: Dict[str, FitnessChatbot]) -> Dict:
    """세션별 채팅"""
    if session_id not in sessions:
        return {
            "success": False,
            "error": "Session not found"
        }
    
    chatbot = sessions[session_id]
    response = chatbot.handle_user_input(message)
    
    return {
        "success": True,
        "response": response,
        "session_info": chatbot.get_session_info()
    }

# 테스트 함수
def test_chatbot():
    """챗봇 기능 테스트"""
    print("🧪 챗봇 테스트 시작...")
    
    # 챗봇 생성
    chatbot = FitnessChatbot()
    print(f"✅ 챗봇 생성 완료: {chatbot.session_id}")
    
    # 샘플 InBody 데이터로 분석
    sample_inbody = """
    체중: 70kg, 체지방률: 15%, 근육량: 55kg
    BMI: 22.5, 기초대사율: 1650kcal
    """
    
    recommendation = chatbot.process_inbody_analysis(sample_inbody)
    if recommendation:
        print("✅ InBody 분석 테스트 성공")
        
        # 채팅 테스트
        response = chatbot.handle_user_input("운동 시간을 줄이고 싶어요")
        print(f"✅ 채팅 테스트 성공: {response[:50]}...")
        
        # 세션 정보 확인
        info = chatbot.get_session_info()
        print(f"✅ 세션 정보: {info}")
        
    else:
        print("❌ InBody 분석 테스트 실패")

if __name__ == "__main__":
    test_chatbot()