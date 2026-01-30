import React, { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import usePolling from "../components/PollingHook";
import AnimeCard from "../components/AnimeCard";
import { fetchRecommendations } from "../api/apiClient";
import "../styles/Recommendations.css";

export default function Recommendations() {
  const [userId, setUserId] = useState("demo-user");

  const fetchFn = useCallback(async () => {
    const res = await fetchRecommendations(userId);
    return res.recommendations || [];
  }, [userId]);

  const { data, loading } = usePolling(fetchFn, 3000);

  return (
    <div className="recommendations-container">
      <div className="recommendations-header">
        <h1 className="recommendations-title">Your Anime Recommendations</h1>
        <div className="user-input-section">
          <label>User ID:</label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter your user ID"
          />
        </div>
        {data && data.length > 0 && (
          <div className="recommendations-count">
            📊 {data.length} recommendations found
          </div>
        )}
      </div>

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Fetching your personalized recommendations...</p>
        </div>
      )}

      {!loading && data && data.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📺</div>
          <p className="empty-state-text">
            No recommendations yet. Complete onboarding to get started!
          </p>
          <Link to="/onboarding" className="btn empty-state-link">
            Start Onboarding
          </Link>
        </div>
      )}

      {!loading && data && data.length > 0 && (
        <div className="recommendations-grid">
          {data.map((anime) => (
            <AnimeCard key={anime.anime_id} anime={anime} />
          ))}
        </div>
      )}
    </div>
  );
}
