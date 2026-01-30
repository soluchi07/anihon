import React from 'react';
import '../styles/AnimeCard.css';

export default function AnimeCard({ anime }) {
  const score = anime.score != null ? Number(anime.score).toFixed(2) : 'N/A';
  const popularity = anime.popularity_score != null ? Number(anime.popularity_score).toFixed(0) : 'N/A';
  
  const getScoreClass = (score) => {
    if (score === 'N/A') return '';
    const numScore = Number(score);
    if (numScore >= 0.6) return 'high';
    if (numScore >= 0.4) return 'medium';
    return 'low';
  };

  return (
    <div className="anime-card">
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
      </div>
    </div>
  );
}
