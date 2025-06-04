export const processImageFiles = (files) => {
  return new Promise((resolve) => {
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
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
          resolve(processedImages.filter(img => img));
        }
      };
      
      reader.readAsDataURL(file);
    });
  });
};

export const extractIngredientImages = async (detections, originalImage) => {
  // 기존 이미지 추출 로직을 여기로 이동
  if (!detections || detections.length === 0 || !originalImage) {
    return [];
  }

  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      // 이미지 크롭 로직
      // ...
      resolve(extractedImages);
    };
    img.src = originalImage;
  });
};