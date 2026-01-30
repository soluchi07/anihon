import React from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import Landing from "./pages/Landing";
import Onboarding from "./pages/Onboarding";
import Recommendations from "./pages/Recommendations";
import "./styles/App.css";

function Navbar() {
  const location = useLocation();
  if (location.pathname === '/') return null;
  
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/" className="navbar-brand">
          🎬 AnimeRec
        </Link>
        <div className="navbar-links">
          <Link to="/onboarding">Get Started</Link>
          <Link to="/recommendations">Recommendations</Link>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/recommendations" element={<Recommendations />} />
        </Routes>
      </div>
    </Router>
  );
}
