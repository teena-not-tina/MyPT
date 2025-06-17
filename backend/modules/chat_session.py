# backend/modules/chat_session.py - 루틴 저장 및 UI 개선
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging
import pytz  # ✅ 추가
import re

# ✅ 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korea_time():
    """한국 시간 반환"""
    return datetime.now(KST)

logger = logging.getLogger(__name__)

class SessionState(Enum):
    INITIAL = "initial"
    CHECKING_EXISTING_ROUTINE = "checking_existing_routine"
    ASKING_PDF = "asking_pdf"
    COLLECTING_INBODY = "collecting_inbody"
    COLLECTING_WORKOUT_PREFS = "collecting_workout_prefs"
    ASKING_ROUTINE_MODIFICATION = "asking_routine_modification"
    MODIFYING_ROUTINE = "modifying_routine"
    READY_FOR_RECOMMENDATION = "ready_for_recommendation"
    CHATTING = "chatting"

class ChatSession:
    def __init__(self, session_id: str = None, user_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.state = SessionState.INITIAL
        self.messages: List[Dict] = []
        self.inbody_data: Dict = {}
        self.workout_preferences: Dict = {}
        self.current_question_index = 0
        self.user_intent = None
        self.routine_data = None
        self.existing_routines = None  # 기존 루틴 저장
        self.modification_request = None  # 수정 요청 내용
        self.daily_modifications = {}  # 일일 수정사항 저장
        self.created_at = get_korea_time()  # ✅ 한국 시간 적용
        self.last_activity = get_korea_time()  # ✅ 한국 시간 적용
        
        self.selected_day_permanent = None  # 영구 수정할 일차 저장
    
    def add_message(self, sender: str, text: str, message_type: str = 'text', **kwargs) -> Dict:
        """메시지 추가"""
        message = {
            'id': len(self.messages) + 1,
            'sender': sender,
            'text': text,
            'type': message_type,
            'timestamp': get_korea_time().isoformat(),  # ✅ 한국 시간 적용
            **kwargs
        }
        self.messages.append(message)
        self.last_activity = get_korea_time()  # ✅ 한국 시간 적용
        return message
    
    def update_state(self, new_state: SessionState):
        """세션 상태 업데이트"""
        logger.info(f"Session {self.session_id}: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self.last_activity = get_korea_time()  # ✅ 한국 시간 적용
    
    def set_inbody_data(self, data: Dict):
        """인바디 데이터 설정"""
        self.inbody_data.update(data)
    
    def set_workout_preferences(self, data: Dict):
        """운동 선호도 설정"""
        self.workout_preferences.update(data)
    
    def set_existing_routines(self, routines: List[Dict]):
        """기존 루틴 설정"""
        self.existing_routines = routines
    
    def set_daily_modification(self, modification: Dict):
        """일일 수정사항 설정 (당일만 적용)"""
        today = get_korea_time().date().isoformat()  # ✅ 한국 시간 기준
        self.daily_modifications[today] = modification
        
        # 이전 날짜의 수정사항 정리
        to_remove = [date for date in self.daily_modifications.keys() if date != today]
        for date in to_remove:
            del self.daily_modifications[date]
    
    def get_current_routines(self):
        """현재 적용된 루틴 반환 (일일 수정사항 반영)"""
        today = get_korea_time().date().isoformat()  # ✅ 한국 시간 기준
        base_routines = self.existing_routines or []
        
        # 오늘의 수정사항이 있으면 적용
        if today in self.daily_modifications:
            modified_routines = base_routines.copy()
            modification = self.daily_modifications[today]
            return self._apply_daily_modifications(modified_routines, modification)
        
        return base_routines
    
    def _apply_daily_modifications(self, routines: List[Dict], modification: Dict) -> List[Dict]:
        """일일 수정사항을 루틴에 적용"""
        # 실제 수정 로직 구현
        # 예시: 특정 운동의 강도 조절, 운동 교체 등
        modified_routines = json.loads(json.dumps(routines))  # 깊은 복사
        
        mod_type = modification.get('type')
        if mod_type == 'intensity_adjustment':
            # 강도 조절
            factor = modification.get('factor', 1.0)
            for routine in modified_routines:
                for exercise in routine.get('exercises', []):
                    for set_info in exercise.get('sets', []):
                        if 'weight' in set_info:
                            set_info['weight'] = int(set_info['weight'] * factor)
                        if 'reps' in set_info:
                            set_info['reps'] = int(set_info['reps'] * factor)
        
        elif mod_type == 'exercise_replacement':
            # 운동 교체
            old_exercise = modification.get('old_exercise')
            new_exercise = modification.get('new_exercise')
            if old_exercise and new_exercise:
                for routine in modified_routines:
                    for exercise in routine.get('exercises', []):
                        if old_exercise.lower() in exercise.get('name', '').lower():
                            exercise['name'] = new_exercise
        
        return modified_routines
    
    def get_session_info(self) -> Dict:
        """세션 정보 반환"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'state': self.state.value,
            'message_count': len(self.messages),
            'current_question_index': self.current_question_index,
            'has_inbody_data': bool(self.inbody_data),
            'has_workout_preferences': bool(self.workout_preferences),
            'has_routine_data': bool(self.routine_data),
            'has_existing_routines': bool(self.existing_routines),
            'has_daily_modifications': bool(self.daily_modifications),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

class ChatSessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        
        # 질문 템플릿
        self.INBODY_QUESTIONS = [
            {'key': 'gender', 'text': '성별을 선택해주세요.', 'type': 'buttons', 'options': ['남성', '여성'], 'required': True},
            {'key': 'age', 'text': '나이를 입력해주세요.', 'type': 'input', 'required': True},
            {'key': 'height', 'text': '키를 입력해주세요. (cm 단위)', 'type': 'input', 'required': True},
            {'key': 'weight', 'text': '현재 체중을 입력해주세요. (kg 단위)', 'type': 'input', 'required': True},
            {'key': 'muscle_mass', 'text': '골격근량을 알고 계신다면 선택해주세요.', 'type': 'buttons', 'options': ['모름', '30kg 미만', '30-35kg', '35-40kg', '40-45kg', '45kg 이상'], 'required': False},
            {'key': 'body_fat', 'text': '체지방률을 알고 계신다면 선택해주세요.', 'type': 'buttons', 'options': ['모름', '10% 미만', '10-15%', '15-20%', '20-25%', '25-30%', '30% 이상'], 'required': False},
            {'key': 'bmi', 'text': 'BMI를 알고 계신다면 선택해주세요.', 'type': 'buttons', 'options': ['모름', '18.5 미만 (저체중)', '18.5-23 (정상)', '23-25 (과체중)', '25-30 (비만)', '30 이상 (고도비만)'], 'required': False},
            {'key': 'basal_metabolic_rate', 'text': '기초대사율을 알고 계신다면 선택해주세요.', 'type': 'buttons', 'options': ['모름', '1200 미만', '1200-1400', '1400-1600', '1600-1800', '1800-2000', '2000 이상'], 'required': False}
        ]
        
        self.WORKOUT_QUESTIONS = [
            {'key': 'goal', 'text': '운동 목표를 입력해주세요.\n(예: 다이어트, 근육량 증가, 체력 향상, 건강 유지 등)', 'type': 'input', 'required': True},
            {'key': 'experience_level', 'text': '운동 경험 수준을 선택해주세요.', 'type': 'buttons', 'options': ['초보자', '보통', '숙련자'], 'required': True},
            {'key': 'injury_status', 'text': '현재 부상이나 주의사항을 입력해주세요.\n(없으면 \'없음\'이라고 입력해주세요)', 'type': 'input', 'required': True},
            {'key': 'available_time', 'text': '운동 가능 시간을 선택해주세요.', 'type': 'buttons', 'options': ['주 1-2회, 30분', '주 2-3회, 45분', '주 3-4회, 1시간', '주 4-5회, 1시간+', '매일, 30분', '매일, 1시간+'], 'required': True}
        ]
        
        # 루틴 수정 옵션들
        self.ROUTINE_MODIFICATION_OPTIONS = [
            '새로운 루틴으로 완전히 교체',
            '오늘 하루만 수정하기',  
            '특정 일차를 영구적으로 수정하기', 
            '기존 루틴 유지하고 상담만'
        ]
        
        # 2단계: 일일 수정 세부 옵션들
        self.DAILY_MODIFICATION_OPTIONS = [
            '특정 운동 교체하기',
            '운동 강도 조절하기',
            '운동 시간 조절하기',
            '전체 루틴 일부 수정하기'
        ]
        
    MAX_SESSIONS = 1000
    
    def get_or_create_session(self, session_id: str = None, user_id: str = None) -> ChatSession:
        """세션 가져오기 또는 생성 - 빈 세션만 생성"""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if user_id and not session.user_id:
                session.user_id = user_id
            return session
        
        session = ChatSession(session_id, user_id)
        self.sessions[session.session_id] = session
        logger.info(f"새 세션 생성: {session.session_id} (사용자: {user_id})")
        
        return session
    
    async def create_session_with_welcome_message(self, user_id: str, analyzer) -> Dict:
        """새 세션 생성 + 환영 메시지 생성 (모든 초기화 로직의 중심)"""
        try:
            # 1. 빈 세션 생성
            session = self.get_or_create_session(user_id=user_id)
            
            # 2. 사용자 상황에 따른 환영 메시지 생성
            if user_id and user_id not in ["None", "null", None]:
                # 사용자 ID가 있는 경우 - 기존 루틴 확인
                try:
                    has_routines = analyzer.db.has_user_routines(user_id)
                    logger.info(f"사용자 {user_id} 기존 루틴 존재: {has_routines}")
                    
                    if has_routines:
                        # 기존 루틴이 있는 경우
                        existing_routines = analyzer.db.get_user_routines(user_id)
                        session.set_existing_routines(existing_routines)
                        
                        bot_message = session.add_message(
                            'bot',
                            f'안녕하세요! 💪 기존에 생성하신 운동 루틴({len(existing_routines)}일차)이 있습니다.\n\n어떻게 도와드릴까요?'
                        )
                        session.update_state(SessionState.ASKING_ROUTINE_MODIFICATION)
                        
                        return self._create_response(
                            session, 
                            bot_message,
                            show_buttons=True,
                            button_options=self.ROUTINE_MODIFICATION_OPTIONS,
                            routine_data=existing_routines
                        )
                    else:
                        # 기존 루틴이 없는 경우 - 바로 PDF 질문
                        bot_message = session.add_message(
                            'bot',
                            '운동 루틴 추천을 위해 인바디 정보가 필요합니다.\n\n인바디 측정 결과 PDF가 있으신가요?'
                        )
                        session.update_state(SessionState.ASKING_PDF)
                        
                        return self._create_response(
                            session,
                            bot_message,
                            show_buttons=True,
                            button_options=['예, PDF가 있어요', '아니오, 수동 입력할게요']
                        )
                        
                except Exception as db_error:
                    logger.error(f"DB 조회 실패: {str(db_error)}")
                    # DB 실패시 기본 PDF 질문
                    bot_message = session.add_message(
                        'bot',
                        '운동 루틴 추천을 위해 인바디 정보가 필요합니다.\n\n인바디 측정 결과 PDF가 있으신가요?'
                    )
                    session.update_state(SessionState.ASKING_PDF)
                    
                    return self._create_response(
                        session,
                        bot_message,
                        show_buttons=True,
                        button_options=['예, PDF가 있어요', '아니오, 수동 입력할게요']
                    )
            else:
                # 사용자 ID가 없는 경우 - 바로 PDF 질문
                bot_message = session.add_message(
                    'bot',
                    '안녕하세요! AI 피트니스 코치입니다! 💪\n\n운동 루틴 추천을 위해 인바디 정보가 필요합니다.\n\n인바디 측정 결과 PDF가 있으신가요?'
                )
                session.update_state(SessionState.ASKING_PDF)
                
                return self._create_response(
                    session,
                    bot_message,
                    show_buttons=True,
                    button_options=['예, PDF가 있어요', '아니오, 수동 입력할게요']
                )
                
        except Exception as e:
            logger.error(f"환영 메시지 생성 실패: {str(e)}")
            raise
    
    async def process_message(self, session_id: str, message: str, analyzer, user_id: str = None) -> Dict:
        """메시지 처리 메인 로직"""
        session = self.get_or_create_session(session_id, user_id)
        
        # 사용자 메시지 추가
        session.add_message('user', message)
        
        try:
            if session.state == SessionState.ASKING_ROUTINE_MODIFICATION:
                return await self._handle_routine_modification_choice(session, message, analyzer)
            
            elif session.state == SessionState.MODIFYING_ROUTINE:
                return await self._handle_routine_modification(session, message, analyzer)
            
            elif session.state == SessionState.ASKING_PDF:
                return await self._handle_pdf_question(session, message)
            
            elif session.state == SessionState.COLLECTING_INBODY:
                return await self._handle_inbody_collection(session, message, analyzer)
            
            elif session.state == SessionState.COLLECTING_WORKOUT_PREFS:
                return await self._handle_workout_prefs_collection(session, message, analyzer)
            
            elif session.state == SessionState.CHATTING:
                return await self._handle_general_chat(session, message, analyzer)
            
            else:
                # 예상치 못한 상태 - 일반 채팅으로 처리
                return await self._handle_general_chat(session, message, analyzer)
                
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {str(e)}")
            bot_message = session.add_message(
                'bot',
                '죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요.'
            )
            return self._create_response(session, bot_message)

    async def _handle_routine_modification_choice(self, session: ChatSession, message: str, analyzer) -> Dict:
        """루틴 수정 선택 처리"""
        session.modification_request = message
        
        if '새로운 루틴으로 완전히 교체' in message:
            # 기존 루틴을 temp_routines에 백업
            existing_routines = analyzer.db.get_user_routines(session.user_id)
            if existing_routines:
                backup_success = analyzer.db.backup_user_routines_to_temp(
                    session.user_id, 
                    existing_routines,
                    backup_type="complete_replacement"
                )
                if backup_success:
                    logger.info(f"사용자 {session.user_id}의 기존 루틴을 temp_routines에 백업 완료")
            
            # 기존 루틴 삭제
            analyzer.db.delete_user_routines(session.user_id)
            
            # 사용자 벡터DB에서도 기존 데이터 삭제
            if hasattr(analyzer, 'user_vector_store') and session.user_id:
                analyzer.user_vector_store.delete_user_data(session.user_id)
            
            bot_message = session.add_message(
                'bot',
                '기존 루틴을 삭제하고 새로운 루틴을 생성하겠습니다.\n\n인바디 측정 결과 PDF가 있으신가요?'
            )
            session.update_state(SessionState.ASKING_PDF)
            return self._create_response(session, bot_message, show_buttons=True,
                                       button_options=['예, PDF가 있어요', '아니오, 수동 입력할게요'])
        
        elif '오늘 하루만 수정하기' in message:
            bot_message = session.add_message(
                'bot',
                '오늘 하루만 어떤 방식으로 수정하시겠어요?\n\n선택하신 수정사항은 오늘만 적용되고, 내일부터는 자동으로 원래 루틴으로 돌아갑니다.'
            )
            session.update_state(SessionState.MODIFYING_ROUTINE)
            session.modification_request = "daily_modification"
            
            return self._create_response(session, bot_message, show_buttons=True,
                                       button_options=self.DAILY_MODIFICATION_OPTIONS)
        
        elif '특정 일차를 영구적으로 수정하기' in message:
            existing_routines = session.get_current_routines()
            if not existing_routines:
                bot_message = session.add_message(
                    'bot',
                    '수정할 기존 루틴을 찾을 수 없습니다.'
                )
                return self._create_response(session, bot_message)
            
            # 사용가능한 일차 옵션 동적 생성
            available_days = []
            max_day = len(existing_routines)
            for i in range(1, max_day + 1):
                available_days.append(f'{i}일차 영구 수정')
            
            if max_day > 1:
                available_days.append('여러 일차 영구 수정')
            
            bot_message = session.add_message(
                'bot',
                f'현재 {max_day}일간의 루틴이 있습니다.\n\n어떤 일차를 영구적으로 수정하시겠어요?\n\n⚠️ 이 수정은 영구적으로 적용되며, 해당 일차 루틴이 완전히 바뀝니다.'
            )
            session.update_state(SessionState.MODIFYING_ROUTINE)
            session.modification_request = "permanent_day_selection"
            
            return self._create_response(session, bot_message, show_buttons=True,
                                       button_options=available_days)
        
        elif '기존 루틴 유지하고 상담만' in message:
            current_routines = session.get_current_routines()
            bot_message = session.add_message(
                'bot',
                '현재 루틴에 대해 궁금한 점이나 조언이 필요한 부분을 말씀해주세요! 💪'
            )
            session.update_state(SessionState.CHATTING)
            return self._create_response(session, bot_message, routine_data=current_routines)
        
        else:
            bot_message = session.add_message(
                'bot',
                '죄송합니다. 다시 선택해주세요.'
            )
            return self._create_response(session, bot_message, show_buttons=True,
                                       button_options=self.ROUTINE_MODIFICATION_OPTIONS)

    async def _handle_routine_modification(self, session: ChatSession, message: str, analyzer) -> Dict:
        """루틴 수정 처리"""
        try:
            if session.modification_request == "daily_modification":
                if '특정 운동 교체하기' in message:
                    bot_message = session.add_message(
                        'bot',
                        '어떤 운동을 어떤 운동으로 교체하고 싶으신가요?\n\n예시: "1일차 벤치프레스를 스쿼트로 바꿔주세요"'
                    )
                    return self._create_response(session, bot_message, show_input=True,
                                               input_placeholder="예: 1일차 벤치프레스를 스쿼트로 바꿔주세요")
                
                elif '운동 강도 조절하기' in message:
                    bot_message = session.add_message(
                        'bot',
                        '운동 강도를 어떻게 조절하고 싶으신가요?\n\n예시: "전체적으로 20% 낮춰주세요" 또는 "중량을 10% 늘려주세요"'
                    )
                    return self._create_response(session, bot_message, show_input=True,
                                               input_placeholder="예: 전체적으로 20% 낮춰주세요")
                
                elif '운동 시간 조절하기' in message:
                    bot_message = session.add_message(
                        'bot',
                        '운동 시간을 어떻게 조절하고 싶으신가요?\n\n예시: "30분으로 줄여주세요" 또는 "1시간으로 늘려주세요"'
                    )
                    return self._create_response(session, bot_message, show_input=True,
                                               input_placeholder="예: 30분으로 줄여주세요")
                
                elif '전체 루틴 일부 수정하기' in message:
                    bot_message = session.add_message(
                        'bot',
                        '루틴의 어떤 부분을 수정하고 싶으신가요?\n\n구체적으로 말씀해주세요.'
                    )
                    return self._create_response(session, bot_message, show_input=True,
                                               input_placeholder="수정하고 싶은 내용을 구체적으로 입력해주세요")
                
                else:
                    return await self._process_daily_modification(session, message, analyzer)
            
            elif session.modification_request == "permanent_day_selection":
                return await self._handle_permanent_day_selection(session, message, analyzer)
            
            elif hasattr(session, 'selected_day_permanent') and session.selected_day_permanent:
                return await self._process_permanent_day_modification(session, message, analyzer)
            
            else:
                bot_message = session.add_message(
                    'bot',
                    '수정 방식을 다시 선택해주세요.'
                )
                session.update_state(SessionState.ASKING_ROUTINE_MODIFICATION)
                return self._create_response(session, bot_message, show_buttons=True,
                                           button_options=self.ROUTINE_MODIFICATION_OPTIONS)
                
        except Exception as e:
            logger.error(f"루틴 수정 처리 중 오류: {str(e)}")
            bot_message = session.add_message(
                'bot',
                '루틴 수정 중 오류가 발생했습니다. 다시 시도해주세요.'
            )
            return self._create_response(session, bot_message)

    async def _process_daily_modification(self, session: ChatSession, message: str, analyzer) -> Dict:
        """실제 일일 수정 처리"""
        try:
            existing_routines = analyzer.db.get_user_routines(session.user_id)
            if not existing_routines:
                bot_message = session.add_message(
                    'bot',
                    '수정할 기존 루틴을 찾을 수 없습니다.'
                )
                return self._create_response(session, bot_message)
            
            # 기존 루틴을 임시 저장
            backup_success = analyzer.db.backup_user_routines_to_temp(
                session.user_id, 
                existing_routines,
                backup_type="daily_modification"
            )
            if not backup_success:
                bot_message = session.add_message(
                    'bot',
                    '루틴 백업 중 오류가 발생했습니다. 다시 시도해주세요.'
                )
                return self._create_response(session, bot_message)
            
            # Function calling으로 수정된 루틴 생성
            response = await analyzer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "사용자의 요청에 따라 운동 루틴을 수정하세요. 기존 루틴의 구조를 유지하면서 요청된 부분만 수정해야 합니다."
                }, {
                    "role": "user",
                    "content": f"기존 루틴: {existing_routines}\n\n수정 요청: {message}"
                }],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "modify_routine",
                        "description": "운동 루틴을 수정합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "modified_routines": {
                                    "type": "array",
                                    "description": "수정된 운동 루틴 배열",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {"type": "integer"},
                                            "day": {"type": "integer"},
                                            "title": {"type": "string"},
                                            "exercises": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"},
                                                        "sets": {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "id": {"type": "integer"},
                                                                    "reps": {"type": "integer"},
                                                                    "weight": {"type": "integer"},
                                                                    "time": {"type": "string"},
                                                                    "completed": {"type": "boolean"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "modification_summary": {
                                    "type": "string",
                                    "description": "수정 내용 요약"
                                },
                                "success": {
                                    "type": "boolean",
                                    "description": "수정 성공 여부"
                                }
                            },
                            "required": ["modified_routines", "modification_summary", "success"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "modify_routine"}}
            )
            
            if response.choices[0].message.tool_calls:
                function_call = response.choices[0].message.tool_calls[0].function
                modification_result = json.loads(function_call.arguments)
                
                if modification_result.get('success', False):
                    modified_routines = modification_result.get('modified_routines', [])
                    modification_summary = modification_result.get('modification_summary', '')
                    
                    # 기존 루틴을 삭제하고 수정된 루틴을 저장
                    analyzer.db.delete_user_routines(session.user_id)
                    
                    # 수정된 루틴 저장
                    saved_routines = []
                    for routine in modified_routines:
                        routine['user_id'] = int(session.user_id)
                        saved_id = analyzer.db.save_routine(routine)
                        if saved_id:
                            routine['_id'] = str(saved_id)
                            saved_routines.append(routine)
                    
                    # 자동 복원 스케줄링 (24시간 후)
                    analyzer.db.schedule_routine_restoration(session.user_id, 24)
                    
                    bot_message = session.add_message(
                        'bot',
                        f"오늘 하루만 적용될 루틴 수정이 완료되었습니다! ✅\n\n📝 수정 내용: {modification_summary}\n\n⏰ 내일 자정에 자동으로 원래 루틴으로 돌아갑니다.\n\n수정된 오늘의 루틴을 확인해보세요."
                    )
                    session.update_state(SessionState.CHATTING)
                    return self._create_response(session, bot_message, routine_data=saved_routines)
                else:
                    analyzer.db.restore_user_routines_from_temp(session.user_id, backup_type="daily_modification")
                    bot_message = session.add_message(
                        'bot',
                        '요청하신 수정이 어려울 수 있습니다. 다른 방식으로 수정해보시겠어요?'
                    )
                    return self._create_response(session, bot_message)
            
        except Exception as e:
            logger.error(f"일일 수정 처리 중 오류: {str(e)}")
            try:
                analyzer.db.restore_user_routines_from_temp(session.user_id, backup_type="daily_modification")
            except:
                pass
            
            bot_message = session.add_message(
                'bot',
                '루틴 수정 중 오류가 발생했습니다. 원래 루틴을 유지합니다.'
            )
            return self._create_response(session, bot_message)

    async def _handle_permanent_day_selection(self, session: ChatSession, message: str, analyzer) -> Dict:
        """영구적인 특정 일차 선택 처리"""
        try:
            day_pattern = r'(\d+)일차 영구 수정'
            match = re.search(day_pattern, message)
            
            if match:
                selected_day = int(match.group(1))
                session.selected_day_permanent = selected_day
                
                existing_routines = session.get_current_routines()
                target_routine = next((r for r in existing_routines if r['day'] == selected_day), None)
                
                if not target_routine:
                    bot_message = session.add_message(
                        'bot',
                        f'{selected_day}일차 루틴을 찾을 수 없습니다.'
                    )
                    return self._create_response(session, bot_message)
                
                current_exercises = []
                for exercise in target_routine.get('exercises', []):
                    current_exercises.append(f"- {exercise['name']}")
                
                current_routine_text = '\n'.join(current_exercises)
                
                bot_message = session.add_message(
                    'bot',
                    f'📋 현재 {selected_day}일차 루틴:\n{current_routine_text}\n\n⚠️ 영구적으로 어떻게 수정하고 싶으신가요?\n\n예시:\n- "1번째 운동을 ○○으로 바꿔주세요"\n- "전체적으로 강도를 20% 낮춰주세요"\n- "○○ 운동을 추가해주세요"\n\n❗ 이 수정은 영구적으로 적용됩니다.'
                )
                
                session.modification_request = f"permanent_day_{selected_day}_modification"
                
                return self._create_response(session, bot_message, show_input=True,
                                           input_placeholder=f"{selected_day}일차 영구 수정 요청을 구체적으로 입력해주세요")
            
            elif '여러 일차 영구 수정' in message:
                existing_routines = session.get_current_routines()
                routine_summary = []
                for routine in existing_routines:
                    exercise_names = [ex['name'] for ex in routine.get('exercises', [])]
                    routine_summary.append(f"{routine['day']}일차: {', '.join(exercise_names[:2])}...")
                
                summary_text = '\n'.join(routine_summary)
                
                bot_message = session.add_message(
                    'bot',
                    f'📋 현재 루틴 요약:\n{summary_text}\n\n⚠️ 여러 일차를 영구적으로 어떻게 수정하고 싶으신가요?\n\n예시:\n- "1일차와 3일차에서 ○○ 운동을 ××로 바꿔주세요"\n- "모든 일차의 강도를 15% 높여주세요"\n\n❗ 이 수정은 영구적으로 적용됩니다.'
                )
                
                session.modification_request = "permanent_multiple_days_modification"
                session.selected_day_permanent = "multiple"
                
                return self._create_response(session, bot_message, show_input=True,
                                           input_placeholder="여러 일차 영구 수정 요청을 구체적으로 입력해주세요")
            else:
                bot_message = session.add_message(
                    'bot',
                    '선택을 인식할 수 없습니다. 다시 선택해주세요.'
                )
                return self._create_response(session, bot_message)
                
        except Exception as e:
            logger.error(f"영구 일차 선택 처리 중 오류: {str(e)}")
            bot_message = session.add_message(
                'bot',
                '일차 선택 처리 중 오류가 발생했습니다.'
            )
            return self._create_response(session, bot_message)

    async def _process_permanent_day_modification(self, session: ChatSession, message: str, analyzer) -> Dict:
        """영구적인 특정 일차 수정 처리"""
        try:
            selected_day = session.selected_day_permanent
            existing_routines = analyzer.db.get_user_routines(session.user_id)
            
            if not existing_routines:
                bot_message = session.add_message(
                    'bot',
                    '수정할 기존 루틴을 찾을 수 없습니다.'
                )
                return self._create_response(session, bot_message)
            
            if selected_day == "multiple":
                return await self._process_permanent_multiple_days_modification(session, message, analyzer, existing_routines)
            else:
                return await self._process_permanent_single_day_modification(session, message, analyzer, existing_routines, selected_day)
                
        except Exception as e:
            logger.error(f"영구 일차 수정 처리 중 오류: {str(e)}")
            bot_message = session.add_message(
                'bot',
                '루틴 수정 중 오류가 발생했습니다. 다시 시도해주세요.'
            )
            return self._create_response(session, bot_message)

    async def _process_permanent_single_day_modification(self, session: ChatSession, message: str, analyzer, existing_routines: List[Dict], selected_day: int) -> Dict:
        """단일 일차 영구 수정 처리"""
        try:
            target_routine = next((r for r in existing_routines if r['day'] == selected_day), None)
            
            if not target_routine:
                bot_message = session.add_message(
                    'bot',
                    f'{selected_day}일차 루틴을 찾을 수 없습니다.'
                )
                return self._create_response(session, bot_message)
            
            # Function calling으로 특정 일차만 수정
            response = await analyzer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"사용자가 {selected_day}일차 루틴만 영구적으로 수정하고 싶어합니다. 기존 루틴의 구조를 유지하면서 요청된 부분만 수정해주세요."
                }, {
                    "role": "user",
                    "content": f"기존 {selected_day}일차 루틴: {target_routine}\n\n영구 수정 요청: {message}"
                }],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "modify_single_day_routine_permanent",
                        "description": f"{selected_day}일차 운동 루틴을 영구적으로 수정합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "modified_routine": {
                                    "type": "object",
                                    "description": f"영구 수정된 {selected_day}일차 운동 루틴",
                                    "properties": {
                                        "user_id": {"type": "integer"},
                                        "day": {"type": "integer"},
                                        "title": {"type": "string"},
                                        "exercises": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"},
                                                    "sets": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "id": {"type": "integer"},
                                                                "reps": {"type": "integer"},
                                                                "weight": {"type": "integer"},
                                                                "time": {"type": "string"},
                                                                "completed": {"type": "boolean"}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "modification_summary": {
                                    "type": "string",
                                    "description": "수정 내용 요약"
                                },
                                "success": {
                                    "type": "boolean",
                                    "description": "수정 성공 여부"
                                }
                            },
                            "required": ["modified_routine", "modification_summary", "success"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "modify_single_day_routine_permanent"}}
            )
            
            if response.choices[0].message.tool_calls:
                function_call = response.choices[0].message.tool_calls[0].function
                modification_result = json.loads(function_call.arguments)
                
                if modification_result.get('success', False):
                    modified_routine = modification_result.get('modified_routine', {})
                    modification_summary = modification_result.get('modification_summary', '')
                    
                    modified_routine['user_id'] = int(session.user_id)
                    modified_routine['day'] = selected_day
                    
                    # 기존 해당 일차 루틴 삭제
                    analyzer.db.delete_specific_day_routine(session.user_id, selected_day)
                    
                    # 수정된 루틴 저장
                    saved_id = analyzer.db.save_routine(modified_routine)
                    
                    if saved_id:
                        modified_routine['_id'] = str(saved_id)
                        
                        # 업데이트된 전체 루틴 조회
                        updated_routines = analyzer.db.get_user_routines(session.user_id)
                        
                        bot_message = session.add_message(
                            'bot',
                            f"{selected_day}일차 루틴이 영구적으로 수정되었습니다! ✅\n\n📝 수정 내용: {modification_summary}\n\n✨ 나머지 일차는 기존대로 유지됩니다.\n\n❗ 이 수정은 영구적으로 적용되었습니다.\n\n업데이트된 전체 루틴을 확인해보세요."
                        )
                        session.update_state(SessionState.CHATTING)
                        
                        if hasattr(session, 'selected_day_permanent'):
                            delattr(session, 'selected_day_permanent')
                        
                        return self._create_response(session, bot_message, routine_data=updated_routines)
                    else:
                        raise ValueError("수정된 루틴 저장에 실패했습니다.")
                else:
                    bot_message = session.add_message(
                        'bot',
                        '요청하신 수정이 어려울 수 있습니다. 다른 방식으로 수정해보시겠어요?'
                    )
                    return self._create_response(session, bot_message)
            else:
                raise ValueError("Function calling 응답을 받지 못했습니다.")
                
        except Exception as e:
            logger.error(f"영구 단일 일차 수정 처리 중 오류: {str(e)}")
            bot_message = session.add_message(
                'bot',
                f'{selected_day}일차 루틴 영구 수정 중 오류가 발생했습니다.'
            )
            return self._create_response(session, bot_message)

    async def _process_permanent_multiple_days_modification(self, session: ChatSession, message: str, analyzer, existing_routines: List[Dict]) -> Dict:
        """여러 일차 영구 수정 처리"""
        try:
            # Function calling으로 여러 일차 영구 수정
            response = await analyzer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "사용자가 여러 일차 루틴을 영구적으로 수정하고 싶어합니다. 요청된 일차들만 수정하고 나머지는 유지해주세요."
                }, {
                    "role": "user",
                    "content": f"기존 전체 루틴: {existing_routines}\n\n영구 수정 요청: {message}"
                }],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "modify_multiple_days_routine_permanent",
                        "description": "여러 일차 운동 루틴을 영구적으로 수정합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "modified_days": {
                                    "type": "array",
                                    "description": "영구 수정된 일차들",
                                    "items": {
                                        "type": "integer"
                                    }
                                },
                                "modified_routines": {
                                    "type": "array",
                                    "description": "영구 수정된 루틴들",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {"type": "integer"},
                                            "day": {"type": "integer"},
                                            "title": {"type": "string"},
                                            "exercises": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"},
                                                        "sets": {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "id": {"type": "integer"},
                                                                    "reps": {"type": "integer"},
                                                                    "weight": {"type": "integer"},
                                                                    "time": {"type": "string"},
                                                                    "completed": {"type": "boolean"}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "modification_summary": {
                                    "type": "string",
                                    "description": "수정 내용 요약"
                                },
                                "success": {
                                    "type": "boolean",
                                    "description": "수정 성공 여부"
                                }
                            },
                            "required": ["modified_days", "modified_routines", "modification_summary", "success"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "modify_multiple_days_routine_permanent"}}
            )
            
            if response.choices[0].message.tool_calls:
                function_call = response.choices[0].message.tool_calls[0].function
                modification_result = json.loads(function_call.arguments)
                
                if modification_result.get('success', False):
                    modified_days = modification_result.get('modified_days', [])
                    modified_routines = modification_result.get('modified_routines', [])
                    modification_summary = modification_result.get('modification_summary', '')
                    
                    # 수정된 일차들만 삭제하고 새로운 루틴으로 교체
                    analyzer.db.delete_multiple_days_routines(session.user_id, modified_days)
                    
                    # 수정된 루틴들 저장
                    saved_routines = []
                    for routine in modified_routines:
                        routine['user_id'] = int(session.user_id)
                        saved_id = analyzer.db.save_routine(routine)
                        if saved_id:
                            routine['_id'] = str(saved_id)
                            saved_routines.append(routine)
                    
                    if saved_routines:
                        # 업데이트된 전체 루틴 조회
                        updated_routines = analyzer.db.get_user_routines(session.user_id)
                        
                        modified_days_text = ', '.join([f"{day}일차" for day in modified_days])
                        
                        bot_message = session.add_message(
                            'bot',
                            f"{modified_days_text} 루틴이 영구적으로 수정되었습니다! ✅\n\n📝 수정 내용: {modification_summary}\n\n✨ 나머지 일차는 기존대로 유지됩니다.\n\n❗ 이 수정은 영구적으로 적용되었습니다.\n\n업데이트된 전체 루틴을 확인해보세요."
                        )
                        session.update_state(SessionState.CHATTING)
                        
                        if hasattr(session, 'selected_day_permanent'):
                            delattr(session, 'selected_day_permanent')
                        
                        return self._create_response(session, bot_message, routine_data=updated_routines)
                    else:
                        raise ValueError("수정된 루틴 저장에 실패했습니다.")
                else:
                    bot_message = session.add_message(
                        'bot',
                        '요청하신 수정이 어려울 수 있습니다. 다른 방식으로 수정해보시겠어요?'
                    )
                    return self._create_response(session, bot_message)
            else:
                raise ValueError("Function calling 응답을 받지 못했습니다.")
                
        except Exception as e:
            logger.error(f"영구 여러 일차 수정 처리 중 오류: {str(e)}")
            bot_message = session.add_message(
                'bot',
                '여러 일차 루틴 영구 수정 중 오류가 발생했습니다.'
            )
            return self._create_response(session, bot_message)
    
    async def _handle_pdf_question(self, session: ChatSession, message: str) -> Dict:
        """PDF 질문 처리"""
        if '예' in message or 'PDF가 있어요' in message:
            bot_message = session.add_message(
                'bot',
                '인바디 PDF 파일을 업로드해주세요! 📄\n\n파일을 분석하여 더 정확한 맞춤 운동 루틴을 추천해드릴게요.'
            )
            return self._create_response(session, bot_message, show_file_upload=True)
        else:
            session.update_state(SessionState.COLLECTING_INBODY)
            session.current_question_index = 0
            question = self.INBODY_QUESTIONS[0]
            
            bot_message = session.add_message(
                'bot',
                f'인바디 정보를 수동으로 입력하도록 하겠습니다.\n\n{question["text"]}'
            )
            
            if question['type'] == 'buttons':
                return self._create_response(session, bot_message, 
                                           show_buttons=True, 
                                           button_options=question['options'])
            else:
                return self._create_response(session, bot_message, show_input=True)
    
    async def _handle_inbody_collection(self, session: ChatSession, message: str, analyzer) -> Dict:
        """인바디 정보 수집 처리"""
        current_question = self.INBODY_QUESTIONS[session.current_question_index]
        
        # 사용자 정보 처리
        processed_info = await analyzer.process_user_info_async(message, current_question['key'])
        session.set_inbody_data({current_question['key']: processed_info['value']})
        
        # 사용자 벡터DB에 저장 (user_id 포함)
        if hasattr(analyzer, 'user_vector_store') and session.user_id:
            await self._save_inbody_to_vector_db(session, analyzer)
        
        # BMI 및 BMR 계산
        self._calculate_derived_values(session)
        
        # 다음 질문으로 진행
        next_index = session.current_question_index + 1
        
        if next_index < len(self.INBODY_QUESTIONS):
            session.current_question_index = next_index
            next_question = self.INBODY_QUESTIONS[next_index]
            bot_message = session.add_message('bot', next_question['text'])
            
            if next_question['type'] == 'buttons':
                return self._create_response(session, bot_message, 
                                           show_buttons=True, 
                                           button_options=next_question['options'])
            else:
                return self._create_response(session, bot_message, show_input=True)
        else:
            # 운동 선호도 수집으로 전환
            session.update_state(SessionState.COLLECTING_WORKOUT_PREFS)
            session.current_question_index = 0
            first_workout_question = self.WORKOUT_QUESTIONS[0]
            
            bot_message = session.add_message(
                'bot',
                f'신체 정보 수집이 완료되었습니다! 👍\n\n이제 운동 선호도에 대해 알려주세요.\n\n{first_workout_question["text"]}'
            )
            
            if first_workout_question['type'] == 'buttons':
                return self._create_response(session, bot_message, 
                                           show_buttons=True, 
                                           button_options=first_workout_question['options'])
            else:
                return self._create_response(session, bot_message, show_input=True)
    
    async def _handle_workout_prefs_collection(self, session: ChatSession, message: str, analyzer) -> Dict:
        """운동 선호도 수집 처리"""
        current_question = self.WORKOUT_QUESTIONS[session.current_question_index]
        
        # 사용자 정보 처리
        processed_info = await analyzer.process_user_info_async(message, current_question['key'])
        session.set_workout_preferences({current_question['key']: processed_info['value']})
        
        # 사용자 벡터DB에 저장 (user_id 포함)
        if hasattr(analyzer, 'user_vector_store') and session.user_id:
            await self._save_preferences_to_vector_db(session, analyzer)
        
        # 다음 질문으로 진행
        next_index = session.current_question_index + 1
        
        if next_index < len(self.WORKOUT_QUESTIONS):
            session.current_question_index = next_index
            next_question = self.WORKOUT_QUESTIONS[next_index]
            bot_message = session.add_message('bot', next_question['text'])
            
            if next_question['type'] == 'buttons':
                return self._create_response(session, bot_message, 
                                           show_buttons=True, 
                                           button_options=next_question['options'])
            else:
                return self._create_response(session, bot_message, show_input=True)
        else:
            # 🔥 루틴 생성 단계 - 여기서 루틴이 제대로 저장되도록 수정
            session.update_state(SessionState.READY_FOR_RECOMMENDATION)
            return await self._generate_workout_routine(session, analyzer)
    
    async def _generate_workout_routine(self, session: ChatSession, analyzer) -> Dict:
        """🔥 핵심 수정: 운동 루틴 생성 및 저장 - UI 개선"""
        # 로딩 메시지 추가
        loading_message = session.add_message(
            'bot',
            '수집된 정보를 바탕으로 맞춤 운동 루틴을 생성하고 있습니다... ⚡'
        )
        
        try:
            # 사용자별 컨텍스트 가져오기 (user_id 기반)
            user_context = ""
            if hasattr(analyzer, 'user_vector_store') and session.user_id:
                user_context = analyzer.user_vector_store.get_user_context(
                    session.user_id, 
                    f"운동 루틴 추천 {session.workout_preferences.get('goal', '')}"
                )
            
            # 최종 인바디 데이터 구성
            final_inbody_data = {
                'gender': session.inbody_data['gender'],
                'age': int(session.inbody_data['age']),
                'height': int(session.inbody_data['height']),
                'weight': int(session.inbody_data['weight']),
                'muscle_mass': session.inbody_data.get('muscle_mass') if session.inbody_data.get('muscle_mass') != '모름' else None,
                'body_fat': session.inbody_data.get('body_fat') if session.inbody_data.get('body_fat') != '모름' else None,
                'bmi': session.inbody_data.get('bmi') if session.inbody_data.get('bmi') != '모름' else session.inbody_data.get('calculated_bmi'),
                'basal_metabolic_rate': session.inbody_data.get('basal_metabolic_rate') if session.inbody_data.get('basal_metabolic_rate') != '모름' else session.inbody_data.get('calculated_bmr')
            }
            
            # 사용자 데이터 구성 (user_id 포함하여 개인화)
            user_data = {
                'inbody': final_inbody_data,
                'preferences': session.workout_preferences,
                'user_id': session.user_id,
                'user_context': user_context
            }
            
            # 🔥 핵심 수정: 운동 루틴 생성 및 저장 처리
            routine_result = await analyzer.generate_enhanced_routine_async(user_data)
            
            if isinstance(routine_result, dict) and routine_result.get('success'):
                # 🔥 분석 결과 메시지 (텍스트로 표시)
                analysis_message = session.add_message(
                    'bot', 
                    routine_result.get('analysis', '분석이 완료되었습니다!')
                )
                
                # 🔥 운동 루틴 데이터 저장 및 UI 표시
                session.routine_data = routine_result.get('routines', [])
                session.set_existing_routines(session.routine_data)
                
                # 🔥 루틴 메시지를 'routine' 타입으로 생성하여 UI에서 특별히 렌더링
                routine_message = session.add_message(
                    'bot', 
                    f'📋 맞춤 운동 루틴 ({len(session.routine_data)}일차)이 생성되었습니다!', 
                    'routine'
                )
                
                # 🔥 대화 상태로 전환하고 추가 안내 메시지
                session.update_state(SessionState.CHATTING)
                final_message = session.add_message(
                    'bot',
                    '운동 루틴에 대해 궁금한 점이나 조정이 필요한 부분이 있으면 언제든 말씀해주세요! 💪\n\n예시:\n- "1일차 운동을 좀 더 쉽게 바꿔주세요"\n- "전체적으로 강도를 높여주세요"\n- "스쿼트 대신 다른 운동으로 바꿔주세요"'
                )
                
                # 🔥 중요: routine_data를 응답에 포함하여 프론트엔드에서 렌더링
                return self._create_response(
                    session, 
                    final_message, 
                    routine_data=session.routine_data
                )
            else:
                # Fallback 텍스트 응답
                bot_message = session.add_message('bot', routine_result)
                session.update_state(SessionState.CHATTING)
                return self._create_response(session, bot_message)
                
        except Exception as e:
            logger.error(f"운동 루틴 생성 중 오류: {str(e)}")
            error_message = session.add_message(
                'bot',
                '죄송합니다. 운동 루틴 생성 중 오류가 발생했습니다. 다시 시도해주세요.'
            )
            session.update_state(SessionState.INITIAL)
            return self._create_response(session, error_message)
    
    async def _handle_general_chat(self, session: ChatSession, message: str, analyzer) -> Dict:
        """일반 채팅 처리 - 사용자별 컨텍스트 활용"""
        # 사용자별 컨텍스트 가져오기 (user_id 기반)
        user_context = ""
        if (hasattr(analyzer, 'user_vector_store') and session.user_id and 
            session.user_id != "None" and session.user_id != "null"):
            try:
                user_context = analyzer.user_vector_store.get_user_context(session.user_id, message)
            except Exception as e:
                logger.error(f"사용자 컨텍스트 조회 실패: {str(e)}")
        
        # 컨텍스트와 함께 응답 생성
        enhanced_message = message
        if user_context:
            enhanced_message = f"사용자 컨텍스트: {user_context}\n\n사용자 질문: {message}"
        
        response = await analyzer.chat_with_bot_async(enhanced_message, use_vector_search=True)
        bot_message = session.add_message('bot', response)
        
        # 현재 루틴 데이터 포함 (수정사항 반영)
        current_routines = session.get_current_routines()
        return self._create_response(session, bot_message, routine_data=current_routines if current_routines else None)
    
    async def _save_inbody_to_vector_db(self, session: ChatSession, analyzer):
        """인바디 데이터를 사용자별 벡터DB에 저장"""
        try:
            if session.user_id and session.user_id != "None" and session.user_id != "null" and session.inbody_data:
                analyzer.user_vector_store.add_user_inbody_data(session.user_id, session.inbody_data)
                # MongoDB에도 저장
                analyzer.db.save_user_data(session.user_id, 'inbody', session.inbody_data)
                logger.info(f"사용자 {session.user_id}의 인바디 데이터 저장 완료")
        except Exception as e:
            logger.error(f"인바디 데이터 벡터DB 저장 실패: {str(e)}")
    
    async def _save_preferences_to_vector_db(self, session: ChatSession, analyzer):
        """운동 선호도를 사용자별 벡터DB에 저장"""
        try:
            if session.user_id and session.user_id != "None" and session.user_id != "null" and session.workout_preferences:
                analyzer.user_vector_store.add_user_preferences(session.user_id, session.workout_preferences)
                # MongoDB에도 저장
                analyzer.db.save_user_data(session.user_id, 'preferences', session.workout_preferences)
                logger.info(f"사용자 {session.user_id}의 운동 선호도 저장 완료")
        except Exception as e:
            logger.error(f"운동 선호도 벡터DB 저장 실패: {str(e)}")
    
    def _calculate_derived_values(self, session: ChatSession):
        """BMI 및 BMR 계산"""
        try:
            # BMI 계산
            if ('weight' in session.inbody_data and 'height' in session.inbody_data and 
                session.inbody_data['weight'] and session.inbody_data['height']):
                
                weight = float(session.inbody_data['weight'])
                height = float(session.inbody_data['height'])
                bmi = self._calculate_bmi(weight, height)
                if bmi:
                    session.set_inbody_data({'calculated_bmi': bmi})
            
            # BMR 계산
            if ('age' in session.inbody_data and 'weight' in session.inbody_data and 
                'height' in session.inbody_data and 'gender' in session.inbody_data):
                
                bmr = self._calculate_bmr(
                    session.inbody_data['gender'],
                    float(session.inbody_data['weight']),
                    float(session.inbody_data['height']),
                    int(session.inbody_data['age'])
                )
                if bmr:
                    session.set_inbody_data({'calculated_bmr': bmr})
                    
        except Exception as e:
            logger.error(f"수치 계산 중 오류: {str(e)}")
    
    def _calculate_bmi(self, weight: float, height: float) -> float:
        """BMI 계산"""
        if not weight or not height:
            return None
        height_in_meters = height / 100
        return round((weight / (height_in_meters * height_in_meters)), 1)
    
    def _calculate_bmr(self, gender: str, weight: float, height: float, age: int) -> int:
        """BMR 계산"""
        if not weight or not height or not age:
            return None
        
        if gender == '남성':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        elif gender == '여성':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        else:
            return None
        
        return int(bmr)
    
    def _create_response(self, session: ChatSession, bot_message: Dict, **kwargs) -> Dict:
        """응답 생성"""
        return {
            'success': True,
            'session_id': session.session_id,
            'session_info': session.get_session_info(),
            'messages': session.messages,
            'latest_message': bot_message,
            **kwargs
        }
    
    async def process_inbody_pdf(self, session_id: str, inbody_data: Dict, user_id: str = None) -> Dict:
        """인바디 PDF 처리"""
        session = self.get_or_create_session(session_id, user_id)
        
        # 인바디 데이터 저장
        session.set_inbody_data(inbody_data)
        
        # 사용자별 벡터DB에 저장
        if hasattr(session, 'user_id') and session.user_id:
            try:
                # analyzer는 process_inbody_pdf 호출부에서 전달받아야 함
                pass
            except Exception as e:
                logger.error(f"PDF 인바디 데이터 벡터DB 저장 실패: {str(e)}")
        
        # 추출된 데이터 표시
        formatted_data = self._format_inbody_data(inbody_data)
        bot_message = session.add_message(
            'bot',
            f'PDF 분석이 완료되었습니다! ✅\n\n추출된 인바디 정보:\n{formatted_data}'
        )
        
        # 운동 선호도 질문으로 전환 (첫 번째 질문)
        session.update_state(SessionState.COLLECTING_WORKOUT_PREFS)
        session.current_question_index = 0
        first_workout_question = self.WORKOUT_QUESTIONS[0]
        
        next_message = session.add_message(
            'bot',
            f'이제 운동 선호도에 대해 몇 가지 질문을 드릴게요.\n\n{first_workout_question["text"]}'
        )
        
        # 질문 타입에 따라 응답 형태 결정
        if first_workout_question['type'] == 'buttons':
            return self._create_response(session, next_message, 
                                       show_buttons=True, 
                                       button_options=first_workout_question['options'])
        else:
            return self._create_response(session, next_message, show_input=True)
    
    def _format_inbody_data(self, data: Dict) -> str:
        """인바디 데이터 포맷팅"""
        korean_labels = {
            'gender': '성별',
            'age': '나이',
            'height': '신장',
            'weight': '체중',
            'muscle_mass': '골격근량',
            'body_fat': '체지방률',
            'bmi': 'BMI',
            'basal_metabolic_rate': '기초대사량'
        }
        
        formatted_lines = []
        for key, value in data.items():
            if value is not None:
                label = korean_labels.get(key, key)
                unit = self._get_unit_for_field(key)
                formatted_lines.append(f"- {label}: {value}{unit}")
        
        return '\n'.join(formatted_lines)
    
    def _get_unit_for_field(self, field: str) -> str:
        """필드별 단위 반환"""
        units = {
            'height': 'cm',
            'weight': 'kg',
            'muscle_mass': 'kg',
            'body_fat': '%',
            'basal_metabolic_rate': 'kcal',
            'age': '세'
        }
        return units.get(field, '')
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """세션 가져오기"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"세션 삭제: {session_id}")
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """오래된 세션 정리"""
        current_time = get_korea_time()  # ✅ 한국 시간 적용
        
        to_delete = []
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > timedelta(hours=max_age_hours):
                to_delete.append(session_id)
        
        for session_id in to_delete:
            self.delete_session(session_id)
        
        if to_delete:
            logger.info(f"{len(to_delete)}개의 오래된 세션을 정리했습니다. (한국 시간: {get_korea_time()})")

# 전역 세션 매니저 인스턴스
session_manager = ChatSessionManager()