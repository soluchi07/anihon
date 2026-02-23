import React, { useState } from 'react';
import '../styles/RatingInput.css';

export default function RatingInput({ currentRating = 0, onRate, disabled = false }) {
  const [hoverRating, setHoverRating] = useState(0);

  const handleClick = (rating) => {
    if (!disabled && onRate) {
      onRate(rating);
    }
  };

  const handleMouseEnter = (rating) => {
    if (!disabled) {
      setHoverRating(rating);
    }
  };

  const handleMouseLeave = () => {
    setHoverRating(0);
  };

  const getStarDisplay = (position) => {
    const rating = hoverRating || currentRating;
    if (rating >= position) {
      return '⭐'; // Filled star
    }
    return '☆'; // Empty star
  };

  return (
    <div className={`rating-input ${disabled ? 'disabled' : ''}`}>
      <div className="rating-stars" onMouseLeave={handleMouseLeave}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((position) => (
          <span
            key={position}
            className={`star ${(hoverRating || currentRating) >= position ? 'filled' : ''}`}
            onClick={() => handleClick(position)}
            onMouseEnter={() => handleMouseEnter(position)}
            role="button"
            aria-label={`Rate ${position} out of 10`}
            tabIndex={disabled ? -1 : 0}
          >
            {getStarDisplay(position)}
          </span>
        ))}
      </div>
      {currentRating > 0 && (
        <span className="rating-value">{currentRating}/10</span>
      )}
    </div>
  );
}
