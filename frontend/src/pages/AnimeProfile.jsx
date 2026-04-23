import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  fetchAnimeDetails, 
  fetchSimilarAnime, 
  rateAnime, 
  fetchUserInteractions, 
  likeAnime,
  fetchUserLists,
  addToList,
  removeFromList
} from '../api/apiClient';
import { useAuth } from '../contexts/AuthContext';
import AnimeCard from '../components/AnimeCard';
import RatingInput from '../components/RatingInput';
import ListSelector from '../components/ListSelector';
import '../styles/AnimeProfile.css';

export default function AnimeProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [anime, setAnime] = useState(null);
  const [similarAnime, setSimilarAnime] = useState([]);
  const [loading, setLoading] = useState(true);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userRating, setUserRating] = useState(0);
  const [userLiked, setUserLiked] = useState(false);
  const [currentList, setCurrentList] = useState(null);

  useEffect(() => {
    async function loadAnimeDetails() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchAnimeDetails(id);
        
        if (data.status === 'ok' && data.anime) {
          setAnime(data.anime);
        } else {
          setError('Anime not found');
        }
      } catch (err) {
        console.error('Error loading anime:', err);
        setError('Failed to load anime details');
      } finally {
        setLoading(false);
      }
    }

    loadAnimeDetails();
  }, [id]);

  useEffect(() => {
    async function loadSimilarAnime() {
      if (!anime) return;
      
      try {
        setSimilarLoading(true);
        const data = await fetchSimilarAnime(id);
        
        if (data.status === 'ok' && data.similar_anime) {
          setSimilarAnime(data.similar_anime);
        }
      } catch (err) {
        console.error('Error loading similar anime:', err);
        // Don't show error for similar anime - just don't display them
      } finally {
        setSimilarLoading(false);
      }
    }

    loadSimilarAnime();
  }, [anime, id]);

  // Load user interactions if authenticated
  useEffect(() => {
    async function loadUserInteractions() {
      if (!isAuthenticated || !user) return;
      
      try {
        const data = await fetchUserInteractions(user.userId);
        if (data.status === 'ok' && data.interactions) {
          const interaction = data.interactions.find(
            int => int.anime_id === parseInt(id)
          );
          
          if (interaction) {
            setUserRating(interaction.rating || 0);
            setUserLiked(interaction.liked || false);
          }
        }
      } catch (err) {
        console.error('Error loading user interactions:', err);
      }
    }

    async function loadUserList() {
      if (!isAuthenticated || !user) return;
      
      try {
        const data = await fetchUserLists(user.userId);
        if (data.status === 'ok' && data.lists) {
          // Find which list this anime is in
          for (const [listType, items] of Object.entries(data.lists)) {
            if (items.some(item => item.anime_id === parseInt(id))) {
              setCurrentList(listType);
              break;
            }
          }
        }
      } catch (err) {
        console.error('Error loading user lists:', err);
      }
    }

    loadUserInteractions();
    loadUserList();
  }, [isAuthenticated, user, id]);

  const handleRate = async (rating) => {
    if (!isAuthenticated || !user) {
      navigate('/login');
      return;
    }

    try {
      await rateAnime(user.userId, parseInt(id), rating);
      setUserRating(rating);
    } catch (err) {
      console.error('Error rating anime:', err);
    }
  };

  const handleLike = async () => {
    if (!isAuthenticated || !user) {
      navigate('/login');
      return;
    }

    if (userLiked) return; // Already liked

    try {
      await likeAnime(user.userId, parseInt(id));
      setUserLiked(true);
    } catch (err) {
      console.error('Error liking anime:', err);
    }
  };

  const handleListChange = async (listType) => {
    if (!isAuthenticated || !user) {
      navigate('/login');
      return;
    }

    try {
      if (listType === null) {
        // Remove from current list
        if (currentList) {
          await removeFromList(user.userId, parseInt(id), currentList);
          setCurrentList(null);
        }
      } else {
        // Add to new list
        await addToList(user.userId, parseInt(id), listType);
        setCurrentList(listType);
      }
    } catch (err) {
      console.error('Error updating list:', err);
    }
  };

  if (loading) {
    return (
      <div className="anime-profile-container">
        <div className="loading-state">Loading anime details...</div>
      </div>
    );
  }

  if (error || !anime) {
    return (
      <div className="anime-profile-container">
        <div className="error-state">
          <h2>{error || 'Anime not found'}</h2>
          <button onClick={() => navigate('/recommendations')} className="back-button">
            Back to Recommendations
          </button>
        </div>
      </div>
    );
  }

  const malScore = anime.score != null ? Number(anime.score).toFixed(2) : 'N/A';
  const popularity = anime.popularity != null ? anime.popularity : 'N/A';

  return (
    <div className="anime-profile-container">
      {/* Hero Section */}
      <div className="anime-hero">
        <div className="anime-hero-backdrop">
          {anime.image_url && (
            <img src={anime.image_url} alt="" className="backdrop-image" />
          )}
        </div>
        
        <div className="anime-hero-content">
          <div className="anime-poster">
            {anime.image_url ? (
              <img src={anime.image_url} alt={anime.title} />
            ) : (
              <div className="empty-poster" aria-hidden="true" />
            )}
          </div>
          
          <div className="anime-hero-info">
            <h1 className="anime-title">{anime.title}</h1>
            
            {anime.alternate_titles && anime.alternate_titles.length > 0 && (
              <div className="alternate-titles">
                {anime.alternate_titles.slice(0, 2).join(' • ')}
              </div>
            )}
            
            <div className="anime-meta">
              {anime.type && <span className="meta-badge">{anime.type}</span>}
              {anime.year && <span className="meta-item">{anime.year}</span>}
              {anime.episodes && <span className="meta-item">{anime.episodes} episodes</span>}
              {anime.rating && <span className="meta-badge rating-badge">{anime.rating}</span>}
            </div>
            
            <div className="anime-scores">
              {malScore !== 'N/A' && (
                <div className="score-item">
                  <span className="score-label">MAL Score</span>
                  <span className="score-value">★ {malScore}</span>
                </div>
              )}
              {popularity !== 'N/A' && (
                <div className="score-item">
                  <span className="score-label">Popularity</span>
                  <span className="score-value">#{popularity}</span>
                </div>
              )}
              {anime.favorites && (
                <div className="score-item">
                  <span className="score-label">Favorites</span>
                  <span className="score-value">♥ {anime.favorites.toLocaleString()}</span>
                </div>
              )}
            </div>

            {/* User Interactions */}
            {isAuthenticated ? (
              <div className="user-interactions">
                <div className="interaction-section">
                  <h3 className="interaction-title">Your Rating</h3>
                  <RatingInput 
                    currentRating={userRating} 
                    onRate={handleRate}
                  />
                </div>
                
                <div className="interaction-section">
                  <h3 className="interaction-title">Add to List</h3>
                  <ListSelector 
                    currentList={currentList}
                    onListChange={handleListChange}
                  />
                </div>
                
                <div className="interaction-section">
                  <button
                    className={`profile-like-button ${userLiked ? 'liked' : ''}`}
                    onClick={handleLike}
                    disabled={userLiked}
                  >
                    {userLiked ? '♥ Liked' : '♡ Like'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="user-interactions-placeholder">
                <div className="interaction-note">
                  Please <span onClick={() => navigate('/login')} className="login-link">log in</span> to rate and interact
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Details Section */}
      <div className="anime-details">
        {/* Genres */}
        {anime.genres && anime.genres.length > 0 && (
          <div className="detail-section">
            <h2 className="section-title">Genres</h2>
            <div className="genre-list">
              {anime.genres.map((genre, idx) => (
                <span key={idx} className="genre-chip">{genre}</span>
              ))}
            </div>
          </div>
        )}

        {/* Studios */}
        {anime.studios && anime.studios.length > 0 && (
          <div className="detail-section">
            <h2 className="section-title">Studios</h2>
            <div className="studio-list">
              {anime.studios.map((studio, idx) => (
                <span key={idx} className="studio-chip">{studio}</span>
              ))}
            </div>
          </div>
        )}

        {/* Synopsis */}
        {anime.synopsis && (
          <div className="detail-section">
            <h2 className="section-title">Synopsis</h2>
            <p className="synopsis-text">{anime.synopsis}</p>
          </div>
        )}

        {/* Similar Anime Section */}
        <div className="detail-section similar-anime-section">
          <h2 className="section-title">Similar Anime</h2>
          {similarLoading ? (
            <div className="loading-similar">Loading similar anime...</div>
          ) : similarAnime.length > 0 ? (
            <div className="similar-anime-grid">
              {similarAnime.map((similar) => (
                <AnimeCard
                  key={similar.anime_id}
                  anime={similar}
                  variant="poster"
                />
              ))}
            </div>
          ) : (
            <div className="no-similar">
              No similar anime found. Check back later!
            </div>
          )}
        </div>
      </div>

      {/* Back Button */}
      <div className="profile-actions">
        <button onClick={() => navigate(-1)} className="back-button">
          ← Back
        </button>
      </div>
    </div>
  );
}
