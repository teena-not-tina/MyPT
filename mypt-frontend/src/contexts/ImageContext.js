import React, { createContext, useContext, useState } from 'react';
import { DEFAULT_IMAGES } from '../constants/images';

const ImageContext = createContext();

export const ImageProvider = ({ children }) => {
  const [images, setImages] = useState({
    profile: DEFAULT_IMAGES.PROFILE,
    food: DEFAULT_IMAGES.FOOD,
    exercise: DEFAULT_IMAGES.EXERCISE
  });

  const updateImage = (type, newImage) => {
    setImages(prev => ({
      ...prev,
      [type]: newImage
    }));
  };

  return (
    <ImageContext.Provider value={{ images, updateImage }}>
      {children}
    </ImageContext.Provider>
  );
};

export const useImages = () => {
  const context = useContext(ImageContext);
  if (!context) {
    throw new Error('useImages must be used within an ImageProvider');
  }
  return context;
};