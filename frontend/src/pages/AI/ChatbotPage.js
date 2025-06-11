// src/pages/AI/ChatbotPage.js
import React, { useState, useRef, useEffect } from 'react';
import Header from '../Shared/Header'; // 헤더 임포트

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
    <div className="flex flex-col h-screen bg-gray-50">
      <Header title="AI 트레이너" showBackButton={true} />
      
      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
              msg.sender === 'user' 
                ? 'bg-blue-600 text-white ml-auto' 
                : 'bg-white text-gray-800 shadow-sm border'
            }`}>
              {msg.sender === 'bot' && (
                <div className="flex items-center mb-2">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                    <span className="text-xs font-bold text-blue-600">AI</span>
                  </div>
                  <span className="text-xs text-gray-500 font-medium">트레이너</span>
                </div>
              )}
              <p className="text-sm leading-relaxed">{msg.text}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleSendMessage} className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              className="w-full px-4 py-3 border border-gray-300 rounded-2xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              rows="1"
              placeholder="메시지를 입력하세요..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  handleSendMessage(e);
                }
              }}
            />
          </div>
          <button 
            type="submit" 
            className="bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            disabled={!inputMessage.trim()}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatbotPage;