import React, { useState, useEffect, useRef } from 'react';
import './index.css';

// 기본 프로필 이미지 (없다면 투명 픽셀 Base64 등)
const DEFAULT_PROFILE_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="; // 1x1 투명 픽셀 이미지

function App() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: '안녕하세요! 오늘 무엇을 드셨나요?' }
  ]);
  // API 키는 이제 프론트엔드에서 직접 설정하지 않습니다.
  // 백엔드에서 환경 변수를 통해 가져올 것입니다.
  const [userInput, setUserInput] = useState(''); // 사용자 입력
  const [isLoading, setIsLoading] = useState(false); // 로딩 상태
  const [profileImage, setProfileImage] = useState(DEFAULT_PROFILE_IMAGE_B64); // 프로필 이미지 (Base64)

  const messagesEndRef = useRef(null); // 메시지 스크롤을 위한 Ref

  // 메시지가 업데이트될 때마다 스크롤을 맨 아래로 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // handleSetApiKey 함수는 더 이상 필요 없으므로 제거합니다.

  const sendMessage = async () => {
    // API 키 설정 여부 검증 로직 제거 (백엔드에서 처리)
    if (!userInput.trim()) {
      alert('음식을 입력해주세요.');
      return;
    }

    const userMessage = userInput.trim();
    const loadingMessageId = Date.now(); // 로딩 메시지 식별을 위한 고유 ID

    // 1. 사용자 메시지 추가
    setMessages((prev) => [...prev, { sender: 'user', text: userMessage }]);
    setUserInput(''); // 입력창 비우기

    // 2. 봇의 "생성 중" 메시지 즉시 추가
    setMessages((prev) => [
      ...prev,
      { sender: 'bot', text: `"${userMessage}"에 대해 이야기해줘서 고마워! 귀여운 캐릭터 이미지를 생성 중이야... 잠시만 기다려줘!`, id: loadingMessageId, isLoadingMessage: true }
    ]);
    setIsLoading(true);

    try {
      const response = await fetch('/chat_and_generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // API 키를 더 이상 프론트엔드에서 보내지 않습니다.
        // 백엔드의 환경 변수 OPENAI_API_KEY를 사용합니다.
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();

      if (response.ok) {
        const imageUrl = data.profile_image_b64 ? `data:image/png;base64,${data.profile_image_b64}` : null;

        // 기존 로딩 메시지를 찾아서 업데이트
        setMessages((prev) => {
          return prev.map(msg => {
            if (msg.id === loadingMessageId) {
              return {
                ...msg,
                text: data.chat_response, // GPT 응답 텍스트
                image: imageUrl, // 이미지 데이터 추가
                isLoadingMessage: false // 로딩 완료
              };
            }
            return msg;
          });
        });

        // 프로필 이미지 업데이트 (기존 로직 유지)
        if (imageUrl) {
          setProfileImage(data.profile_image_b64); // Base64 자체를 저장하고 src에서 프리픽스 붙임
        }

      } else {
        // 에러 처리: 로딩 메시지 업데이트
        setMessages((prev) => {
          return prev.map(msg => {
            if (msg.id === loadingMessageId) {
              return { ...msg, text: `이미지 생성 중 오류가 발생했어: ${data.error || '알 수 없는 오류'}`, isLoadingMessage: false };
            }
            return msg;
          });
        });
      }
    } catch (error) {
      console.error('Error:', error);
      // 네트워크 오류: 로딩 메시지 업데이트
      setMessages((prev) => {
        return prev.map(msg => {
          if (msg.id === loadingMessageId) {
            return { ...msg, text: '네트워크 오류가 발생했습니다. 다시 시도해주세요.', isLoadingMessage: false };
          }
          return msg;
        });
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        GPT-4o-mini & ComfyUI 프로필 챗봇
        <div className="profile-area">
          <img
            src={`data:image/png;base64,${profileImage}`} // Base64 이미지를 직접 표시
            alt="프로필 이미지"
            className="profile-image"
          />
        </div>
      </div>
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={msg.id || index} className={`message ${msg.sender}`}>
            {msg.text}
            {/* msg.image가 존재할 때만 이미지 렌더링 */}
            {msg.image && (
              <img
                src={msg.image}
                alt="Generated"
                style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '10px' }}
              />
            )}
          </div>
        ))}
        {/* 스크롤을 위한 더미 div */}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-area">
        {/* API 키 입력 섹션을 제거하여 항상 채팅 입력이 가능하게 합니다. */}
        <div className="chat-input">
          <input
            type="text"
            placeholder="오늘 먹은 음식을 알려주세요..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />
          <button onClick={sendMessage} disabled={isLoading}>
            보내기
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;