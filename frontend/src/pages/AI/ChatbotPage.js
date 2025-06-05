import { sendChatMessage } from '../../services/aiService';
import React, { useState, useRef, useEffect } from 'react';
import Header from '../../components/Shared/Header';
import '../../styles/global.css';
import './ChatbotPage.css';

const CHATBOT_STORAGE_KEY = "mypt_chatbot_messages";

function ChatbotPage() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem(CHATBOT_STORAGE_KEY);
    return saved
      ? JSON.parse(saved)
      : [
        { id: 1, sender: 'bot', text: '안녕하세요! 무엇을 도와드릴까요?', type: 'text' },
        { id: 2, sender: 'bot', text: '운동 루틴이나 식단에 대해 궁금한 점이 있으신가요?', type: 'text' },
      ];
  });
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [collectingInbody, setCollectingInbody] = useState(false);
  const [collectingWorkout, setCollectingWorkout] = useState(false);
  const [inbodyStep, setInbodyStep] = useState(0);
  const [workoutStep, setWorkoutStep] = useState(0);
  const [inbodyData, setInbodyData] = useState({});
  const [workoutData, setWorkoutData] = useState({});
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isPdfAnalyzing, setIsPdfAnalyzing] = useState(false); // PDF 분석중 상태
  const messagesEndRef = useRef(null);

  // 인바디 정보 질문 목록
  const inbodyQuestions = [
    { key: 'user_age', text: '나이를 입력해 주세요.' },
    { key: 'user_gender', text: '성별을 입력해 주세요. (남/여)' },
    { key: 'user_current_weight', text: '현재 체중(kg)을 입력해 주세요.' },
    { key: 'user_muscle_mass', text: '골격근량(kg)을 입력해 주세요.' },
    { key: 'user_body_fat_percent', text: '체지방률(%)을 입력해 주세요.' }
  ];
  // 운동 정보 질문 목록
  const workoutQuestions = [
    { key: 'user_target_weight', text: '목표 체중(kg)을 입력해 주세요.' },
    { key: 'user_fitness_level', text: '운동 수준을 입력해 주세요. (입문/초급/중급/고급/전문가)' },
    { key: 'user_available_equipment', text: '이용 가능 기구를 입력해 주세요. (헬스장/홈짐/소도구/맨몸)' },
    { key: 'user_workout_frequency', text: '주당 운동 횟수를 입력해 주세요.' },
    { key: 'user_goal', text: '운동 목표를 입력해 주세요. (예: 다이어트, 근육량 증가 등)' }
  ];

  useEffect(() => {
    localStorage.setItem(CHATBOT_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    // 창이 닫힐 때 채팅 기록 삭제
    const handleUnload = () => {
      localStorage.removeItem(CHATBOT_STORAGE_KEY);
    };
    window.addEventListener('unload', handleUnload);
    return () => {
      window.removeEventListener('unload', handleUnload);
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isPdfAnalyzing]);

  // 루틴 JSON 렌더링 함수
  const renderRoutine = (routineObj) => {
    if (typeof routineObj === "string") {
      // 루틴이 텍스트 형태일 경우 그대로 출력
      return <pre>{routineObj}</pre>;
    }
    let routines = routineObj;
    if (routineObj && typeof routineObj === "object" && Array.isArray(routineObj.routines)) {
      routines = routineObj.routines;
    }
    if (!Array.isArray(routines)) return null;
    return (
      <div className="routine-list">
        {routines.map((day, idx) => (
          <div key={idx} className="routine-day-card">
            <h4>{day.title || `Day ${day.day}`}</h4>
            <ul>
              {day.exercises.map((ex, exIdx) => (
                <li key={exIdx}>
                  <strong>{ex.name}</strong>
                  <ul>
                    {ex.sets.map((set, setIdx) => (
                      <li key={setIdx}>
                        {set.reps ? `${set.reps}회` : ""}
                        {set.weight ? ` / ${set.weight}kg` : ""}
                        {set.time ? ` / ${set.time}` : ""}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  };

  // 메시지 렌더링
  const renderMessage = (msg) => {
    if (msg.type === "user-info" && msg.text) {
      return (
        <div className="user-info-summary">
          <strong>분석된 사용자 정보:</strong>
          <pre>{JSON.stringify(msg.text, null, 2)}</pre>
        </div>
      );
    }
    // routine-json 타입이거나, routines 키가 있는 객체면 목록 렌더링
    if (
      (msg.type === "routine-json" && msg.text) ||
      (msg.text && typeof msg.text === "object" && msg.text.routines)
    ) {
      return renderRoutine(msg.text);
    }
    // JSON 문자열이지만 type이 text인 경우도 파싱 시도
    if (msg.type === "text" && typeof msg.text === "string") {
      try {
        const parsed = JSON.parse(msg.text);
        if (parsed && parsed.routines) return renderRoutine(parsed);
        if (Array.isArray(parsed)) return renderRoutine(parsed);
      } catch (e) { /* 무시 */ }
    }
    return <p>{msg.text}</p>;
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '' || isLoading || isPdfAnalyzing) return;

    const userMsg = {
      id: Date.now() + Math.random(),
      sender: 'user',
      text: inputMessage.trim(),
      type: 'text'
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // 기본: 서버에 메시지 전송
    try {
      setIsLoading(true);
      const res = await sendChatMessage(userMsg.text, sessionId);
      setSessionId(res.session_id);

      // 백엔드에서 파일 업로드 안내 신호가 오면 파일 업로드 UI를 챗봇 말풍선에 표시
      if (res.response && res.response.includes('__SHOW_INBODY_UPLOAD__')) {
        setShowFileUpload(true);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + Math.random(),
            sender: 'bot',
            text: res.response.replace('__SHOW_INBODY_UPLOAD__', '').trim(),
            type: 'text',
            showFileUpload: true
          }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + Math.random(), sender: 'bot', text: res.response, type: 'text' }
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + Math.random(), sender: 'bot', text: '서버 오류가 발생했습니다.', type: 'text' }
      ]);
    }
    setInputMessage('');
    setIsLoading(false);
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    setShowFileUpload(false);
    setIsPdfAnalyzing(true);
    setMessages((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), sender: 'user', text: file ? file.name : '파일 없음', type: 'text' },
      { id: Date.now() + Math.random(), sender: 'bot', text: '파일이 업로드되었습니다. 분석을 시작합니다.', type: 'text' }
    ]);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('http://localhost:8000/api/inbody/upload_and_recommend', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      // 1. 사용자 정보 요약 출력
      if (data.result && data.result.user_info) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + Math.random(),
            sender: 'bot',
            text: data.result.user_info,
            type: 'user-info'
          }
        ]);
      }
      // 2. 루틴 목록 출력
      if (data.result && data.result.routines) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + Math.random(),
            sender: 'bot',
            text: data.result.routines, // routines만 넘김
            type: 'routine-json'
          }
        ]);
      }
      // 3. 에러 처리
      if (data.result && data.result.error) {
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + Math.random(), sender: 'bot', text: data.result.error, type: 'text' }
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + Math.random(), sender: 'bot', text: '분석 또는 추천 중 오류가 발생했습니다.', type: 'text' }
      ]);
    }
    setIsPdfAnalyzing(false);
  };

  return (
    <div className="page-container chatbot-page-container">
      <Header title="AI 트레이너" showBackButton={true} />
      <div className="chatbot-messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble ${msg.sender}`}>
            {renderMessage(msg)}
            {/* 파일 업로드 UI를 챗봇 말풍선 안에 표시 */}
            {msg.showFileUpload && (
              <input type="file" accept="application/pdf,image/*" onChange={handleFileChange} />
            )}
          </div>
        ))}
        {/* PDF 분석중이면 챗봇 말풍선에 회전 스피너 표시 */}
        {isPdfAnalyzing && (
          <div className="message-bubble bot">
            <div className="pdf-analyzing-spinner">
              <div className="spinner"></div>
              <span style={{ marginLeft: '0.5rem' }}>PDF 파일 분석 중입니다...</span>
            </div>
          </div>
        )}
        {isLoading && (
          <div className="chatbot-loading-indicator">
            <span className="dot-flashing"></span>
            <span style={{ marginLeft: '0.5rem' }}>AI가 답변을 준비중입니다...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSendMessage} className="chatbot-input-area">
        <textarea
          className="message-input-textarea"
          rows="1"
          placeholder={isLoading || isPdfAnalyzing ? "AI가 답변을 준비중입니다..." : "메시지를 입력하세요..."}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          disabled={isLoading || isPdfAnalyzing}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !isLoading && !isPdfAnalyzing) {
              e.preventDefault();
              handleSendMessage(e);
            }
          }}
        />
        <button type="submit" className="send-button primary-button" disabled={isLoading || isPdfAnalyzing}>
          <svg viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}

export default ChatbotPage;