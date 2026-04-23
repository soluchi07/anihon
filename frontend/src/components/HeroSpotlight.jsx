import React from 'react';
import { useNavigate } from 'react-router-dom';
import ListSelector from './ListSelector';
import '../styles/HeroSpotlight.css';

export default function HeroSpotlight({ anime, liked, onLike, currentList, onListChange }) {
  const navigate = useNavigate();
  const matchPct = anime.score != null ? `${(Number(anime.score) * 100).toFixed(0)}%` : null;

  const handleListChange = (listType) => {
    if (onListChange) onListChange(anime.anime_id, listType);
  };

  return (
    <section className="hero-spotlight" aria-label={`Top pick: ${anime.title}`}>
      {anime.image_url && (
        <div className="hero-backdrop" aria-hidden="true">
          <img src={anime.image_url} alt="" className="hero-backdrop-img" />
        </div>
      )}

      <div className="hero-content">
        <div className="hero-poster">
          {anime.image_url ? (
            <img
              src={anime.image_url}
              alt={`${anime.title} poster`}
              className="hero-poster-img"
            />
          ) : (
            <div className="hero-poster-empty" aria-hidden="true" />
          )}
        </div>

        <div className="hero-info">
          <span className="hero-eyebrow">✦ Top Pick For You</span>

          <h2 className="hero-title">{anime.title}</h2>

          {anime.genres && anime.genres.length > 0 && (
            <div className="hero-genres">
              {anime.genres.slice(0, 4).map((g, i) => (
                <span key={i} className="hero-genre-tag">{g}</span>
              ))}
            </div>
          )}

          <div className="hero-scores">
            {matchPct && (
              <span className="hero-match-badge">{matchPct} match</span>
            )}
            {anime.score != null && (
              <span className="hero-score">
                {(Number(anime.score) * 10).toFixed(1)}
              </span>
            )}
          </div>

          {anime.synopsis && (
            <p className="hero-synopsis">
              {anime.synopsis.length > 220
                ? `${anime.synopsis.slice(0, 220)}…`
                : anime.synopsis}
            </p>
          )}

          <div className="hero-actions">
            <button
              className="hero-btn hero-btn-view"
              onClick={() => navigate(`/anime/${anime.anime_id}`)}
            >
              View Details →
            </button>

            {onLike && (
              <button
                className={`hero-btn hero-btn-like ${liked ? 'liked' : ''}`}
                onClick={() => onLike(anime.anime_id)}
                aria-label={liked ? `Unlike ${anime.title}` : `Like ${anime.title}`}
              >
                {liked ? '♥ Liked' : '♡ Like'}
              </button>
            )}

            {onListChange && (
              <div onClick={(e) => e.stopPropagation()}>
                <ListSelector
                  currentList={currentList || null}
                  onListChange={handleListChange}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
