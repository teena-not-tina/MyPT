import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./components/Auth/LandingPage";
import MainPage from "./pages/MainPage";

/**
 * App routing: LandingPage (/) and MainPage (/main).
 * Add authentication context/provider as needed.
 */
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/main" element={<MainPage />} />
      </Routes>
    </Router>
  );
}

export default App;