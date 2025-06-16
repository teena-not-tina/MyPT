import asyncio
import hashlib
import threading
import os
import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List
from openai import OpenAI
import openai
from config.settings import OPENAI_API_KEY, SYSTEM_PROMPT, GPT_MODEL, GPT_TEMPERATURE, CHATBOT_PROMPT         
import glob
from modules.vector_store import VectorStore
from modules.user_vector_store import UserVectorStore
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
import logging
from database.db_config import DatabaseHandler
from datetime import datetime, timezone

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIAnalyzer:
    
    def __init__(self):
        self.client = openai.AsyncClient(api_key=OPENAI_API_KEY)
        self.conversation_history = []
        self.db = DatabaseHandler()
        
        # 기존 VectorStore 초기화 (일반 피트니스 지식)
        self.vector_store = VectorStore(
            collection_name="fitness_knowledge_base",
            openai_api_key=OPENAI_API_KEY
        )
        
        # 사용자 전용 VectorStore 초기화 (개인 데이터)
        self.user_vector_store = UserVectorStore(
            collection_name="user_personal_data",
            persist_directory="./user_chroma_db",
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
    
    async def identify_intent(self, message: str) -> Dict[str, Any]:
        """Function Calling을 사용하여 사용자 의도 파악 (식단 제거)"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "사용자의 의도를 정확히 파악하세요."},
                    {"role": "user", "content": message}
                ],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "identify_user_intent",
                        "description": "사용자의 메시지에서 의도를 파악합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intent": {
                                    "type": "string",
                                    "enum": ["workout_recommendation", "general_chat"],
                                    "description": "사용자의 의도 (운동 추천, 일반 채팅)"
                                },
                                "has_pdf": {
                                    "type": "boolean",
                                    "description": "PDF 파일 보유/언급 여부"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "의도 파악 확신도 (0-1)"
                                }
                            },
                            "required": ["intent", "has_pdf", "confidence"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "identify_user_intent"}}
            )
            
            function_response = response.choices[0].message.tool_calls[0].function
            return json.loads(function_response.arguments)

        except Exception as e:
            logger.error(f"의도 파악 중 오류 발생: {str(e)}")
            return {
                "intent": "general_chat",
                "has_pdf": False,
                "confidence": 0.0
            }
    
    def _get_file_hash(self, file_path: str) -> str:
        """파일의 해시값(MD5) 반환"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError) as e:
            logger.error(f"파일 해시 계산 실패 {file_path}: {e}")
            return "error_hash"
        except Exception as e:
            logger.error(f"예상치 못한 해시 계산 오류 {file_path}: {e}")
            return "unknown_hash"
    
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
            logger.error(f"파일 메타데이터 생성 실패 {filepath}: {e}")
            return {}
    
    def _load_stored_metadata(self) -> Dict[str, Dict[str, Any]]:
        """저장된 메타데이터 로드"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"메타데이터 로드 실패: {e}")
        return {}
    
    def _save_metadata(self, metadata: Dict[str, Dict[str, Any]]):
        """메타데이터 저장"""
        try:
            os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")
    
    def _has_files_changed(self, current_files: List[str], stored_metadata: Dict[str, Dict[str, Any]]) -> tuple:
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
        return (has_changed, new_files, changed_files)
    
    def _check_vector_store_exists(self) -> bool:
        """VectorStore에 데이터가 존재하는지 확인"""
        try:
            stats = self.vector_store.get_collection_stats()
            total_docs = stats.get('total_documents', 0)
            return total_docs > 0
        except Exception as e:
            logger.error(f"VectorStore 상태 확인 실패: {e}")
            return False
    
    def _initialize_vector_store_sync(self):
        """동기적 VectorStore 초기화 (백그라운드 스레드에서 실행)"""
        try:
            self._loading_in_progress = True
            
            # PDF 파일들 찾기
            pdf_files = glob.glob("./data/*.pdf")
            existing_files = [f for f in pdf_files if self._file_exists(f)]
            
            if not existing_files:
                logger.info("추가할 PDF 파일이 없습니다.")
                self._documents_loaded = True
                return

            # 저장된 메타데이터 로드
            stored_metadata = self._load_stored_metadata()
            
            # 파일 변경 여부 확인
            has_changed, new_files, changed_files = self._has_files_changed(existing_files, stored_metadata)
            
            # VectorStore에 데이터가 존재하는지 확인
            vector_store_exists = self._check_vector_store_exists()
            
            logger.info(f"VectorStore 존재 여부: {vector_store_exists}")
            logger.info(f"새로운 파일: {len(new_files)}개")
            logger.info(f"변경된 파일: {len(changed_files)}개")
            
            if vector_store_exists and not has_changed:
                # 기존 데이터가 있고 파일에 변경이 없으면 기존 데이터 사용
                logger.info("기존 VectorStore 데이터를 사용합니다.")
                self._documents_loaded = True
                return
            
            # 새로운 파일이나 변경된 파일이 있으면 처리
            files_to_process = new_files + changed_files
            
            if files_to_process:
                logger.info(f"VectorStore에 {len(files_to_process)}개 문서 처리 중...")
                
                # 변경된 파일이 있으면 해당 파일의 기존 데이터 삭제
                if changed_files:
                    for changed_file in changed_files:
                        try:
                            if hasattr(self.vector_store, 'delete_documents_by_source'):
                                self.vector_store.delete_documents_by_source(changed_file)
                                logger.info(f"기존 데이터 삭제: {changed_file}")
                        except Exception as e:
                            logger.error(f"기존 데이터 삭제 실패 {changed_file}: {e}")
                
                # 새로운/변경된 문서 추가
                self.vector_store.add_documents(files_to_process, extract_images=True)
                logger.info("문서 처리 완료")
                
                # 메타데이터 업데이트
                current_metadata = stored_metadata.copy()
                for filepath in files_to_process:
                    current_metadata[filepath] = self._get_file_metadata(filepath)
                
                self._save_metadata(current_metadata)
                logger.info("메타데이터 업데이트 완료")
            
            elif vector_store_exists:
                logger.info("모든 파일이 이미 VectorStore에 최신 상태로 존재합니다.")
            else:
                logger.info("처리할 파일이 없습니다.")
        
            # 최종 통계
            stats = self.vector_store.get_collection_stats()
            logger.info(f"VectorStore 총 문서 수: {stats.get('total_documents', 0)}")
        
            self._documents_loaded = True

        except Exception as e:
            logger.error(f"VectorStore 초기화 중 오류: {e}")
        finally:
            self._loading_in_progress = False
    
    def _start_background_initialization(self):
        """백그라운드에서 VectorStore 초기화 시작"""
        self._loading_thread = threading.Thread(
            target=self._initialize_vector_store_sync,
            daemon=True
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
            logger.error(f"비동기 VectorStore 초기화 중 오류: {e}")
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
        """강제로 문서 재로딩"""
        try:
            # 메타데이터 파일 삭제
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            
            # VectorStore 초기화
            if hasattr(self.vector_store, 'clear_collection'):
                self.vector_store.clear_collection()
            
            # 상태 초기화
            self._documents_loaded = False
            
            # 재초기화 시작
            self._start_background_initialization()
            
            return True
        except Exception as e:
            logger.error(f"강제 재로딩 실패: {e}")
            return False
    
    def wait_for_documents(self, timeout: float = 30.0) -> bool:
        """문서 로딩 완료까지 대기"""
        if self._documents_loaded:
            return True
            
        if self._loading_thread and self._loading_thread.is_alive():
            self._loading_thread.join(timeout=timeout)
            
        return self._documents_loaded

    def _extract_and_parse_json(self, text: str):
        """다양한 방법으로 JSON을 추출하고 파싱하는 헬퍼 메서드"""
        
        # 방법 1: 완전한 JSON 배열 패턴
        json_match = re.search(r"\[\s*{[\s\S]*?}\s*\]", text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group().strip()
                logger.debug(f"방법1 - 추출된 JSON 문자열: {json_str[:200]}...")
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.debug(f"방법1 실패: {e}")

        # 방법 2: 시작과 끝 대괄호 찾기
        start_idx = text.find('[')
        end_idx = text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                json_str = text[start_idx:end_idx + 1]
                logger.debug(f"방법2 - 추출된 JSON 문자열: {json_str[:200]}...")
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.debug(f"방법2 실패: {e}")

        # 방법 3: JSON 수정 시도
        if start_idx != -1:
            try:
                partial_json = text[start_idx:]
                fixed_json = self._attempt_json_repair(partial_json)
                if fixed_json:
                    logger.debug(f"방법3 - 수정된 JSON: {fixed_json[:200]}...")
                    return json.loads(fixed_json)
            except json.JSONDecodeError as e:
                logger.debug(f"방법3 실패: {e}")

        # 방법 4: 라인별로 JSON 구조 재구성
        try:
            reconstructed = self._reconstruct_json_from_lines(text)
            if reconstructed:
                logger.debug(f"방법4 - 재구성된 JSON: {reconstructed[:200]}...")
                return json.loads(reconstructed)
        except json.JSONDecodeError as e:
            logger.debug(f"방법4 실패: {e}")

        return None

    def _attempt_json_repair(self, partial_json: str) -> Optional[str]:
        """불완전한 JSON 수정 시도"""
        try:
            # 기본적인 JSON 수정 로직
            fixed = partial_json.strip()
            
            # 끝에 누락된 괄호 추가
            open_brackets = fixed.count('[') - fixed.count(']')
            open_braces = fixed.count('{') - fixed.count('}')
            
            if open_brackets > 0:
                fixed += ']' * open_brackets
            if open_braces > 0:
                fixed += '}' * open_braces
                
            return fixed
        except:
            return None

    def _reconstruct_json_from_lines(self, text: str) -> Optional[str]:
        """라인별로 JSON 구조 재구성"""
        try:
            lines = text.split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                line = line.strip()
                if '[' in line or '{' in line:
                    in_json = True
                    json_lines.append(line)
                elif in_json:
                    json_lines.append(line)
                    if ']' in line or '}' in line:
                        break
            
            if json_lines:
                return '\n'.join(json_lines)
        except:
            pass
        return None
    
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
            logger.error(f"컨텍스트 검색 중 오류: {e}")
            return ""
    
    def _create_enhanced_system_prompt(self, context: str, system_prompt: str) -> str:
        """컨텍스트를 포함한 향상된 시스템 프롬프트 생성"""
        if context.strip():
            enhanced_prompt = f"""{system_prompt}

            추가 전문 참고 자료:
            {context}

            위의 전문 자료를 참고하여 더욱 과학적이고 근거 있는 운동 루틴을 제안해주세요. 
            전문 자료의 내용과 일치하는 부분이 있다면 해당 내용을 인용하여 신뢰성을 높여주세요."""
        else:
            enhanced_prompt = system_prompt
        
        return enhanced_prompt
    
    def chat_with_bot(self, user_message: str, use_vector_search: bool = True) -> str:
        """챗봇과의 대화 처리 (동기식)"""
        additional_context = ""
        
        if use_vector_search and self._documents_loaded:
            additional_context = self._get_relevant_context_for_chat(user_message)
        
        enhanced_chatbot_prompt = self._create_enhanced_chatbot_prompt(additional_context)
        
        chatbot_messages = [
            {"role": "system", "content": enhanced_chatbot_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=chatbot_messages,
                temperature=GPT_TEMPERATURE,
                max_tokens=1500
            )
            
            bot_response = response.choices[0].message.content
            
            if bot_response is None:
                bot_response = "죄송합니다, 응답을 생성할 수 없습니다."

            return bot_response
            
        except Exception as e:
            logger.error(f"챗봇 응답 생성 중 오류: {str(e)}")
            return f"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
    
    async def chat_with_bot_async(self, user_message: str, use_vector_search: bool = True) -> str:
        """비동기 챗봇 대화 - 사용자 컨텍스트 통합"""
        try:
            additional_context = ""
            
            # 일반 피트니스 지식 검색
            if use_vector_search and self._documents_loaded:
                additional_context = self._get_relevant_context_for_chat(user_message)
            
            enhanced_chatbot_prompt = self._create_enhanced_chatbot_prompt(additional_context)
            
            # 간단한 대화 처리
            messages = [
                {"role": "system", "content": enhanced_chatbot_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=GPT_TEMPERATURE,
                max_tokens=1000
            )
            
            bot_response = response.choices[0].message.content
            
            if bot_response is None:
                bot_response = "죄송합니다, 응답을 생성할 수 없습니다."

            return bot_response
            
        except Exception as e:
            logger.error(f"챗봇 응답 생성 중 오류: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
    
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
            logger.error(f"채팅 컨텍스트 검색 중 오류: {e}")
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
    
    async def process_user_info_async(self, answer: str, question_type: str) -> Dict[str, Any]:
        """사용자 응답 정보 처리"""
        try:
            messages = [
                {"role": "system", "content": "사용자의 답변에서 관련 정보를 정확히 추출하세요."},
                {"role": "user", "content": f"질문 유형: {question_type}\n답변: {answer}"}
            ]

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "extract_user_info",
                        "description": "사용자 답변에서 정보 추출",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"},
                                "unit": {"type": "string"},
                                "normalized": {"type": "boolean"}
                            }
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "extract_user_info"}}
            )
            
            function_response = response.choices[0].message.tool_calls[0].function
            return json.loads(function_response.arguments)
        except Exception as e:
            logger.error(f"사용자 정보 처리 중 오류: {str(e)}")
            return {"value": answer, "unit": None, "normalized": False}
    
    def _create_routine_system_prompt(self, user_data: Dict[str, Any]) -> str:
        """운동 루틴 시스템 프롬프트 생성 - 사용자 컨텍스트 포함"""
        try:
            inbody_data = user_data.get("inbody", {})
            preferences = user_data.get("preferences", {})
            user_context = user_data.get("user_context", "")
            user_id = user_data.get("user_id", "Unknown")
            
            # JSON 직렬화를 안전하게 처리
            try:
                inbody_json = json.dumps(inbody_data, ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                logger.error(f"InBody 데이터 직렬화 실패: {e}")
                inbody_json = str(inbody_data)
            
            try:
                preferences_json = json.dumps(preferences, ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                logger.error(f"Preferences 데이터 직렬화 실패: {e}")
                preferences_json = str(preferences)
            
            base_prompt = f"""다음 정보를 바탕으로 맞춤형 운동 루틴을 생성해주세요:

    [사용자 ID] {user_id}

    [인바디 정보]
    {inbody_json}

    [운동 선호도]
    {preferences_json}"""
            
            # 사용자 컨텍스트가 있으면 추가
            if user_context and user_context.strip():
                context_section = f"""

    [사용자 개인 데이터 컨텍스트]
    {user_context}

    위의 개인 데이터를 참고하여 더욱 개인화된 운동 루틴을 제공해주세요.
    이 사용자만의 특별한 요구사항이나 선호도를 반영해주세요."""
                base_prompt += context_section
            
            final_instructions = """

    다음 형식으로 응답해주세요:
    1. 전반적인 분석 및 권장사항
    2. 주간 운동 계획
    3. 각 운동별 세부 지침 (세트, 반복 횟수, 휴식 시간)
    4. 주의사항

    **중요: 매번 다양하고 창의적인 운동 루틴을 생성해주세요.**"""
            
            return base_prompt + final_instructions
            
        except Exception as e:
            logger.error(f"시스템 프롬프트 생성 실패: {str(e)}")
            return "전문 피트니스 코치로서 사용자에게 맞춤형 운동 루틴을 제공해주세요."

    
    async def generate_enhanced_routine_async(self, user_data: Dict[str, Any]) -> str:
        """비동기 향상된 운동 루틴 생성 - 사용자별 개인화된 추천"""
        try:
            # 사용자 데이터 검증
            inbody = user_data.get("inbody", {})
            preferences = user_data.get("preferences", {})
            user_id = user_data.get("user_id")
            user_context = user_data.get("user_context", "")
            
            logger.info(f"운동 루틴 생성 시작 - 사용자: {user_id}, 목표: {preferences.get('goal')}")
            
            # 필수 필드 확인
            required_fields = ["gender", "age", "height", "weight"]
            for field in required_fields:
                if field not in inbody:
                    raise ValueError(f"필수 인바디 정보 누락: {field}")
            
            # 일반 피트니스 지식 VectorDB 컨텍스트 검색
            general_context = ""
            if self._documents_loaded:
                search_query = f"운동 루틴 {inbody['gender']} {preferences.get('goal', '')} {preferences.get('experience_level', '')}"
                general_context = self.vector_store.get_relevant_context(search_query, max_context_length=800)
            
            # 사용자별 컨텍스트 가져오기 (개인화 강화)
            enhanced_user_context = ""
            if user_id and user_id != "None" and user_id != "null":
                try:
                    # 사용자별 최신 데이터 조회
                    enhanced_user_context = self.user_vector_store.get_user_context(
                        user_id, 
                        f"운동 루틴 추천 {preferences.get('goal', '')} 개인화",
                        n_results=3  # 더 많은 개인 데이터 활용
                    )
                    logger.info(f"사용자 {user_id}의 개인화 컨텍스트 조회 완료: {len(enhanced_user_context)} chars")
                except Exception as e:
                    logger.error(f"사용자 컨텍스트 조회 실패: {str(e)}")
            
            # 전체 컨텍스트 구성 (개인화를 더 우선시)
            combined_context = ""
            if enhanced_user_context:
                combined_context += f"개인 맞춤 데이터:\n{enhanced_user_context}\n\n"
            if general_context:
                combined_context += f"전문 지식:\n{general_context}"
            
            # context_info 변수 정의 (f-string 내 백슬래시 문제 해결)
            context_info = ""
            if combined_context:
                context_info = f"개인화 참고자료:\n{combined_context}"
            
            # Function Calling을 사용한 구조화된 운동 루틴 생성
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system", 
                    "content": f"""
                    당신은 전문 피트니스 코치입니다. 사용자별 개인화된 4일간의 운동 루틴을 MongoDB에 저장할 수 있는 형태로 생성해주세요.
                    
                    사용자 정보:
                    - 사용자 ID: {user_id}
                    - 성별: {inbody['gender']}
                    - 나이: {inbody['age']}세
                    - 신장: {inbody['height']}cm
                    - 체중: {inbody['weight']}kg
                    - BMI: {inbody.get('bmi', '계산됨')}
                    - 기초대사율: {inbody.get('basal_metabolic_rate', '계산됨')}kcal
                    - 운동 목표: {preferences.get('goal', '건강 유지')}
                    - 경험 수준: {preferences.get('experience_level', '보통')}
                    - 부상 여부: {preferences.get('injury_status', '없음')}
                    - 운동 시간: {preferences.get('available_time', '주 3회')}
                    
                    {context_info}
                    
                    **중요 지침:**
                    1. 이 사용자(ID: {user_id})만을 위한 완전히 개인화된 루틴을 생성해주세요
                    2. 매번 다양하고 창의적인 운동들을 조합하여 새로운 루틴을 만들어주세요
                    3. 사용자의 개인 데이터 히스토리를 최대한 활용해주세요
                    4. 동일한 사용자라도 항상 다른 운동 조합으로 구성해주세요
                    
                    반드시 다음 JSON 형태로 4일간의 운동 루틴을 생성해주세요:
                    [
                        {{
                            "user_id": {int(user_id) if user_id and str(user_id).isdigit() else 1},
                            "day": 1,
                            "title": "1일차 - [개인맞춤] 하체 & 힙 집중",
                            "exercises": [
                                {{
                                    "id": 1,
                                    "name": "워밍업: 러닝머신 빠르게 걷기",
                                    "sets": [
                                        {{
                                            "id": 1,
                                            "time": "5분",
                                            "completed": false
                                        }}
                                    ]
                                }},
                                {{
                                    "id": 2,
                                    "name": "개인맞춤 운동",
                                    "sets": [
                                        {{
                                            "id": 1,
                                            "reps": 12,
                                            "weight": 20,
                                            "completed": false
                                        }}
                                    ]
                                }}
                            ]
                        }}
                    ]
                    
                    주의사항:
                    1. user_id는 반드시 정수(integer)로 설정
                    2. 각 운동의 id는 고유한 번호로 설정
                    3. sets 배열 안의 각 세트도 고유한 id 필요
                    4. 사용자의 경험 수준과 목표에 맞는 적절한 중량과 횟수 설정
                    5. **매번 완전히 다른 운동들로 구성하여 개인화 극대화**
                    6. 사용자 개인 데이터를 적극 반영한 맞춤형 운동 선택
                    """
                }, {
                    "role": "user", 
                    "content": f"사용자 ID {user_id}를 위한 완전히 개인화된 4일간의 운동 루틴을 생성해주세요. 이 사용자만의 특별한 루틴으로 만들어주세요."
                }],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "generate_personalized_workout_routine",
                        "description": "사용자별 개인화된 MongoDB 저장용 4일간의 운동 루틴을 생성합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "routines": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {"type": "integer", "description": "사용자 ID (정수)"},
                                            "day": {"type": "integer", "description": "운동 일차 (1-4)"},
                                            "title": {"type": "string", "description": "개인화된 운동 제목"},
                                            "exercises": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer", "description": "운동 고유 ID"},
                                                        "name": {"type": "string", "description": "개인맞춤 운동 이름"},
                                                        "sets": {
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "id": {"type": "integer", "description": "세트 고유 ID"},
                                                                    "reps": {"type": "integer", "description": "반복 횟수"},
                                                                    "weight": {"type": "integer", "description": "중량 kg"},
                                                                    "time": {"type": "string", "description": "시간"},
                                                                    "completed": {"type": "boolean", "description": "완료 여부"}
                                                                },
                                                                "required": ["id", "completed"]
                                                            }
                                                        }
                                                    },
                                                    "required": ["id", "name", "sets"]
                                                }
                                            }
                                        },
                                        "required": ["user_id", "day", "title", "exercises"]
                                    }
                                }
                            },
                            "required": ["routines"]
                        }
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "generate_personalized_workout_routine"}},
                temperature=1.0  # 최대 다양성을 위해 temperature 증가
            )
            
            # Function calling 응답 처리
            if response.choices[0].message.tool_calls:
                function_call = response.choices[0].message.tool_calls[0].function
                routine_data = json.loads(function_call.arguments)
                
                # 데이터 검증
                if 'routines' not in routine_data or not routine_data['routines']:
                    raise ValueError("운동 루틴 데이터가 생성되지 않았습니다.")
                
                # user_id를 강제로 정수로 변환
                for routine in routine_data['routines']:
                    if user_id:
                        try:
                            routine['user_id'] = int(user_id)
                        except (ValueError, TypeError):
                            routine['user_id'] = 1
                    else:
                        routine['user_id'] = 1
                
                # MongoDB에 저장
                saved_routines = []
                for routine in routine_data['routines']:
                    try:
                        # user_id가 정수인지 재확인
                        if not isinstance(routine['user_id'], int):
                            try:
                                routine['user_id'] = int(routine['user_id'])
                            except (ValueError, TypeError):
                                routine['user_id'] = 1
                        
                        # MongoDB에 저장
                        saved_id = self.db.save_routine(routine)
                        if saved_id:
                            routine['_id'] = str(saved_id)
                            routine['created_at'] = datetime.now(timezone.utc).isoformat()
                            saved_routines.append(routine)
                            logger.info(f"개인화 운동 루틴 저장 완료: Day {routine['day']} (사용자: {routine['user_id']})")
                    except Exception as e:
                        logger.error(f"운동 루틴 저장 실패: {str(e)}")
                
                if not saved_routines:
                    raise ValueError("운동 루틴을 데이터베이스에 저장할 수 없습니다.")
                
                # 사용자 벡터DB에 운동 진행 상황 초기화 (개인화)
                if user_id and user_id != "None" and user_id != "null":
                    try:
                        progress_data = {
                            'user_id': user_id,
                            'total_days': len(saved_routines),
                            'completion_rate': 0,
                            'created_routines': [r['day'] for r in saved_routines],
                            'personalization_level': 'high',
                            'routine_generation_date': datetime.now(timezone.utc).isoformat()
                        }
                        self.user_vector_store.add_user_progress(user_id, progress_data)
                        logger.info(f"사용자 {user_id}의 개인화된 진행 상황 초기화 완료")
                    except Exception as e:
                        logger.error(f"진행 상황 초기화 실패: {str(e)}")
                
                # 성공 응답 생성
                return {
                    'success': True,
                    'routines': saved_routines,
                    'analysis': self._create_personalized_analysis_text(inbody, preferences, user_id),
                    'total_days': len(saved_routines),
                    'personalization_applied': bool(enhanced_user_context)
                }
                
            else:
                raise ValueError("Function calling 응답을 받지 못했습니다.")
                
        except Exception as e:
            logger.error(f"운동 루틴 생성 중 오류: {str(e)}")
            # 오류 발생 시 기본 텍스트 형태로 fallback
            return await self._generate_fallback_routine_text(user_data)
        
    async def _generate_fallback_routine_text(self, user_data: Dict[str, Any]) -> str:
        """오류 발생 시 기본 텍스트 형태 운동 루틴 생성"""
        try:
            inbody = user_data.get("inbody", {})
            preferences = user_data.get("preferences", {})
            user_id = user_data.get("user_id", "Unknown")
            
            # 안전한 변수 할당
            gender = inbody.get('gender', '미지정')
            age = inbody.get('age', '미지정')
            goal = preferences.get('goal', '건강 유지')
            experience = preferences.get('experience_level', '보통')
            
            user_info_text = f"""사용자 정보:
    - 사용자 ID: {user_id}
    - 성별: {gender}
    - 나이: {age}세
    - 운동 목표: {goal}
    - 경험 수준: {experience}

    이 사용자만을 위한 개인화된 4일간의 운동 루틴을 체계적으로 추천해주세요."""
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"전문 피트니스 코치로서 사용자 ID {user_id}에게 맞춤 운동 루틴을 제공해주세요."
                }, {
                    "role": "user",
                    "content": user_info_text
                }],
                temperature=0.8,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Fallback 루틴 생성 실패: {str(e)}")
            return "죄송합니다. 운동 루틴 생성 중 오류가 발생했습니다. 다시 시도해주세요."

    def _create_personalized_analysis_text(self, inbody: Dict, preferences: Dict, user_id: str) -> str:
        """사용자별 개인화된 분석 텍스트 생성"""
        try:
            # BMI 값 안전하게 처리
            bmi_raw = inbody.get('bmi', 0)
            try:
                if isinstance(bmi_raw, str):
                    bmi_numbers = re.findall(r'\d+\.?\d*', bmi_raw)
                    bmi = float(bmi_numbers[0]) if bmi_numbers else 0
                else:
                    bmi = float(bmi_raw) if bmi_raw else 0
            except (ValueError, TypeError, IndexError):
                bmi = 0
            
            # BMI 상태 판정
            bmi_status = "정상"
            if bmi > 0:
                if bmi < 18.5:
                    bmi_status = "저체중"
                elif bmi < 23:
                    bmi_status = "정상"
                elif bmi < 25:
                    bmi_status = "과체중"
                else:
                    bmi_status = "비만"
            
            # 기초대사율 안전하게 처리
            bmr_raw = inbody.get('basal_metabolic_rate', '계산됨')
            try:
                if isinstance(bmr_raw, str) and bmr_raw != '계산됨':
                    bmr_numbers = re.findall(r'\d+', bmr_raw)
                    bmr_display = f"{bmr_numbers[0]}kcal" if bmr_numbers else '계산됨'
                elif isinstance(bmr_raw, (int, float)):
                    bmr_display = f"{int(bmr_raw)}kcal"
                else:
                    bmr_display = '계산됨'
            except (ValueError, TypeError, IndexError):
                bmr_display = '계산됨'
            
            # BMI 표시 형식 결정
            bmi_display = f"{bmi:.1f}" if bmi > 0 else "계산됨"
            
            # 개별 변수로 분리하여 f-string 문제 방지
            goal = preferences.get('goal', '건강 유지')
            experience = preferences.get('experience_level', '보통')
            
            analysis = f"""## 🎯 개인화된 분석 결과 (사용자 ID: {user_id})

    **신체 정보 분석:**
    - BMI {bmi_display} ({bmi_status})
    - 기초대사율: {bmr_display}
    - 목표: {goal}
    - 경험 수준: {experience}

    **개인 맞춤 운동 계획:**
    귀하만을 위한 완전히 개인화된 4일간의 운동 루틴을 설계했습니다.
    과거 운동 데이터와 개인 선호도를 모두 반영하여 최적화된 루틴입니다.

    **개인화 특징:**
    - 사용자별 운동 히스토리 반영
    - 개인 맞춤 운동 강도 및 볼륨 설정
    - 지속적인 개선을 위한 데이터 기반 추천
    - 사용자 피드백을 통한 동적 조정"""
            
            return analysis.strip()
            
        except Exception as e:
            logger.error(f"개인화된 분석 텍스트 생성 실패: {str(e)}")
            goal = preferences.get('goal', '건강 유지')
            experience = preferences.get('experience_level', '보통')
            
            fallback_analysis = f"""## 🎯 개인화된 분석 결과 (사용자 ID: {user_id})

    **맞춤 운동 계획:**
    귀하의 목표({goal})에 맞는 개인화된 4일간의 운동 루틴이 생성되었습니다.
    {experience} 수준에 최적화된 운동 강도로 구성되었습니다."""
            
            return fallback_analysis.strip()

    def generate_enhanced_routine_sync(self, user_data: Dict[str, Any]) -> str:
        """동기식 향상된 운동 루틴 생성"""
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system", 
                    "content": self._create_routine_system_prompt(user_data)
                }],
                temperature=0.8,  # 다양성 증가
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"운동 루틴 생성 중 오류: {str(e)}")
            raise Exception(f"운동 루틴 생성 실패: {str(e)}")
    
    async def add_documents_to_vector_store_async(self, pdf_paths: list) -> bool:
        """비동기 문서 추가"""
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            self._executor,
            self.add_documents_to_vector_store_sync,
            pdf_paths
        )
    
    def add_documents_to_vector_store_sync(self, pdf_paths: list) -> bool:
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
            logger.error(f"문서 추가 실패: {e}")
            return False
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """대화 요약 정보 반환"""
        vector_stats = {}
        user_vector_stats = {}
        
        try:
            if self._documents_loaded:
                vector_stats = self.vector_store.get_collection_stats()
            user_vector_stats = self.user_vector_store.get_collection_stats()
        except Exception as e:
            logger.error(f"벡터 스토어 통계 조회 실패: {e}")
            
        return {
            "message_count": len(self.conversation_history),
            "has_recommendation": len(self.conversation_history) > 2,
            "last_recommendation": self.conversation_history[1]["content"] if len(self.conversation_history) > 1 else None,
            "general_vector_store_stats": vector_stats,
            "user_vector_store_stats": user_vector_stats,
            "loading_status": self.get_loading_status()
        }
    
    def __del__(self):
        """소멸자 - 스레드 풀 정리"""
        try:
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=False)
        except Exception:
            pass