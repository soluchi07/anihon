"""Recommendation algorithm utilities

- cosine_similarity between genre/studio vectors
- score composition with popularity normalization
- top-N recommendation selection
"""
import math
from typing import Dict, List, Set, Tuple, Optional


def normalize_vector(vec: Dict[str, float]) -> Dict[str, float]:
    """Normalize a vector so its magnitude is 1."""
    magnitude = math.sqrt(sum(v * v for v in vec.values()))
    if magnitude == 0:
        return vec
    return {k: v / magnitude for k, v in vec.items()}


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Returns value in [0, 1] where 1 is perfect match.
    """
    if not vec_a or not vec_b:
        return 0.0
    
    # Normalize both vectors
    vec_a_norm = normalize_vector(vec_a)
    vec_b_norm = normalize_vector(vec_b)
    
    # Compute dot product
    dot = sum(vec_a_norm.get(k, 0.0) * vec_b_norm.get(k, 0.0) for k in vec_a_norm)
    
    # Dot product of normalized vectors is already the cosine similarity
    return max(0.0, min(1.0, dot))


def build_anime_vector(anime: Dict, weight_genres: float = 1.0, weight_studios: float = 0.5, 
                       weight_year: float = 0.3, weight_score: float = 0.2, 
                       weight_popularity: float = 0.2) -> Dict[str, float]:
    """Build a feature vector from anime metadata.
    
    Features include genres, studios, year, score, and popularity.
    """
    vec = {}
    
    # Genre features (weighted)
    for genre in (anime.get("genres") or []):
        if isinstance(genre, str) and genre.strip():
            key = f"genre:{genre}"
            vec[key] = vec.get(key, 0.0) + weight_genres
    
    # Studio features (weighted)
    for studio in (anime.get("studios") or []):
        if isinstance(studio, str) and studio.strip():
            key = f"studio:{studio}"
            vec[key] = vec.get(key, 0.0) + weight_studios
    
    # Year feature (normalize to 0-1 range assuming 1960-2030)
    year = anime.get("year")
    if year is not None:
        try:
            year_int = int(year)
            year_norm = (year_int - 1960) / (2030 - 1960)
            year_norm = max(0.0, min(1.0, year_norm))
            vec[f"year"] = year_norm * weight_year
        except (ValueError, TypeError):
            pass
    
    # Score feature (normalize to 0-1 range; score is 1-10)
    score = anime.get("score")
    if score is not None:
        try:
            score_float = float(score)
            score_norm = max(0.0, min(1.0, score_float / 10.0))
            vec[f"score"] = score_norm * weight_score
        except (ValueError, TypeError):
            pass
    
    # Popularity feature (0-100 already)
    popularity = anime.get("popularity_score")
    if popularity is not None:
        try:
            pop_norm = max(0.0, min(1.0, float(popularity) / 100.0))
            vec[f"popularity"] = pop_norm * weight_popularity
        except (ValueError, TypeError):
            pass
    
    return vec


def compose_recommendation_score(
    content_similarity: float,
    popularity_score: float,
    opt_in_popularity: bool = True
) -> float:
    """Compose final recommendation score from content similarity and popularity.
    
    If user opts in: score = 0.7 * content_similarity + 0.3 * (popularity_score / 100)
    If user opts out: score = content_similarity
    
    Returns value in [0, 1].
    """
    content_sim = max(0.0, min(1.0, content_similarity))
    
    if opt_in_popularity:
        pop_norm = max(0.0, min(1.0, popularity_score / 100.0))
        return 0.7 * content_sim + 0.3 * pop_norm
    else:
        return content_sim


def recommend_anime(
    user_preferences: Dict,
    user_liked_anime: List[Dict],
    candidate_anime: List[Dict],
    top_n: int = 20,
    opt_in_popularity: bool = True,
    exclude_anime_ids: Optional[Set[int]] = None
) -> List[Dict]:
    """Generate top-N anime recommendations for a user.
    
    Algorithm:
    1. Build preference vector from user's stated interests (genres, studios, etc.)
    2. Build preference vector from user's liked anime (average of their vectors)
    3. Compute content similarity between user preference and each candidate anime
    4. Optionally blend with popularity score
    5. Sort and return top-N excluding already-liked anime
    
    Args:
        user_preferences: Dict with keys like 'genres', 'studios', 'prefer_recent', 'prefer_popular'
        user_liked_anime: List of anime dicts the user has already liked
        candidate_anime: List of all candidate anime to score
        top_n: Number of recommendations to return
        opt_in_popularity: Whether to include popularity in scoring
        exclude_anime_ids: Set of anime IDs to exclude from results
    
    Returns:
        List of dicts with keys: anime_id, title, score, genres, image_url, similarity, popularity_score
    """
    if exclude_anime_ids is None:
        exclude_anime_ids = set()

    # Exclude anime the user already liked
    for liked in (user_liked_anime or []):
        liked_id = liked.get("anime_id")
        if liked_id is not None:
            exclude_anime_ids.add(liked_id)
    
    # Build user preference vector
    pref_vec = {}
    
    # Add genres from stated preferences
    for genre in (user_preferences.get("genres") or []):
        if isinstance(genre, str) and genre.strip():
            key = f"genre:{genre}"
            pref_vec[key] = pref_vec.get(key, 0.0) + 1.0
    
    # Add studios from stated preferences
    for studio in (user_preferences.get("studios") or []):
        if isinstance(studio, str) and studio.strip():
            key = f"studio:{studio}"
            pref_vec[key] = pref_vec.get(key, 0.0) + 1.0
    
    # Blend in vectors from user's liked anime (cold-start: if no likes, use preferences only)
    if user_liked_anime:
        liked_vecs = [build_anime_vector(anime) for anime in user_liked_anime]
        # Average the vectors
        avg_vec = {}
        for vec in liked_vecs:
            for k, v in vec.items():
                avg_vec[k] = avg_vec.get(k, 0.0) + v
        for k in avg_vec:
            avg_vec[k] /= len(liked_vecs)
        # Merge with preference vector (true 50/50 weight on all keys)
        pref_vec = {k: v * 0.5 for k, v in pref_vec.items()}
        for k, v in avg_vec.items():
            pref_vec[k] = pref_vec.get(k, 0.0) + v * 0.5
    
    # Score all candidate anime
    scored = []
    for anime in candidate_anime:
        anime_id = anime.get("anime_id")
        if anime_id in exclude_anime_ids:
            continue
        
        # Build anime feature vector
        anime_vec = build_anime_vector(anime)
        
        # Compute content similarity
        content_sim = cosine_similarity(pref_vec, anime_vec)
        
        # Get popularity score (default 50 if missing)
        popularity = anime.get("popularity_score", 50.0)
        try:
            popularity = float(popularity)
        except (ValueError, TypeError):
            popularity = 50.0
        
        # Compose final score
        final_score = compose_recommendation_score(content_sim, popularity, opt_in_popularity)
        
        scored.append({
            "anime_id": anime_id,
            "title": anime.get("title"),
            "score": round(final_score, 4),
            "content_similarity": round(content_sim, 4),
            "popularity_score": round(popularity, 2),
            "genres": anime.get("genres", []),
            "image_url": anime.get("image_url"),
        })
    
    # Sort by score descending and return top-N
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
