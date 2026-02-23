import React, { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import usePolling from "../components/PollingHook";
import AnimeCard from "../components/AnimeCard";
import { fetchRecommendations, likeAnime } from "../api/apiClient";
import "../styles/Recommendations.css";

export default function Recommendations() {
  const { user } = useAuth();
  const [likedIds, setLikedIds] = useState(new Set());

  const fetchFn = useCallback(async () => {
    const res = await fetchRecommendations(user.userId);
    return res.recommendations || [];
  }, [user.userId]);

  const { data, loading } = usePolling(fetchFn, 3000);

  const handleLike = useCallback(async (animeId) => {
    if (likedIds.has(animeId)) return;
    try {
      await likeAnime(user.userId, animeId);
      setLikedIds((prev) => new Set([...prev, animeId]));
    } catch (err) {
      console.error("Failed to like anime:", err);
    }
  }, [user.userId, likedIds]);

  return (
    <div className="recommendations-container">
      <div className="recommendations-header">
        <h1 className="recommendations-title">Your Anime Recommendations</h1>
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
            <AnimeCard
              key={anime.anime_id}
              anime={anime}
              liked={likedIds.has(anime.anime_id)}
              onLike={handleLike}
            />
          ))}
        </div>
      )}
    </div>
  );
}
