import React, { useState } from 'react';
import HomePage from './HomePage';
import CookingMode from './CookingMode';
import EatingMode from './EatingMode';

const FoodDetectionApp = () => {
  const [currentMode, setCurrentMode] = useState('home');
  
  return (
    <div className="min-h-screen">
      {currentMode === 'home' && (
        <HomePage 
          onStartCooking={() => setCurrentMode('homeCooking')}
          onStartEating={() => setCurrentMode('eating')}
        />
      )}
      {currentMode === 'homeCooking' && (
        <CookingMode onBack={() => setCurrentMode('home')} />
      )}
      {currentMode === 'eating' && (
        <EatingMode onBack={() => setCurrentMode('home')} />
      )}
    </div>
  );
};

export default FoodDetectionApp;