import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Onboarding from "./pages/Onboarding";
import Recommendations from "./pages/Recommendations";
import AnimeProfile from "./pages/AnimeProfile";
import MyLists from "./pages/MyLists";
import "./styles/tokens.css";
import "./styles/App.css";

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>Loading...</div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function Navbar() {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();

  // Initialize from the class that may have been set by the inline script in index.html
  const [motionReduced, setMotionReduced] = useState(
    () => document.documentElement.classList.contains("motion-reduced")
  );

  const toggleMotion = () => {
    const next = !motionReduced;
    setMotionReduced(next);
    document.documentElement.classList.toggle("motion-reduced", next);
    try {
      localStorage.setItem("motionReduced", String(next));
    } catch (e) {}
  };

  const hiddenPaths = ["/", "/login", "/signup"];
  if (hiddenPaths.includes(location.pathname)) return null;

  return (
    <nav className="navbar" aria-label="Main navigation">
      <div className="navbar-content">
        <Link to="/" className="navbar-brand">
          AniHon
        </Link>

        <div className="navbar-links">
          {isAuthenticated ? (
            <>
              <Link to="/onboarding">Get Started</Link>
              <Link to="/recommendations">Recommendations</Link>
              <Link to="/lists">My Lists</Link>
              <span className="navbar-user" aria-label={`Signed in as ${user?.email || "User"}`}>
                {user?.email || "User"}
              </span>
              <button
                className="navbar-motion-toggle"
                onClick={toggleMotion}
                aria-pressed={motionReduced}
                aria-label={motionReduced ? "Enable animations" : "Reduce motion"}
                title={motionReduced ? "Enable animations" : "Reduce motion"}
              >
                {motionReduced ? "Motion On" : "Motion Off"}
              </button>
              <button onClick={logout} className="navbar-logout">
                Log Out
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Log In</Link>
              <Link to="/signup">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app-container">
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <Navbar />
          <main id="main-content">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route
                path="/anime/:id"
                element={
                  <ProtectedRoute>
                    <AnimeProfile />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/onboarding"
                element={
                  <ProtectedRoute>
                    <Onboarding />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/recommendations"
                element={
                  <ProtectedRoute>
                    <Recommendations />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/lists"
                element={
                  <ProtectedRoute>
                    <MyLists />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </Router>
  );
}
