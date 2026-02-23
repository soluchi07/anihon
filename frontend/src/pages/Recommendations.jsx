import React, { useCallback, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import usePolling from "../components/PollingHook";
import AnimeCard from "../components/AnimeCard";
import { 
  fetchRecommendations, 
  likeAnime, 
  rateAnime, 
  fetchUserInteractions,
  fetchUserLists,
  addToList,
  removeFromList
} from "../api/apiClient";
import "../styles/Recommendations.css";

export default function Recommendations() {
  const { user } = useAuth();
  const [likedIds, setLikedIds] = useState(new Set());
  const [ratings, setRatings] = useState({});
  const [animeLists, setAnimeLists] = useState({}); // maps anime_id -> list_type

  const fetchFn = useCallback(async () => {
    const res = await fetchRecommendations(user.userId);
    return res.recommendations || [];
  }, [user.userId]);

  const { data, loading } = usePolling(fetchFn, 3000);

  // Load user interactions on mount
  useEffect(() => {
    async function loadInteractions() {
      try {
        const res = await fetchUserInteractions(user.userId);
        if (res.status === 'ok' && res.interactions) {
          const liked = new Set();
          const ratingsMap = {};
          
          res.interactions.forEach(interaction => {
            if (interaction.liked) {
              liked.add(interaction.anime_id);
            }
            if (interaction.rating) {
              ratingsMap[interaction.anime_id] = interaction.rating;
            }
          });
          
          setLikedIds(liked);
          setRatings(ratingsMap);
        }
      } catch (err) {
        console.error("Failed to load interactions:", err);
      }
    }

    async function loadLists() {
      try {
        const res = await fetchUserLists(user.userId);
        if (res.status === 'ok' && res.lists) {
          const listsMap = {};
          
          // Flatten all lists into a map of anime_id -> list_type
          Object.entries(res.lists).forEach(([listType, items]) => {
            items.forEach(item => {
              listsMap[item.anime_id] = listType;
            });
          });
          
          setAnimeLists(listsMap);
        }
      } catch (err) {
        console.error("Failed to load lists:", err);
      }
    }
    
    loadInteractions();
    loadLists();
  }, [user.userId]);

  const handleLike = useCallback(async (animeId) => {
    if (likedIds.has(animeId)) return;
    try {
      await likeAnime(user.userId, animeId);
      setLikedIds((prev) => new Set([...prev, animeId]));
    } catch (err) {
      console.error("Failed to like anime:", err);
    }
  }, [user.userId, likedIds]);

  const handleRate = useCallback(async (animeId, rating) => {
    try {
      await rateAnime(user.userId, animeId, rating);
      setRatings((prev) => ({ ...prev, [animeId]: rating }));
    } catch (err) {
      console.error("Failed to rate anime:", err);
    }
  }, [user.userId]);

  const handleListChange = useCallback(async (animeId, listType) => {
    try {
      if (listType === null) {
        // Remove from current list
        const currentListType = animeLists[animeId];
        if (currentListType) {
          await removeFromList(user.userId, animeId, currentListType);
          setAnimeLists((prev) => {
            const newLists = { ...prev };
            delete newLists[animeId];
            return newLists;
          });
        }
      } else {
        // Add to new list (or move from current list)
        await addToList(user.userId, animeId, listType);
        setAnimeLists((prev) => ({ ...prev, [animeId]: listType }));
      }
    } catch (err) {
      console.error("Failed to update list:", err);
    }
  }, [user.userId, animeLists]);

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
              rating={ratings[anime.anime_id] || 0}
              onRate={handleRate}
              currentList={animeLists[anime.anime_id] || null}
              onListChange={handleListChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
