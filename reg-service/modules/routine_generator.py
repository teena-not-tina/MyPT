import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from openai import OpenAI
from config.settings import OPENAI_API_KEY, SYSTEM_PROMPT, GPT_MODEL, GPT_TEMPERATURE, CHATBOT_PROMPT         
import glob
from modules.vector_store import VectorStore
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)

class AIAnalyzer:
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.conversation_history = []
        
        # VectorStore 초기화
        self.vector_store = VectorStore(
            collection_name="fitness_knowledge_base",
            openai_api_key=OPENAI_API_KEY
        )
        
        # 문서 로딩 상태 관리
        self._documents_loaded = False
        self._loading_in_progress = False
        self._loading_thread = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # 백그라운드에서 문서 초기화 시작
        self._start_background_initialization()
    
    def _start_background_initialization(self):
        """백그라운드에서 VectorStore 초기화 시작"""
        self._loading_thread = threading.Thread(
            target=self._initialize_vector_store_sync,
            daemon=True  # 메인 프로세스 종료 시 함께 종료
        )
        self._loading_thread.start()
    
    def _initialize_vector_store_sync(self):
        """동기적 VectorStore 초기화 (백그라운드 스레드에서 실행)"""
        try:
            self._loading_in_progress = True
            #PDF 파일들 찾기
            pdf_files = glob.glob("./data/*.pdf")
            existing_files = [f for f in pdf_files if self._file_exists(f)]
            
            if not existing_files:
                print("추가할 PDF 파일이 없습니다.")
                self._documents_loaded = True
                return

            processed_files = self.vector_store.get_processed_files() if hasattr(self.vector_store, 'get_processed_files') else []

            files_to_add = [f for f in existing_files if f not in processed_files]
            # 기존에 문서가 있는지 확인
            stats = self.vector_store.get_collection_stats()
            
            if files_to_add:
                print(f"백그라운드에서 VectorStore에 {len(files_to_add)}개 새 문서 추가 중...")
                self.vector_store.add_documents(files_to_add, extract_images=True)
                print("새 문서 추가 완료")
            else:
                print("모든 PDF 파일이 이미 VectorStore에 존재합니다.")
        
        # 최종 통계
            stats = self.vector_store.get_collection_stats()
            print(f"총 문서 수: {stats.get('total_documents', 0)}")
        
            self._documents_loaded = True

        except Exception as e:
            print(f"VectorStore 초기화 중 오류: {e}")
        finally:
            self._loading_in_progress = False
    
    async def _initialize_vector_store_async(self):
        """비동기 VectorStore 초기화"""
        loop = asyncio.get_event_loop()
        
        try:
            self._loading_in_progress = True
            
            # CPU 집약적 작업을 별도 스레드에서 실행
            await loop.run_in_executor(
                self._executor, 
                self._initialize_vector_store_sync
            )
                
        except Exception as e:
            print(f"비동기 VectorStore 초기화 중 오류: {e}")
        finally:
            self._loading_in_progress = False
    
    def _file_exists(self, filepath: str) -> bool:
        """파일 존재 여부 확인"""
        try:
            import os
            return os.path.exists(filepath)
        except:
            return False
    
    def get_loading_status(self) -> Dict[str, Any]:
        """문서 로딩 상태 반환"""
        return {
            "documents_loaded": self._documents_loaded,
            "loading_in_progress": self._loading_in_progress,
            "can_use_vector_search": self._documents_loaded
        }
    
    def wait_for_documents(self, timeout: float = 30.0) -> bool:
        """문서 로딩 완료까지 대기 (선택적)"""
        if self._documents_loaded:
            return True
            
        if self._loading_thread and self._loading_thread.is_alive():
            self._loading_thread.join(timeout=timeout)
            
        return self._documents_loaded
        
    def analyze_inbody_data(self, inbody_text: str, use_vector_search: bool = True) -> str:
        """InBody 데이터 분석 및 운동 루틴 추천 (선택적 VectorStore 활용)"""
        
        relevant_context = ""
        
        # VectorStore 사용 여부 결정
        if use_vector_search and self._documents_loaded:
            relevant_context = self._get_relevant_context_for_inbody(inbody_text)
        elif use_vector_search and self._loading_in_progress:
            print("문서 로딩 중입니다. 기본 분석으로 진행합니다.")
        
        # 시스템 프롬프트 생성
        enhanced_system_prompt = self._create_enhanced_system_prompt(relevant_context)
        
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": f"다음 InBody 검사 결과를 분석하여 운동 루틴을 추천해주세요:\\n\\n{inbody_text}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=GPT_TEMPERATURE,
                max_tokens=2000
            )
            
            recommendation = response.choices[0].message.content
            
            if not recommendation:
                recommendation = "분석 결과를 생성할 수 없습니다."

            # 대화 기록 저장
            self.conversation_history = messages + [
                {"role": "assistant", "content": recommendation}
            ]
            
            return recommendation
            
        except Exception as e:
            raise RuntimeError(f"AI 분석 실패: {str(e)}")
    
    async def analyze_inbody_data_async(self, inbody_text: str, use_vector_search: bool = True) -> str:
        """비동기 InBody 데이터 분석"""
        loop = asyncio.get_event_loop()
        
        # CPU 집약적 작업을 별도 스레드에서 실행
        return await loop.run_in_executor(
            self._executor,
            self.analyze_inbody_data,
            inbody_text,
            use_vector_search
        )
    
    def _get_relevant_context_for_inbody(self, inbody_text: str) -> str:
        """InBody 데이터 기반 관련 컨텍스트 검색"""
        if not self._documents_loaded:
            return ""
            
        try:
            search_query = f"체성분 분석 운동 루틴 근력 훈련 체지방 감소 근육량 증가 {inbody_text[:200]}"
            
            relevant_context = self.vector_store.get_relevant_context(
                search_query, 
                max_context_length=1500
            )
            
            return relevant_context if relevant_context.strip() else ""
            
        except Exception as e:
            print(f"컨텍스트 검색 중 오류: {e}")
            return ""
    
    def _create_enhanced_system_prompt(self, context: str) -> str:
        """컨텍스트를 포함한 향상된 시스템 프롬프트 생성"""
        if context.strip():
            enhanced_prompt = f"""{SYSTEM_PROMPT}

            추가 전문 참고 자료:
            {context}

            위의 전문 자료를 참고하여 더욱 과학적이고 근거 있는 운동 루틴을 제안해주세요. 
            전문 자료의 내용과 일치하는 부분이 있다면 해당 내용을 인용하여 신뢰성을 높여주세요."""
        else:
            enhanced_prompt = SYSTEM_PROMPT
        
        return enhanced_prompt
    
    def chat_with_bot(self, user_message: str, use_vector_search: bool = True) -> str:
        """챗봇과의 대화 처리 (선택적 VectorStore 활용)"""
        if not self.conversation_history:
            return "먼저 InBody 분석을 진행해주세요."
        
        additional_context = ""
        
        # VectorStore 사용 여부 결정
        if use_vector_search and self._documents_loaded:
            additional_context = self._get_relevant_context_for_chat(user_message)
        
        enhanced_chatbot_prompt = self._create_enhanced_chatbot_prompt(additional_context)
        
        chatbot_messages = [
            {"role": "system", "content": enhanced_chatbot_prompt}
        ] + self.conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=chatbot_messages,
                temperature=GPT_TEMPERATURE,
                max_tokens=1500
            )
            
            bot_response = response.choices[0].message.content
            
            if bot_response is None:
                bot_response = "죄송합니다, 응답을 생성할 수 없습니다."

            self.conversation_history.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": bot_response}
            ])
            
            return bot_response
            
        except Exception as e:
            return f"챗봇 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def chat_with_bot_async(self, user_message: str, use_vector_search: bool = True) -> str:
        """비동기 챗봇 대화"""
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            self._executor,
            self.chat_with_bot,
            user_message,
            use_vector_search
        )
    
    def _get_relevant_context_for_chat(self, user_message: str) -> str:
        """채팅 메시지 기반 관련 컨텍스트 검색"""
        if not self._documents_loaded:
            return ""
            
        try:
            relevant_context = self.vector_store.get_relevant_context(
                f"{user_message} 운동 피트니스 건강", 
                max_context_length=1000
            )
            
            return relevant_context if relevant_context.strip() else ""
            
        except Exception as e:
            print(f"채팅 컨텍스트 검색 중 오류: {e}")
            return ""
    
    def _create_enhanced_chatbot_prompt(self, context: str) -> str:
        """컨텍스트를 포함한 향상된 챗봇 프롬프트 생성"""
        if context.strip():
            enhanced_prompt = f"""{CHATBOT_PROMPT}

            관련 전문 정보:
            {context}

            위의 전문 정보를 참고하여 더욱 정확하고 전문적인 답변을 제공해주세요."""
        else:
            enhanced_prompt = CHATBOT_PROMPT
        
        return enhanced_prompt
    
    async def generate_enhanced_routine_async(self, user_query: str, inbody_data: str) -> str:
        """비동기 향상된 루틴 생성"""
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            self._executor,
            self.generate_enhanced_routine,
            user_query,
            inbody_data
        )
    
    def generate_enhanced_routine(self, user_query: str, inbody_data: str) -> str:
        """개별적으로 호출 가능한 향상된 루틴 생성 메서드"""
        try:
            relevant_context = ""
            
            if self._documents_loaded:
                relevant_context = self.vector_store.get_relevant_context(
                    f"{user_query} 운동 루틴 근력 체지방", 
                    max_context_length=2000
                )
            
            enhanced_prompt = f"""
                사용자 요청: {user_query}
                InBody 데이터: {inbody_data}

                전문 참고 자료:
                {relevant_context}

                위 전문 자료를 참고하여 과학적 근거가 있는 운동 루틴을 제안해주세요.
                """
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": enhanced_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=GPT_TEMPERATURE,
                max_tokens=2000
            )
            
            return response.choices[0].message.content or "루틴 생성에 실패했습니다."
            
        except Exception as e:
            return f"향상된 루틴 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def add_documents_to_vector_store_async(self, pdf_paths: list) -> bool:
        """비동기 문서 추가"""
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            self._executor,
            self.add_documents_to_vector_store,
            pdf_paths
        )
    
    def add_documents_to_vector_store(self, pdf_paths: list) -> bool:
        """런타임에 새로운 문서를 VectorStore에 추가"""
        try:
            added_count = self.vector_store.add_documents(pdf_paths, extract_images=True)
            if added_count > 0:
                self._documents_loaded = True
            return added_count > 0
        except Exception as e:
            print(f"문서 추가 실패: {e}")
            return False
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """대화 요약 정보 반환"""
        vector_stats = {}
        try:
            if self._documents_loaded:
                vector_stats = self.vector_store.get_collection_stats()
        except:
            pass
            
        return {
            "message_count": len(self.conversation_history),
            "has_recommendation": len(self.conversation_history) > 2,
            "last_recommendation": self.conversation_history[1]["content"] if len(self.conversation_history) > 1 else None,
            "vector_store_stats": vector_stats,
            "loading_status": self.get_loading_status()
        }
    
    def __del__(self):
        """소멸자 - 스레드 풀 정리"""
        try:
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=False)
        except:
            pass