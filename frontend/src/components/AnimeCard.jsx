import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import RatingInput from './RatingInput';
import ListSelector from './ListSelector';
import '../styles/AnimeCard.css';

export default function AnimeCard({
  anime,
  liked,
  onLike,
  rating,
  onRate,
  currentList,
  onListChange,
  variant, // 'poster' | undefined (default card)
}) {
  const navigate = useNavigate();
  const score = anime.score != null ? Number(anime.score).toFixed(2) : 'N/A';
  const popularity = anime.popularity_score != null ? Number(anime.popularity_score).toFixed(0) : 'N/A';

  const getScoreClass = (s) => {
    if (s === 'N/A') return '';
    const n = Number(s);
    if (n >= 0.6) return 'high';
    if (n >= 0.4) return 'medium';
    return 'low';
  };

  const handleCardClick = (e) => {
    if (
      e.target.closest('.like-button') ||
      e.target.closest('.poster-like-btn') ||
      e.target.closest('.rating-input') ||
      e.target.closest('.rating-stars') ||
      e.target.closest('.list-selector')
    ) {
      return;
    }
    navigate(`/anime/${anime.anime_id}`);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      navigate(`/anime/${anime.anime_id}`);
    }
  };

  const handleRate = (newRating) => {
    if (onRate) onRate(anime.anime_id, newRating);
  };

  const handleListChange = (listType) => {
    if (onListChange) onListChange(anime.anime_id, listType);
  };

  /* ── Poster variant ── */
  if (variant === 'poster') {
    return (
      <article
        className="poster-card"
        onClick={handleCardClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label={`${anime.title}${score !== 'N/A' ? `, ${(Number(score) * 100).toFixed(0)}% match` : ''}`}
      >
        {/* Full-card image */}
        <div className="poster-image-wrap">
          {anime.image_url ? (
            <img
              src={anime.image_url}
              alt={`${anime.title} anime poster`}
              className="poster-image"
              loading="lazy"
            />
          ) : (
            <div className="poster-empty" aria-hidden="true" />
          )}
        </div>

        {/* Match badge — always visible */}
        {score !== 'N/A' && (
          <span className="poster-match-badge" aria-hidden="true">
            {(Number(score) * 100).toFixed(0)}% match
          </span>
        )}

        {/* Hover overlay */}
        <div className="poster-overlay" aria-hidden="true">
          <h3 className="poster-title">{anime.title}</h3>

          {anime.genres && anime.genres.length > 0 && (
            <div className="poster-genres">
              {anime.genres.slice(0, 2).map((g, i) => (
                <span key={i} className="poster-genre-tag">{g}</span>
              ))}
            </div>
          )}

          {onLike && (
            <div className="poster-actions">
              <button
                className={`poster-like-btn ${liked ? 'liked' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onLike(anime.anime_id);
                }}
                aria-label={liked ? `Unlike ${anime.title}` : `Like ${anime.title}`}
                tabIndex={-1}
              >
                {liked ? '♥ Liked' : '♡ Like'}
              </button>
            </div>
          )}
        </div>
      </article>
    );
  }

  /* ── Default variant ── */
  return (
    <article className="anime-card" onClick={handleCardClick}>
      <div className="anime-card-image-container">
        {anime.image_url ? (
          <img
            src={anime.image_url}
            alt={`${anime.title} anime poster`}
            className="anime-card-image"
            loading="lazy"
          />
        ) : (
          <div className="anime-card-empty-state" aria-hidden="true" />
        )}
        {score !== 'N/A' && (
          <div className="anime-card-badge">
            ★ {score}
          </div>
        )}
      </div>

      <div className="anime-card-content">
        <h3 className="anime-card-title">
          <Link
            to={`/anime/${anime.anime_id}`}
            className="anime-card-title-link"
            onClick={(e) => e.stopPropagation()}
          >
            {anime.title}
          </Link>
        </h3>

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
              {popularity !== 'N/A' ? popularity : 'N/A'}
            </span>
          </div>
        </div>

        {onRate && (
          <div className="anime-card-rating" onClick={(e) => e.stopPropagation()}>
            <span className="rating-label">Your Rating:</span>
            <RatingInput currentRating={rating || 0} onRate={handleRate} />
          </div>
        )}

        {onListChange && (
          <div className="anime-card-list" onClick={(e) => e.stopPropagation()}>
            <ListSelector currentList={currentList || null} onListChange={handleListChange} />
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
            {liked ? '♥ Liked' : '♡ Like'}
          </button>
        )}
      </div>
    </article>
  );
}
