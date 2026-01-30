import React from "react";
import { Link } from "react-router-dom";
import "../styles/Landing.css";

export default function Landing() {
  return (
    <div className="landing-container">
      <div className="landing-content">
        <h1 className="landing-title">🎬 AnimeRec</h1>
        <p className="landing-subtitle">
          Discover anime you'll love with AI-powered personalized recommendations
        </p>
        
        <div className="landing-features">
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3 className="feature-title">Personalized</h3>
            <p className="feature-description">
              Get recommendations tailored to your unique taste
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3 className="feature-title">Fast & Smart</h3>
            <p className="feature-description">
              Powered by advanced algorithms for instant results
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3 className="feature-title">Data-Driven</h3>
            <p className="feature-description">
              Based on 25,000+ anime from MyAnimeList
            </p>
          </div>
        </div>

        <div className="landing-cta">
          <Link to="/onboarding" className="cta-primary">
            Get Started
          </Link>
          <Link to="/recommendations" className="cta-secondary">
            View Recommendations
          </Link>
        </div>
      </div>
    </div>
  );
}
