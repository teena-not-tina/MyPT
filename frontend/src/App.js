import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardPage from './pages/Home/DashboardPage';
import ChatbotPage from './pages/AI/ChatbotPage';
import RoutineOverviewPage from './pages/Routine/RoutineOverviewPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/chatbot" element={<ChatbotPage />} />
        <Route path="/routine" element={<RoutineOverviewPage />} />
        {/* 필요하다면 다른 라우트도 추가 */}
      </Routes>
    </Router>
  );
}

export default App;