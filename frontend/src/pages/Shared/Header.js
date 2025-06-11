// src/components/Shared/Header.js
import React from 'react';
import { useNavigate } from 'react-router-dom';

function Header({ title, showBackButton = false, onBackClick }) {
  const navigate = useNavigate();

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate(-1);
    }
  };

  return (
    <header className="flex items-center justify-between bg-white shadow-sm border-b border-gray-200 px-4 py-3 h-16 relative">
      {showBackButton && (
        <button 
          onClick={handleBackClick} 
          className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-50 hover:bg-gray-100 transition-colors duration-200 absolute left-4"
        >
          <i className="fas fa-arrow-left text-gray-700 text-lg"></i>
        </button>
      )}
      <h1 className={`text-lg font-semibold text-gray-900 flex-1 text-center ${showBackButton ? 'ml-14' : ''}`}>
        {title}
      </h1>
    </header>
  );
}

export default Header;