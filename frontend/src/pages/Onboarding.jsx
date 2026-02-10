import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { submitOnboarding, startRecommendationJob } from "../api/apiClient";
import "../styles/Onboarding.css";

const GENRES = [
  "Action",
  "Adventure",
  "Drama",
  "Comedy",
  "Romance",
  "Sci-Fi",
  "Fantasy",
  "Slice of Life",
  "Mystery",
  "Thriller",
  "Horror",
  "Sports",
];

const STUDIOS = [
  "MAPPA",
  "Bones",
  "A-1 Pictures",
  "Wit Studio",
  "Ufotable",
  "Kyoto Animation",
  "Madhouse",
  "Production I.G",
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [genres, setGenres] = useState([]);
  const [studios, setStudios] = useState([]);
  const [preferPopular, setPreferPopular] = useState(true);
  const [status, setStatus] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleSelection = (value, current, setCurrent) => {
    if (current.includes(value)) {
      setCurrent(current.filter((v) => v !== value));
    } else {
      setCurrent([...current, value]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatus("Submitting your preferences...");
    try {
      const prefs = {
        genres,
        studios,
        opt_in_popularity: preferPopular,
      };
      await submitOnboarding(user.userId, prefs);
      await startRecommendationJob(user.userId, {
        opt_in_popularity: preferPopular,
        top_n: 20,
      });
      setStatus("Success! Generating your recommendations...");
      setTimeout(() => navigate("/recommendations"), 2000);
    } catch (err) {
      setStatus("Error: " + err.message);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="onboarding-header">
          <h1 className="onboarding-title">Tell Us Your Preferences</h1>
          <p className="onboarding-description">
            Select your favorite genres and studios to get personalized anime recommendations
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-section user-id-input">
            <label className="form-label">Your User ID</label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              required
            />
          </div>

          <div className="form-section">
            <label className="form-label">Favorite Genres</label>
            <div className="selection-grid">
              {GENRES.map((g) => (
                <div key={g} className="selection-item">
                  <input
                    type="checkbox"
                    id={`genre-${g}`}
                    checked={genres.includes(g)}
                    onChange={() => toggleSelection(g, genres, setGenres)}
                  />
                  <label htmlFor={`genre-${g}`}>{g}</label>
                </div>
              ))}
            </div>
          </div>

          <div className="form-section">
            <label className="form-label">Favorite Studios</label>
            <div className="selection-grid">
              {STUDIOS.map((s) => (
                <div key={s} className="selection-item">
                  <input
                    type="checkbox"
                    id={`studio-${s}`}
                    checked={studios.includes(s)}
                    onChange={() => toggleSelection(s, studios, setStudios)}
                  />
                  <label htmlFor={`studio-${s}`}>{s}</label>
                </div>
              ))}
            </div>
          </div>

          <div className="form-section">
            <div className="preference-toggle">
              <input
                type="checkbox"
                id="prefer-popular"
                checked={preferPopular}
                onChange={(e) => setPreferPopular(e.target.checked)}
              />
              <label htmlFor="prefer-popular" className="preference-label">
                Include popularity in recommendations
              </label>
            </div>
          </div>

          <div className="submit-section">
            <button type="submit" className="submit-button" disabled={isSubmitting}>
              {isSubmitting ? "Generating Recommendations..." : "Get My Recommendations"}
            </button>
            {status && (
              <div className={`status-message ${
                status.includes("Error") ? "error" : 
                status.includes("Success") ? "success" : "info"
              }`}>
                {status}
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
