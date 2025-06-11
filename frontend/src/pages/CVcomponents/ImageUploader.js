// frontend/src/components/Diet/components/ImageUploader.js
import React, { useRef } from 'react';

const ImageUploader = ({ onImagesSelected }) => {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      onImagesSelected(files);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onImagesSelected(files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="w-full border-2 border-dashed border-gray-400 p-6 rounded-lg text-center bg-gray-50 hover:bg-gray-100 transition"
    >
      <p className="mb-3 text-gray-600">이미지를 드래그하거나 클릭하여 업로드</p>
      <button
        onClick={() => fileInputRef.current.click()}
        className="px-4 py-2 bg-blue-500 text-white font-semibold rounded hover:bg-blue-600 transition"
      >
        이미지 선택
      </button>
      <input
        type="file"
        accept="image/*"
        multiple
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
};

export default ImageUploader;
