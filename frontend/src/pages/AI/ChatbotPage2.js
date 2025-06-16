import React, { useState, useRef } from 'react';

const API_URL = 'http://192.168.0.18:8004';

function ChatbotPage() {
  const [messages, setMessages] = useState([
    { from: 'bot', text: '안녕하세요! 👋 음식 사진을 올리면 재료를 분석하고, 만들 수 있는 요리를 추천해드려요.' }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [suggestions, setSuggestions] = useState([
    '요리 추천해줘',
    '간단한 요리 추천해줘',
    '이걸로 뭘 만들 수 있어?'
  ]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const fileInputRef = useRef();

  // 사용자 ID 가져오기 함수 - 정수로 생성
const getUserNum = () => {
  let user_num = sessionStorage.getItem('user_id');
  
  // if (!userId) {
  //   // 정수 형태의 user_id 생성 (1000-999999 범위)
  //   userId = (Math.floor(Math.random() * 999000) + 1000).toString();
  //   sessionStorage.setItem('user_id', userId);
  //   console.log('새로운 user_id 생성:', userId);
  // }
  
  return user_num
};

  // 이미지 base64 변환
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  // 메시지 추가
  const addMessage = (msg) => {
    setMessages((prev) => [...prev, msg]);
  };

  // 텍스트 메시지 전송
  const sendText = async () => {
    if (!input.trim() || isProcessing) return;
    const userMsg = { from: 'user', text: input };
    addMessage(userMsg);
    setInput('');
    setIsProcessing(true);
    setShowSuggestions(false); // 새 메시지 전송 시 제안 숨김

    try {
      const res = await fetch('http://192.168.0.18:8004', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: getUserId(),
          text: userMsg.text,
          platform: 'web'
        })
      });
      const data = await res.json();
      handleBotResponse(data);
    } catch (e) {
      addMessage({ from: 'bot', text: '서버 오류가 발생했습니다. 다시 시도해주세요.' });
    }
    setIsProcessing(false);
  };

  // 이미지 메시지 전송
  const sendImage = async (file) => {
    if (!file || isProcessing) return;
    setIsProcessing(true);
    setShowSuggestions(false); // 새 이미지 전송 시 제안 숨김
    addMessage({ from: 'user', text: <img src={URL.createObjectURL(file)} alt="업로드 이미지" style={{maxWidth:200}} /> });

    try {
      const base64 = await fileToBase64(file);
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: getUserId(),
          image_base64: base64,
          platform: 'web'
        })
      });
      const data = await res.json();
      handleBotResponse(data, true);
    } catch (e) {
      addMessage({ from: 'bot', text: '이미지 분석에 실패했습니다. 다시 시도해주세요.' });
    }
    setIsProcessing(false);
  };

  // 챗봇 응답 처리
  const handleBotResponse = (data, isImageResponse = false) => {
    if (data.status === 'success') {
      (data.detections || []).forEach(det => {
        addMessage({ from: 'bot', text: det.label });
      });
      if (data.suggestions) {
        setSuggestions(data.suggestions);
        setShowSuggestions(true); // 봇 응답 후 제안 버튼 표시
      }
      if (isImageResponse && !data.suggestions) {
        setShowSuggestions(true); // 이미지 응답인 경우 기본 제안 표시
      }
    } else {
      addMessage({ from: 'bot', text: data.message || '오류가 발생했습니다.' });
    }
  };

  // user_id 관리 (메모리)
  function getUserId() {
    if (!window.chatbotUserId) {
      window.chatbotUserId = Date.now();
    }
    return window.chatbotUserId;
  }

  // 엔터키 입력 처리
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendText();
    }
  };

  // 제안 버튼 클릭
  const handleSuggestion = (text) => {
    setInput(text);
    setShowSuggestions(false); // 제안 클릭 시 제안 숨김
    setTimeout(sendText, 100);
  };

  // 이미지 선택
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) sendImage(file);
    e.target.value = '';
  };

  return (
    <div style={{
      maxWidth: 500, margin: '0 auto', background: '#fff', borderRadius: 12,
      boxShadow: '0 2px 8px #eee', minHeight: 600, display: 'flex', flexDirection: 'column'
    }}>
      <div style={{padding: 16, borderBottom: '1px solid #eee', background: '#f8fafc'}}>
        <b>🍳 요리 추천 챗봇</b>
      </div>
      <div style={{flex: 1, overflowY: 'auto', padding: 16}}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            textAlign: msg.from === 'user' ? 'right' : 'left',
            margin: '8px 0'
          }}>
            <span style={{
              display: 'inline-block',
              background: msg.from === 'user' ? '#e0f7fa' : '#f1f1f1',
              borderRadius: 8,
              padding: 10,
              maxWidth: '80%',
              wordBreak: 'break-all'
            }}>
              {typeof msg.text === 'string'
                ? <span dangerouslySetInnerHTML={{__html: msg.text.replace(/\n/g, '<br/>')}} />
                : msg.text}
            </span>
          </div>
        ))}
        
        {/* 제안 버튼들을 채팅 메시지처럼 표시 */}
        {showSuggestions && !isProcessing && (
          <div style={{
            textAlign: 'left',
            margin: '8px 0'
          }}>
            <div style={{
              display: 'inline-block',
              background: '#f1f1f1',
              borderRadius: 8,
              padding: 10,
              maxWidth: '80%'
            }}>
              <div style={{marginBottom: 8, fontSize: 14, color: '#666'}}>
                💡 이런 질문은 어떠세요?
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestion(s)}
                    style={{
                      background: '#4caf50', 
                      color: '#fff',
                      border: 'none', 
                      borderRadius: 6, 
                      padding: '8px 12px',
                      cursor: 'pointer', 
                      fontSize: 13,
                      textAlign: 'left',
                      transition: 'background-color 0.2s',
                      ':hover': {
                        background: '#45a049'
                      }
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#45a049'}
                    onMouseLeave={(e) => e.target.style.background = '#4caf50'}
                  >{s}</button>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {isProcessing && (
          <div style={{textAlign: 'left', color: '#aaa', margin: '8px 0'}}>챗봇이 답변 중입니다...</div>
        )}
      </div>

      <div style={{padding: 12, borderTop: '1px solid #eee', background: '#fafbfc'}}>
        <div style={{display: 'flex', gap: 8}}>
          <button
            onClick={() => fileInputRef.current.click()}
            style={{padding: '0 12px', fontSize: 20, background: '#fff', border: '1px solid #ddd', borderRadius: 6}}
            disabled={isProcessing}
          >📷</button>
          <input
            type="file"
            accept="image/*"
            style={{display: 'none'}}
            ref={fileInputRef}
            onChange={handleFileChange}
          />
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="메시지를 입력하세요..."
            style={{flex: 1, padding: 10, borderRadius: 6, border: '1px solid #ddd'}}
            disabled={isProcessing}
          />
          <button
            onClick={sendText}
            style={{padding: '0 16px', background: '#4caf50', color: '#fff', border: 'none', borderRadius: 6}}
            disabled={isProcessing || !input.trim()}
          >전송</button>
        </div>
      </div>
    </div>
  );
}

export default ChatbotPage;