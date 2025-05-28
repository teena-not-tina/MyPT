import streamlit as st
import os
import tempfile
from pathlib import Path
import json
from datetime import datetime

# 모듈 import
from modules.chatbot import FitnessChatbot, ChatbotSessionManager
from modules.pdf_processor import PDFProcessor
from modules.utils import create_upload_directory, save_uploaded_file, validate_uploaded_file, cleanup_temp_files, format_recommendation

# Streamlit 페이지 설정
st.set_page_config(
    page_title="AI 피트니스 코치",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
def initialize_session_state():
    """세션 상태 초기화"""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = ChatbotSessionManager()
    
    if 'current_chatbot' not in st.session_state:
        st.session_state.current_chatbot = st.session_state.session_manager.create_session()
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    
    if 'pdf_processor' not in st.session_state:
        st.session_state.pdf_processor = PDFProcessor()
    
    if 'current_recommendation' not in st.session_state:
        st.session_state.current_recommendation = None
    
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = None
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

def main():
    """메인 애플리케이션"""
    initialize_session_state()
    
    # 사이드바 - 파일 업로드 및 세션 관리
    with st.sidebar:
        st.header("📤 InBody PDF 업로드")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "InBody PDF 파일을 업로드하세요",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="InBody 검사 결과 PDF 및 이미지 파일만 업로드 가능합니다"
        )
        
        # 파일이 업로드되면 자동으로 분석 시작
        if uploaded_file is not None:
            if not validate_uploaded_file(uploaded_file):
                st.error("❌ 유효하지 않은 파일입니다.")
            else:
                st.success(f"✅ 파일 업로드 완료: {uploaded_file.name}")
                st.info(f"📁 파일 크기: {uploaded_file.size / 1024:.1f} KB")
                
                # 분석 버튼
                if st.button("🔍 InBody 분석 시작", type="primary", key="analyze_btn"):
                    analyze_inbody_pdf(uploaded_file)
        
        st.markdown("---")
        
        # 세션 관리
        st.header("🎯 세션 관리")
        
        # 현재 세션 정보
        if st.session_state.current_chatbot:
            session_info = st.session_state.current_chatbot.get_session_info()
            st.success(f"**활성 세션:** {session_info['session_id'][:8]}...")
            st.info(f"**메시지 수:** {session_info['message_count']}")
            st.info(f"**분석 완료:** {'✅' if session_info['recommendation_generated'] else '❌'}")
        
        # 세션 관리 버튼들
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🆕 새 세션", key="new_session_btn"):
                st.session_state.current_chatbot = st.session_state.session_manager.create_session()
                st.session_state.analysis_complete = False
                st.session_state.current_recommendation = None
                st.session_state.extracted_text = None
                st.session_state.chat_messages = []
                st.success("새 세션이 생성되었습니다!")
                st.rerun()
        
        with col2:
            if st.button("🧹 세션 초기화", key="reset_session_btn") and st.session_state.current_chatbot:
                st.session_state.current_chatbot.clear_chat_history()
                st.session_state.analysis_complete = False
                st.session_state.current_recommendation = None
                st.session_state.chat_messages = []
                st.success("세션이 초기화되었습니다!")
                st.rerun()
    
    # 메인 콘텐츠
    st.title("🏋️‍♂️ AI 피트니스 코치")
    st.markdown("---")
    
    # 분석 결과가 있는 경우
    if st.session_state.analysis_complete and st.session_state.current_recommendation:
        display_main_content()
    else:
        # 초기 화면
        display_welcome_screen()

def display_welcome_screen():
    """초기 환영 화면"""
    st.markdown("""
    ### 📊 InBody 분석 기반 맞춤형 운동 루틴 추천
    
    **사용 방법:**
    1. 👈 왼쪽 사이드바에서 InBody PDF를 업로드하세요
    2. 🔍 '분석 시작' 버튼을 클릭하세요
    3. 🤖 AI가 체성분을 분석하여 맞춤형 운동 루틴을 제공합니다
    4. 💬 하단에서 추가 요구사항을 입력하여 루틴을 조정할 수 있습니다
    """)
    
    # 안내 이미지나 추가 정보
    st.info("💡 **팁:** InBody 검사 결과 PDF 파일을 준비해주세요. AI가 당신의 체성분 데이터를 분석하여 최적의 운동 루틴을 제안해드립니다.")
    
    # 샘플 기능 소개
    st.markdown("### 🎯 주요 기능")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 정확한 분석**
        - InBody 데이터 해석
        - 체성분 기반 분석
        - 개인 맞춤형 평가
        """)
    
    with col2:
        st.markdown("""
        **🏋️ 맞춤 루틴**
        - 목적별 운동 계획
        - 강도 조절 가능
        - 상세한 운동 가이드
        """)
    
    with col3:
        st.markdown("""
        **💬 실시간 조정**
        - 요구사항 반영
        - 즉시 루틴 수정
        - 전문가 수준 상담
        """)

def display_main_content():
    """메인 콘텐츠 표시 - 분석 결과 및 챗봇 대화"""
    
    # 분석 결과 표시
    st.markdown("### 🎯 맞춤형 운동 루틴 추천")
    st.markdown("---")
    
    # 추천 결과를 컨테이너에 표시
    recommendation_container = st.container()
    
    with recommendation_container:
        if st.session_state.current_recommendation:
            # 포맷팅된 추천 결과 표시
            formatted_recommendation = format_recommendation(st.session_state.current_recommendation)
            st.markdown(formatted_recommendation)
            
            # 다운로드 버튼
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.download_button(
                    label="📥 추천서 다운로드",
                    data=st.session_state.current_recommendation,
                    file_name=f"fitness_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    st.markdown("---")
    
    # 챗봇 섹션
    st.markdown("### 💬 AI 피트니스 코치와 대화하기")
    
    # 빠른 질문 버튼들
    st.markdown("**💡 빠른 질문 선택:**")
    
    quick_questions = [
        "운동 시간을 30분으로 줄여주세요",
        "집에서 할 수 있는 운동으로 바꿔주세요", 
        "더 강한 강도의 운동을 원해요",
        "운동 빈도를 주 3회로 조정해주세요",
        "식단 조언도 추가해주세요"
    ]
    
    cols = st.columns(3)
    for i, question in enumerate(quick_questions):
        with cols[i % 3]:
            if st.button(question, key=f"quick_{i}"):
                process_chat_message(question)
                st.rerun()
    
    # 채팅 기록 표시
    display_chat_messages()
    
    # 사용자 입력 폼 (채팅 형태)
    st.markdown("**✏️ 메시지 입력:**")
    
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "AI 코치에게 질문하거나 요청사항을 입력하세요:",
            placeholder="예: 무릎이 아파서 스쿼트 대신 다른 운동을 추천해주세요.",
            height=80,
            key="chat_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("💬 전송", type="primary")
        
        if submitted and user_input.strip():
            process_chat_message(user_input)
            st.rerun()

def analyze_inbody_pdf(uploaded_file):
    """InBody PDF 분석 실행"""
    
    # 업로드 디렉토리 생성
    upload_dir = create_upload_directory()
    
    try:
        with st.spinner("📄 PDF 파일 처리 중..."):
            # 파일 저장
            file_path = save_uploaded_file(uploaded_file, upload_dir)
            st.success("✅ 파일 저장 완료")
        
        with st.spinner("🔍 PDF에서 텍스트 추출 중..."):
            # PDF 텍스트 추출
            extracted_text = st.session_state.pdf_processor.process_pdf(file_path)
            
            if not extracted_text.strip():
                st.error("❌ PDF에서 텍스트를 추출할 수 없습니다. 이미지 품질을 확인해주세요.")
                return
            
            st.success("✅ 텍스트 추출 완료")
            st.session_state.extracted_text = extracted_text
            
            # 추출된 텍스트 미리보기 (사이드바에)
            with st.sidebar.expander("📝 추출된 텍스트 미리보기"):
                st.text_area("추출된 내용", extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text, height=200, key="extracted_preview")
        
        with st.spinner("🤖 AI 분석 및 운동 루틴 생성 중..."):
            # InBody 분석 및 추천 생성
            recommendation = st.session_state.current_chatbot.process_inbody_analysis(extracted_text)
            
            if recommendation:
                st.success("✅ 분석 완료!")
                st.session_state.analysis_complete = True
                st.session_state.current_recommendation = recommendation
                
                # 초기 메시지 추가
                st.session_state.chat_messages = []
                add_chat_message("assistant", "안녕하세요! 당신의 InBody 분석 결과를 바탕으로 맞춤형 운동 루틴을 만들어드렸습니다. 궁금한 점이나 조정하고 싶은 부분이 있으시면 언제든 말씀해주세요! 😊")
                
                st.rerun()
            else:
                st.error("❌ 분석에 실패했습니다. 다시 시도해주세요.")
    
    except Exception as e:
        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    finally:
        # 임시 파일 정리
        try:
            cleanup_temp_files(file_path)
        except:
            pass

def add_chat_message(role: str, content: str):
    """채팅 메시지 추가"""
    st.session_state.chat_messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M")
    })

def process_chat_message(user_input: str):
    """사용자 메시지 처리 (챗봇 형태)"""
    
    # 사용자 메시지 추가
    add_chat_message("user", user_input)
    
    try:
        with st.spinner("🤖 AI 코치가 답변을 준비하고 있습니다..."):
            # 챗봇에게 메시지 전달
            response = st.session_state.current_chatbot.handle_user_input(user_input)
            
            if response and "오류가 발생했습니다" not in response:
                # AI 응답 메시지 추가
                add_chat_message("assistant", response)
            else:
                # 오류 응답
                error_msg = "죄송합니다. 일시적으로 응답을 생성할 수 없습니다. 다시 한 번 질문해주시거나, 다른 방식으로 문의해주세요. 🙏"
                add_chat_message("assistant", error_msg)
            
    except Exception as e:
        st.error(f"❌ 메시지 처리 중 오류가 발생했습니다: {str(e)}")
        
        # 대안적 접근 방법 시도
        try:
            st.info("🔄 대안적 방법으로 재시도 중...")
            
            # analyzer에 직접 접근하여 처리
            if hasattr(st.session_state.current_chatbot, 'analyzer'):
                # 컨텍스트를 포함한 프롬프트 생성
                context_prompt = f"""
                당신은 전문 피트니스 코치입니다. 사용자의 InBody 분석 결과를 바탕으로 맞춤형 운동 루틴을 제공했습니다.
                
                현재 제공한 운동 루틴:
                {st.session_state.current_recommendation}
                
                사용자 질문/요청:
                {user_input}
                
                사용자의 질문에 친근하고 전문적으로 답변해주세요. 운동 루틴 수정이 필요한 경우 구체적인 대안을 제시해주세요.
                """
                
                # analyzer의 chat_with_bot 메서드 호출
                response = st.session_state.current_chatbot.analyzer.chat_with_bot(context_prompt)
                
                if response:
                    add_chat_message("assistant", response)
                    st.success("✅ 응답이 생성되었습니다!")
                else:
                    add_chat_message("assistant", "죄송합니다. 기술적인 문제로 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.")
            else:
                add_chat_message("assistant", "AI 시스템에 일시적인 문제가 발생했습니다. 새 세션을 생성하거나 페이지를 새로고침해주세요.")
                
        except Exception as e2:
            st.error(f"❌ 대안 방법도 실패했습니다: {str(e2)}")
            add_chat_message("assistant", "기술적인 문제로 응답할 수 없습니다. 새로고침 후 다시 시도해주세요. 🔄")

def display_chat_messages():
    """채팅 메시지 표시"""
    if st.session_state.chat_messages:
        st.markdown("**💭 대화 내역:**")
        
        # 채팅 컨테이너
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_messages:
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(f"**{message['timestamp']}** - {message['content']}")
                else:  # assistant
                    with st.chat_message("assistant"):
                        st.write(f"**{message['timestamp']}** - {message['content']}")
        
        # 채팅 기록이 많을 경우 스크롤을 위한 여백
        if len(st.session_state.chat_messages) > 4:
            st.markdown("<br>" * 2, unsafe_allow_html=True)
    else:
        st.info("💡 AI 코치와 대화를 시작해보세요! 운동 루틴에 대한 질문이나 조정 요청을 자유롭게 해주세요.")

# 앱 실행을 위한 설정
if __name__ == "__main__":
    # 필요한 디렉토리 생성
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("chroma_db").mkdir(parents=True, exist_ok=True)
    
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        st.stop()
    
    try:
        main()
    except Exception as e:
        st.error(f"❌ 애플리케이션 실행 중 오류가 발생했습니다: {str(e)}")
        st.info("🔄 페이지를 새로고침하거나 관리자에게 문의하세요.")