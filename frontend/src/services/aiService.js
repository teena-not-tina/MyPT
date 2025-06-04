const API_URL = "http://localhost:8000/api/chat"; // '/api/ai/chat' → '/api/chat'으로 수정

export async function sendChatMessage(message, sessionId) {
  console.log('sendChatMessage 호출', message, sessionId);
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    console.log('fetch 응답', response);
    const data = await response.json();
    console.log('파싱된 응답', data);
    return data;
  } catch (err) {
    console.error('sendChatMessage 에러', err);
    throw err;
  }
}