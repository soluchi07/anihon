import React from 'react';
import { useNavigate } from 'react-router-dom';
import RatingInput from './RatingInput';
import ListSelector from './ListSelector';
import '../styles/AnimeCard.css';

export default function AnimeCard({ anime, liked, onLike, rating, onRate, currentList, onListChange }) {
  const navigate = useNavigate();
  const score = anime.score != null ? Number(anime.score).toFixed(2) : 'N/A';
  const popularity = anime.popularity_score != null ? Number(anime.popularity_score).toFixed(0) : 'N/A';
  
  const getScoreClass = (score) => {
    if (score === 'N/A') return '';
    const numScore = Number(score);
    if (numScore >= 0.6) return 'high';
    if (numScore >= 0.4) return 'medium';
    return 'low';
  };

  const handleCardClick = (e) => {
    // Don't navigate if clicking interactive elements
    if (e.target.closest('.like-button') || 
        e.target.closest('.rating-input') ||
        e.target.closest('.rating-stars') ||
        e.target.closest('.list-selector')) {
      return;
    }
    navigate(`/anime/${anime.anime_id}`);
  };

  const handleRate = (newRating) => {
    if (onRate) {
      onRate(anime.anime_id, newRating);
    }
  };

  const handleListChange = (listType) => {
    if (onListChange) {
      onListChange(anime.anime_id, listType);
    }
  };

  return (
    <div className="anime-card" onClick={handleCardClick}>
      <div className="anime-card-image-container">
        {anime.image_url ? (
          <img 
            src={anime.image_url} 
            alt={anime.title} 
            className="anime-card-image"
            loading="lazy"
          />
        ) : (
          <div className="anime-card-empty-state">🎬</div>
        )}
        {score !== 'N/A' && (
          <div className="anime-card-badge">
            ⭐ {score}
          </div>
        )}
      </div>
      
      <div className="anime-card-content">
        <h3 className="anime-card-title">{anime.title}</h3>
        
        {anime.genres && anime.genres.length > 0 && (
          <div className="anime-card-genres">
            {anime.genres.slice(0, 3).map((genre, idx) => (
              <span key={idx} className="genre-tag">{genre}</span>
            ))}
          </div>
        )}
        
        <div className="anime-card-stats">
          <div className="stat-item">
            <span className="stat-label">Match</span>
            <span className={`stat-value ${getScoreClass(score)}`}>
              {score !== 'N/A' ? `${(Number(score) * 100).toFixed(0)}%` : 'N/A'}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Popularity</span>
            <span className="stat-value">
              {popularity !== 'N/A' ? `${popularity}` : 'N/A'}
            </span>
          </div>
        </div>

        {onRate && (
          <div className="anime-card-rating" onClick={(e) => e.stopPropagation()}>
            <span className="rating-label">Your Rating:</span>
            <RatingInput 
              currentRating={rating || 0} 
              onRate={handleRate}
            />
          </div>
        )}

        {onListChange && (
          <div className="anime-card-list" onClick={(e) => e.stopPropagation()}>
            <ListSelector 
              currentList={currentList || null}
              onListChange={handleListChange}
            />
          </div>
        )}

        {onLike && (
          <button
            className={`like-button ${liked ? 'liked' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              onLike(anime.anime_id);
            }}
            aria-label={liked ? 'Unlike' : 'Like'}
          >
            {liked ? '❤️ Liked' : '🤍 Like'}
          </button>
        )}
      </div>
    </div>
  );
}
