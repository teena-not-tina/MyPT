// utils/imageUtils.js

// 이미지 파일 처리
export const processImageFiles = (files) => {
  const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
  
  if (imageFiles.length === 0) {
    return {
      success: false,
      message: '이미지 파일만 업로드 가능합니다.',
      images: []
    };
  }

  const processedImages = [];
  let processedCount = 0;

  return new Promise((resolve) => {
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
          const validImages = processedImages.filter(img => img);
          resolve({
            success: true,
            message: `✅ ${validImages.length}개 이미지가 추가되었습니다.`,
            images: validImages
          });
        }
      };
      
      reader.onerror = () => {
        processedCount++;
        if (processedCount === imageFiles.length) {
          const validImages = processedImages.filter(img => img);
          if (validImages.length > 0) {
            resolve({
              success: true,
              message: `✅ ${validImages.length}개 이미지가 추가되었습니다.`,
              images: validImages
            });
          } else {
            resolve({
              success: false,
              message: '이미지 처리에 실패했습니다.',
              images: []
            });
          }
        }
      };
      
      reader.readAsDataURL(file);
    });
  });
};

// 드래그 앤 드롭 이벤트 핸들러 생성
export const createDragHandlers = (setIsDragOver, processCallback) => {
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const result = await processImageFiles(files);
    processCallback(result);
  };

  return { handleDragOver, handleDragLeave, handleDrop };
};

// 이미지 유효성 검사
export const validateImage = (imageIndex, images) => {
  if (imageIndex < 0 || imageIndex >= images.length) {
    return {
      valid: false,
      message: '유효하지 않은 이미지입니다.'
    };
  }

  const image = images[imageIndex];
  if (!image || !image.file) {
    return {
      valid: false,
      message: '이미지 파일이 없습니다.'
    };
  }

  return {
    valid: true,
    image: image
  };
};