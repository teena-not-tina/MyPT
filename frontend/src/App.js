// frontend/src/App.js

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import WorkoutRoutine from './components/Exercise/WorkoutRoutine';
import MainPage from './pages/MainPage';

// Import other components as needed
// import LandingPage from './components/Auth/LandingPage';

function App() {
  return (
    <Router>
      <div className="App">
        {/* Your app header/navigation here */}
        <header className="bg-blue-600 text-white p-4">
          <h1 className="text-2xl font-bold text-center">B-Fit Health App</h1>
        </header>

        {/* Main content with routing */}x
        <main className="min-h-screen bg-gray-50">
          <Routes>
            {/* 홈페이지 */}
            <Route path="/" element={<WorkoutRoutine />} />
            
            {/* 메인 페이지 */}
            <Route path="/main" element={<MainPage />} />
            
            {/* 운동 루틴 */}
            <Route path="/workout" element={<WorkoutRoutine />} />
            
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;