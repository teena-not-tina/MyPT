import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { User } from 'lucide-react';
// 페이지 import
import DashboardPage from './pages/Home/DashboardPage';
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/SignupPage';
import IngredientInputPage from './pages/Diet/IngredientInputPage';
import MenuRecommendationPage from './pages/Diet/MenuRecommendationPage'; 
import ExerciseCameraPage from './pages/Routine/ExerciseCameraPage';
import RoutineDetailPage from './pages/Routine/RoutineDetailPage';
import RoutineOverviewPage from './pages/Routine/RoutineOverviewPage';
import ChatbotPage from './pages/AI/ChatbotPage';
import ChatbotAvatarPage from './pages/AI/AvatarProgressPage';
import MainPage from './pages/CV/MainPage';
import FoodDetection from './pages/CVcomponents/FoodDetection';
import ImageUploader from './pages/CVcomponents/ImageUploader';
import FridgeManager from './pages/CVcomponents/FridgeManager';
import NotFoundPage from './pages/NotFoundPage';

// 네비게이션 컴포넌트
function Navigation() {
  return (
    <nav className="bg-white shadow-sm border-b p-4">
      <div className="flex justify-between items-center">
        <div className="flex space-x-4">
          <Link to="/diet" className="text-blue-600 hover:text-blue-800 font-medium">식단 기록</Link>
          <Link to="/diet/recommendation" className="text-blue-600 hover:text-blue-800 font-medium">메뉴 추천</Link>
          <Link to="/dashboard" className="text-blue-600 hover:text-blue-800 font-medium">대시보드</Link>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-gray-700 flex items-center">
            <User className="h-4 w-4 mr-1" />
            게스트
          </span>
        </div>
      </div>
    </nav>
  );
}

// 메인 App 컴포넌트
function App() {
  // 이미지/재료 등 상태는 필요시만 사용
  const [images, setImages] = useState([]);
  const handleImagesSelected = (files) => setImages(files);

  const [userId] = useState('guest_' + Date.now());
  const [ingredients, setIngredients] = useState([]);
  const onIngredientsChange = (newIngredients) => setIngredients(newIngredients);

  return (
    <Router>
      <div className="App min-h-screen bg-gray-50">
        <Navigation />
        <Routes>
          <Route path="/" element={<IngredientInputPage />} />
          <Route path="/diet" element={<IngredientInputPage />} />
          <Route path="/diet/recommendation" element={<MenuRecommendationPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/routine" element={<RoutineOverviewPage />} />
          <Route path="/routine/camera" element={<ExerciseCameraPage />} />
          <Route path="/routine/detail" element={<RoutineDetailPage />} />
          <Route path="/chatbot" element={<ChatbotPage />} />
          <Route path="/chatbot/avatar" element={<ChatbotAvatarPage />} />
          <Route path="/cv" element={<MainPage />} />
          <Route path="/food-detection" element={<FoodDetection />} />
          <Route path="/image-uploader" element={<ImageUploader onImagesSelected={handleImagesSelected} />} />
          <Route path="/fridge-manager" element={<FridgeManager userId={userId} ingredients={ingredients} onIngredientsChange={onIngredientsChange} />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;