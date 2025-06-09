// src/pages/AI/ChatbotPage.js
import React, { useState, useRef, useEffect } from 'react';
import Header from '../../components/Shared/Header'; // 헤더 임포트
import '../../styles/global.css'; // 공통 스타일 임포트
import './ChatbotPage.css'; // 챗봇 페이지 전용 스타일 (새로 생성)

function ChatbotPage() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: '안녕하세요! 무엇을 도와드릴까요?', type: 'text' },
    { id: 2, sender: 'bot', text: '운동 루틴이나 식단에 대해 궁금한 점이 있으신가요?', type: 'text' },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null); // 메시지 스크롤을 위한 ref

  // 메시지가 추가될 때마다 스크롤을 맨 아래로 이동
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;

    const newMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: inputMessage.trim(),
      type: 'text'
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInputMessage('');

    // 챗봇 응답 시뮬레이션 (실제로는 백엔드 API 호출)
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        sender: 'bot',
        text: `"${newMessage.text}"에 대한 답변을 준비 중입니다. (아직 구현되지 않은 기능입니다.)`,
        type: 'text'
      };
      setMessages((prevMessages) => [...prevMessages, botResponse]);
    }, 1000);
  };

  return (
    <div className="page-container chatbot-page-container">
      <Header title="AI 트레이너" showBackButton={true} />
      
      <div className="chatbot-messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble ${msg.sender}`}>
            {msg.type === 'text' && <p>{msg.text}</p>}
            {/* 향후 이미지, 버튼 등 다른 타입 추가 가능 */}
          </div>
        ))}
        <div ref={messagesEndRef} /> {/* 스크롤 위치 지정 */}
      </div>

      <form onSubmit={handleSendMessage} className="chatbot-input-area">
        <textarea
          className="message-input-textarea"
          rows="1"
          placeholder="메시지를 입력하세요..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { // Shift+Enter는 줄바꿈, Enter는 전송
              handleSendMessage(e);
            }
          }}
        />
        <button type="submit" className="send-button primary-button">
          <i className="fas fa-paper-plane"></i> {/* 폰트어썸 보내기 아이콘 */}
        </button>
      </form>
    </div>
  );
}

export default ChatbotPage;