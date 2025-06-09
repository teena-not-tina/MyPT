// src/pages/Diet/MenuRecommendationPage.js
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/Shared/Header';
import '../../styles/global.css';
import './MenuRecommendationPage.css';
import axios from 'axios';

// axios 기본 설정
axios.defaults.baseURL = 'http://localhost:5000/api';
axios.defaults.timeout = 240000;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.withCredentials = true;


function MenuRecommendationPage() {
  const navigate = useNavigate();
  const [chatStep, setChatStep] = useState('initial_question');
  const [chatMessages, setChatMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [generatedProfileImage, setGeneratedProfileImage] = useState(null);
  const messagesEndRef = useRef(null);
  const hasInitialMessage = useRef(false); // ✅ 추가된 부분

  useEffect(() => {
    if (!hasInitialMessage.current && chatMessages.length === 0) {
      hasInitialMessage.current = true; // ✅ 최초 한 번만 실행되도록 설정
      setChatStep('initial_question');
      addMessage('bot', '안녕하세요! 식사는 어떻게 할 건가요?');
    }
  }, []);


  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, generatedProfileImage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addMessage = (sender, content) => {
    setChatMessages((prev) => [
      ...prev,
      {
        sender,
        timestamp: new Date(),
        ...(typeof content === 'object' ? content : { type: 'text', text: content })
      }
    ]);
  };

  const handleChatbotOption = (option) => {
    if (option === 'cook_myself') {
      addMessage('user', '직접 해먹기');
      setTimeout(() => {
        addMessage('bot', '직접 해먹기를 선택하셨군요! 어떤 재료를 가지고 계신가요? (이 기능은 현재 구현되지 않았습니다.)');
      }, 500);
    } else if (option === 'eat_out') {
      addMessage('user', '사먹기');
      setTimeout(() => {
        addMessage('bot', '사먹기를 선택하셨군요! 오늘 무엇을 드셨나요? 음식 이름을 알려주세요.');
        setChatStep('awaiting_meal_input');
      }, 500);
    }
  };

  const handleSubmitMeal = async (e) => {
    if (e) e.preventDefault();
    if (!userInput.trim()) {
      alert('메시지를 입력해주세요.');
      return;
    }

    setIsLoading(true);
    addMessage('user', { type: 'text', text: userInput });

    try {
      const response = await axios.post(
        `/chat_and_generate`,
        {
          message: userInput,
          user_id: 'test@mail.com'
        },
        {
          headers: { 'Content-Type': 'application/json' },
          withCredentials: true,
          timeout: 300000
        }
      );

      if (response.data) {
        const { chat_response, profile_image_b64 } = response.data;

        if (profile_image_b64) {
          setGeneratedProfileImage(profile_image_b64);
          localStorage.setItem('userProfileImage', profile_image_b64);

          addMessage('bot', {
            type: 'image',
            text: `${chat_response}\n\n✨ 새로운 캐릭터가 생성되었습니다!`,
            imageUrl: `data:image/png;base64,${profile_image_b64}`
          });

          setChatStep('show_generated_image');
        } else {
          addMessage('bot', { type: 'text', text: chat_response });
        }
      }
    } catch (error) {
      console.error('API 호출 중 오류:', error);
      addMessage('bot', { type: 'text', text: '😢 서버 통신 중 오류가 발생했습니다.' });
      setChatStep('error_state');
    } finally {
      setIsLoading(false);
      setUserInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading && userInput.trim()) {
      handleSubmitMeal();
    }
  };

  const handleGoToDashboard = () => {
    navigate('/dashboard');
  };

  const renderMessage = (msg, index) => (
    <div key={index} className={`chat-bubble ${msg.sender}`}>
      {msg.type === 'image' ? (
        <div className="message-with-image">
          <p>{msg.text}</p>
          <img
            src={msg.imageUrl}
            alt="Generated Food Character"
            className="chat-image"
            onError={(e) => {
              console.error('이미지 로딩 실패');
              e.target.style.display = 'none';
            }}
          />
        </div>
      ) : (
        <p>{msg.text}</p>
      )}
    </div>
  );

  return (
    <div className="page-container">
      <Header
        title="식단 추천 챗봇"
        showBackButton={true}
        profileImage={generatedProfileImage ? `data:image/png;base64,${generatedProfileImage}` : null}
      />

      <div className="page-content-wrapper menu-recommendation-page-content">
        <div className="chatbot-messages-area">
          {chatMessages.map((msg, index) => renderMessage(msg, index))}
          <div ref={messagesEndRef} />
        </div>

        {chatStep === 'initial_question' && (
          <div className="chatbot-options-container">
            <button
              className="primary-button chatbot-option-button"
              onClick={() => handleChatbotOption('cook_myself')}
            >
              직접 해먹기
            </button>
            <button
              className="primary-button chatbot-option-button"
              onClick={() => handleChatbotOption('eat_out')}
            >
              사먹기
            </button>
          </div>
        )}

        {(chatStep === 'awaiting_meal_input' || chatStep === 'processing_request') && (
          <div className="chat-input-area">
            <input
              type="text"
              className="meal-input-field"
              placeholder="오늘 드신 음식 이름을 입력해주세요 (예: 불고기, 스파게티)"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
            />
            <button
              className="primary-button send-meal-button"
              onClick={handleSubmitMeal}
              disabled={isLoading || !userInput.trim()}
            >
              {isLoading ? '생성 중...' : '전송'}
            </button>
          </div>
        )}

        {chatStep === 'error_state' && (
          <div className="error-message">
            <p>이미지 생성에 실패했습니다. 다시 시도해주세요.</p>
            <button
              className="primary-button"
              onClick={() => setChatStep('initial_question')}
              style={{ marginTop: '10px' }}
            >
              처음으로 돌아가기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default MenuRecommendationPage;
