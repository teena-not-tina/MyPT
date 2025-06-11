// frontend/src/components/Diet/hooks/useImageUpload.js
import { useState } from 'react';

export const useImageUpload = () => {
  const [images, setImages] = useState([]);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const processImageFiles = (files) => {
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
      return { success: false, message: '이미지 파일만 업로드 가능합니다.' };
    }

    const processedImages = [];
    let processedCount = 0;

    imageFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        processedImages[index] = {
          id: Date.now() + index,
          file: file,
          dataUrl: e.target.result,
          name: file.name,
          size: file.size,
          processed: false
        };
        
        processedCount++;
        if (processedCount === imageFiles.length) {
          setImages(prev => [...prev, ...processedImages.filter(img => img)]);
          setSelectedImageIndex(images.length);
        }
      };
      
      reader.readAsDataURL(file);
    });

    return { success: true, count: imageFiles.length };
  };

  const removeImage = (imageId) => {
    setImages(prev => {
      const filtered = prev.filter(img => img.id !== imageId);
      if (filtered.length === 0) {
        setSelectedImageIndex(0);
      } else if (selectedImageIndex >= filtered.length) {
        setSelectedImageIndex(filtered.length - 1);
      }
      return filtered;
    });
  };

  const clearImages = () => {
    setImages([]);
    setSelectedImageIndex(0);
  };

  return {
    images,
    selectedImageIndex,
    setSelectedImageIndex,
    processImageFiles,
    removeImage,
    clearImages
  };
};