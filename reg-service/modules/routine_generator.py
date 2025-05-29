import asyncio
import hashlib
import threading
import hashlib
import os
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List
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
        
        # 문서 메타데이터 파일 경로
        self.metadata_file = "./data/.vector_store_metadata.json"
        
        # 문서 로딩 상태 관리
        self._documents_loaded = False
        self._loading_in_progress = False
        self._loading_thread = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # 백그라운드에서 문서 초기화 시작
        self._start_background_initialization()
    
    def _get_file_hash(self, file_path: str) -> str:
        """파일의 해시값(MD5) 반환"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        try:
            stat = os.stat(filepath)
            stored = self._load_stored_metadata().get(filepath, {})
            # 수정시간이 같으면 기존 해시 재사용
            if stored and stat.st_mtime == stored.get("modified_time"):
                file_hash = stored.get("hash")
            else:
                file_hash = self._get_file_hash(filepath)
            return {
                "path": filepath,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "hash": file_hash
            }
        except Exception as e:
            print(f"파일 메타데이터 생성 실패 {filepath}: {e}")
            return {}
    
    def _load_stored_metadata(self) -> Dict[str, Dict[str, Any]]:
        """저장된 메타데이터 로드"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"메타데이터 로드 실패: {e}")
        return {}
    
    def _save_metadata(self, metadata: Dict[str, Dict[str, Any]]):
        """메타데이터 저장"""
        try:
            os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"메타데이터 저장 실패: {e}")
    
    def _has_files_changed(self, current_files: List[str], stored_metadata: Dict[str, Dict[str, Any]]) -> tuple[bool, List[str], List[str]]:
        """
        파일 변경 여부 확인
        Returns: (has_changed, new_files, changed_files)
        """
        new_files = []
        changed_files = []
        
        for filepath in current_files:
            current_metadata = self._get_file_metadata(filepath)
            stored_file_metadata = stored_metadata.get(filepath, {})
            
            if not stored_file_metadata:
                # 새로운 파일
                new_files.append(filepath)
            else:
                # 기존 파일의 변경 여부 확인
                if (current_metadata.get("hash") != stored_file_metadata.get("hash") or
                    current_metadata.get("size") != stored_file_metadata.get("size") or
                    current_metadata.get("modified_time") != stored_file_metadata.get("modified_time")):
                    changed_files.append(filepath)
        
        has_changed = len(new_files) > 0 or len(changed_files) > 0
        return has_changed, new_files, changed_files
    
    def _check_vector_store_exists(self) -> bool:
        """VectorStore에 데이터가 존재하는지 확인"""
        try:
            stats = self.vector_store.get_collection_stats()
            total_docs = stats.get('total_documents', 0)
            return total_docs > 0
        except Exception as e:
            print(f"VectorStore 상태 확인 실패: {e}")
            return False
    
    def _initialize_vector_store_sync(self):
        """동기적 VectorStore 초기화 (백그라운드 스레드에서 실행)"""
        try:
            self._loading_in_progress = True
            
            # PDF 파일들 찾기
            pdf_files = glob.glob("./data/*.pdf")
            existing_files = [f for f in pdf_files if self._file_exists(f)]
            
            if not existing_files:
                print("추가할 PDF 파일이 없습니다.")
                self._documents_loaded = True
                return

            # 저장된 메타데이터 로드
            stored_metadata = self._load_stored_metadata()
            
            # 파일 변경 여부 확인
            has_changed, new_files, changed_files = self._has_files_changed(existing_files, stored_metadata)
            
            # VectorStore에 데이터가 존재하는지 확인
            vector_store_exists = self._check_vector_store_exists()
            
            print(f"VectorStore 존재 여부: {vector_store_exists}")
            print(f"새로운 파일: {len(new_files)}개")
            print(f"변경된 파일: {len(changed_files)}개")
            
            if vector_store_exists and not has_changed:
                # 기존 데이터가 있고 파일에 변경이 없으면 기존 데이터 사용
                print("기존 VectorStore 데이터를 사용합니다.")
                self._documents_loaded = True
                return
            
            # 새로운 파일이나 변경된 파일이 있으면 처리
            files_to_process = new_files + changed_files
            
            if files_to_process:
                print(f"VectorStore에 {len(files_to_process)}개 문서 처리 중...")
                
                # 변경된 파일이 있으면 해당 파일의 기존 데이터 삭제 (VectorStore가 지원하는 경우)
                if changed_files:
                    for changed_file in changed_files:
                        try:
                            # VectorStore에서 해당 파일의 기존 데이터 삭제
                            if hasattr(self.vector_store, 'delete_documents_by_source'):
                                self.vector_store.delete_documents_by_source(changed_file)
                                print(f"기존 데이터 삭제: {changed_file}")
                        except Exception as e:
                            print(f"기존 데이터 삭제 실패 {changed_file}: {e}")
                
                # 새로운/변경된 문서 추가
                self.vector_store.add_documents(files_to_process, extract_images=True)
                print("문서 처리 완료")
                
                # 메타데이터 업데이트
                current_metadata = stored_metadata.copy()
                for filepath in files_to_process:
                    current_metadata[filepath] = self._get_file_metadata(filepath)
                
                self._save_metadata(current_metadata)
                print("메타데이터 업데이트 완료")
            
            elif vector_store_exists:
                print("모든 파일이 이미 VectorStore에 최신 상태로 존재합니다.")
            else:
                # VectorStore가 비어있지만 처리할 파일도 없는 경우
                print("처리할 파일이 없습니다.")
        
            # 최종 통계
            stats = self.vector_store.get_collection_stats()
            print(f"VectorStore 총 문서 수: {stats.get('total_documents', 0)}")
        
            self._documents_loaded = True

        except Exception as e:
            print(f"VectorStore 초기화 중 오류: {e}")
        finally:
            self._loading_in_progress = False
    
    def _start_background_initialization(self):
        """백그라운드에서 VectorStore 초기화 시작"""
        self._loading_thread = threading.Thread(
            target=self._initialize_vector_store_sync,
            daemon=True  # 메인 프로세스 종료 시 함께 종료
        )
        self._loading_thread.start()
    
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
    
    def force_reload_documents(self) -> bool:
        """강제로 문서 재로딩 (개발/테스트용)"""
        try:
            # 메타데이터 파일 삭제
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            
            # VectorStore 초기화 (컬렉션 삭제 후 재생성)
            if hasattr(self.vector_store, 'clear_collection'):
                self.vector_store.clear_collection()
            
            # 상태 초기화
            self._documents_loaded = False
            
            # 재초기화 시작
            self._start_background_initialization()
            
            return True
        except Exception as e:
            print(f"강제 재로딩 실패: {e}")
            return False
    
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
                max_tokens=1500
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
                max_context_length=700
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
                max_tokens=1500
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
                # 메타데이터 업데이트
                stored_metadata = self._load_stored_metadata()
                for filepath in pdf_paths:
                    stored_metadata[filepath] = self._get_file_metadata(filepath)
                self._save_metadata(stored_metadata)
                
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