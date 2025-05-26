import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Chatbot from './components/Chatbot/Chatbot';
import MainPage from './components/MainPage/MainPage';
import ExerciseStart from './components/Exercise/ExerciseStart';
import ExerciseTracking from './components/Exercise/ExerciseTracking';
import DietChoice from './components/Diet/DietChoice';
import DietCapture from './components/Diet/DietCapture';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/main" element={<MainPage />} />
        <Route path="/exercise/start" element={<ExerciseStart />} />
        <Route path="/exercise/tracking" element={<ExerciseTracking />} />
        <Route path="/diet/choice" element={<DietChoice />} />
        <Route path="/diet/capture" element={<DietCapture />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
