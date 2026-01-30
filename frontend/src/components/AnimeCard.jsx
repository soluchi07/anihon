import React from 'react'

export default function AnimeCard({ anime }) {
  return (
    <div className="anime-card">
      <img src={anime.image_url} alt={anime.title} width={120} />
      <div>{anime.title}</div>
      <div>{anime.genres && anime.genres.join(', ')}</div>
      <div>Score: {anime.score == null ? 'N/A' : anime.score}</div>
    </div>
  )
}
