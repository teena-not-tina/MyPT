import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Container } from '@mui/material';
import axios from 'axios';

function MainPage() {
  const navigate = useNavigate();
  const [mascotImage, setMascotImage] = useState(null);

  useEffect(() => {
    // 캐릭터 이미지 가져오기
    fetchMascotImage();
  }, []);

  const fetchMascotImage = async () => {
    try {
      const response = await axios.get('http://localhost:8003/api/character/current');
      setMascotImage(response.data.image_url);
    } catch (error) {
      console.error('마스코트 이미지 로드 실패:', error);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <h1>B-FIT 메인 페이지</h1>

        {/* 마스코트 캐릭터 */}
        <Box sx={{ my: 4 }}>
          {mascotImage ? (
            <img src={mascotImage} alt="마스코트" style={{ width: '300px', height: '300px' }} />
          ) : (
            <div style={{ width: '300px', height: '300px', backgroundColor: '#f0f0f0', margin: '0 auto' }}>
              마스코트 로딩 중...
            </div>
          )}
        </Box>

        {/* 메인 버튼들 */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 4 }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/exercise/start')}
          >
            운동 시작하기
          </Button>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/diet/choice')}
          >
            식단 기록하기
          </Button>
        </Box>
      </Box>
    </Container>
  );
}

export default MainPage;
