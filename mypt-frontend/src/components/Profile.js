import React from 'react';
import { useImages } from '../contexts/ImageContext';
import '../styles/images.css';

function Profile() {
  const { images, updateImage } = useImages();

  return null; // 컴포넌트를 렌더링하지 않도록 변경
}

export default Profile;