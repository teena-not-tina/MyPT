import React from 'react';
import { useImages } from '../contexts/ImageContext';
import '../styles/images.css';

function Profile() {
  const { images, updateImage } = useImages();

  const handleImageUpdate = async (newImageData) => {
    // base64 이미지 데이터를 받아서 모든 이미지 업데이트
    updateImage('food', `data:image/png;base64,${newImageData}`);
    
    // 다른 컴포넌트의 이미지도 동시에 업데이트
    document.querySelectorAll('.food-image').forEach(img => {
      img.src = `data:image/png;base64,${newImageData}`;
    });
  };

  return (
    <div>
      <img 
        src={images.food} 
        alt="Food" 
        className="food-image"
      />
    </div>
  );
}

export default Profile;