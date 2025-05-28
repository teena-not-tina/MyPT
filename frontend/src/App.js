// import React from "react";
// import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
// import LandingPage from "./components/Auth/LandingPage";
// import MainPage from "./pages/MainPage";

// /**
//  * App routing: LandingPage (/) and MainPage (/main).
//  * Add authentication context/provider as needed.
//  */
// function App() {
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<LandingPage />} />
//         <Route path="/main" element={<MainPage />} />
//       </Routes>
//     </Router>
//   );
// }

// export default App;

// frontend/src/App.js

// frontend/src/App.js

import React from 'react';
import WorkoutRoutine from './components/Exercise/WorkoutRoutine';
// Import other components as needed

function App() {
  return (
    <div className="App">
      {/* Your app header/navigation here */}
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">B-Fit Health App</h1>
      </header>

      {/* Main content */}
      <main className="min-h-screen bg-gray-50">
        <WorkoutRoutine />
      </main>

      {/* You can add routing later */}
      {/* Example with React Router:
      <Router>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/workout" element={<WorkoutRoutine />} />
          <Route path="/diet" element={<Diet />} />
          <Route path="/chat" element={<Chatbot />} />
        </Routes>
      </Router>
      */}
    </div>
  );
}

export default App;