"""Recommendation worker

Triggered by CloudWatch Events or on-demand to compute and store top-N recommendations in RecommendationCache table.

Event shape (preferred):
{
  "user_id": "<user-id>",
  "opt_in_popularity": true,
  "top_n": 20
}

Optional for local testing:
{
  "user_id": "<user-id>",
  "user_preferences": {"genres": [...], "studios": [...]},
  "user_liked_anime": [ {anime...}, ... ],
  "candidate_anime": [ {anime...}, ... ]
}
"""
import os
import json
import time
import logging
from typing import Dict, List
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import sys
from pathlib import Path

# Ensure algorithm import works (local and Lambda)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "recommendation"))
    from algorithm import recommend_anime
except Exception:
    # Fallback: minimal local implementation to avoid import errors in Lambda
    def _normalize_vector(vec):
        import math
        mag = math.sqrt(sum(v * v for v in vec.values()))
        if mag == 0:
            return vec
        return {k: v / mag for k, v in vec.items()}

    def _cosine_similarity(vec_a, vec_b):
        if not vec_a or not vec_b:
            return 0.0
        vec_a = _normalize_vector(vec_a)
        vec_b = _normalize_vector(vec_b)
        dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in vec_a)
        return max(0.0, min(1.0, dot))

    def _build_anime_vector(anime):
        vec = {}
        for g in (anime.get("genres") or []):
            if isinstance(g, str) and g.strip():
                vec[f"genre:{g}"] = vec.get(f"genre:{g}", 0.0) + 1.0
        for s in (anime.get("studios") or []):
            if isinstance(s, str) and s.strip():
                vec[f"studio:{s}"] = vec.get(f"studio:{s}", 0.0) + 0.5
        score = anime.get("score")
        if score is not None:
            try:
                vec["score"] = min(1.0, float(score) / 10.0)
            except Exception:
                pass
        pop = anime.get("popularity_score")
        if pop is not None:
            try:
                vec["popularity"] = min(1.0, float(pop) / 100.0)
            except Exception:
                pass
        return vec

    def _compose_score(content_sim, popularity_score, opt_in_popularity=True):
        if opt_in_popularity:
            return 0.7 * content_sim + 0.3 * (float(popularity_score) / 100.0)
        return content_sim

    def recommend_anime(user_preferences, user_liked_anime, candidate_anime, top_n=20, opt_in_popularity=True, exclude_anime_ids=None):
        if exclude_anime_ids is None:
            exclude_anime_ids = set()
        for liked in (user_liked_anime or []):
            liked_id = liked.get("anime_id")
            if liked_id is not None:
                exclude_anime_ids.add(liked_id)

        pref_vec = {}
        for g in (user_preferences.get("genres") or []):
            pref_vec[f"genre:{g}"] = pref_vec.get(f"genre:{g}", 0.0) + 1.0
        for s in (user_preferences.get("studios") or []):
            pref_vec[f"studio:{s}"] = pref_vec.get(f"studio:{s}", 0.0) + 1.0

        scored = []
        for anime in candidate_anime:
            if anime.get("anime_id") in exclude_anime_ids:
                continue
            vec = _build_anime_vector(anime)
            sim = _cosine_similarity(pref_vec, vec)
            pop = anime.get("popularity_score", 50.0)
            score = _compose_score(sim, pop, opt_in_popularity)
            scored.append({
                "anime_id": anime.get("anime_id"),
                "title": anime.get("title"),
                "score": round(score, 4),
                "content_similarity": round(sim, 4),
                "popularity_score": round(float(pop), 2),
                "genres": anime.get("genres", []),
                "image_url": anime.get("image_url"),
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]

logger = logging.getLogger("recommendation_worker")
logging.basicConfig(level=logging.INFO)

USERS_TABLE = os.environ.get("USERS_TABLE", "Users")
INTERACTIONS_TABLE = os.environ.get("INTERACTIONS_TABLE", "UserAnimeInteractions")
ANIME_TABLE = os.environ.get("ANIME_TABLE", "Anime")
CACHE_TABLE = os.environ.get("RECOMMENDATION_CACHE_TABLE", "RecommendationCache")
DEFAULT_TOP_N = int(os.environ.get("TOP_N", "20"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", str(24 * 3600)))


class RecommendationWorkerError(Exception):
    pass


def get_user_preferences(table, user_id: str) -> Dict:
    try:
        resp = table.get_item(Key={"user_id": user_id})
        item = resp.get("Item", {})
        return item.get("preferences", {}) or {}
    except ClientError as e:
        raise RecommendationWorkerError(f"Failed to get user preferences: {e}")


def get_user_liked_anime(table, user_id: str) -> List[Dict]:
    """Fetch liked anime items from interactions table.
    Expects items where `liked` == True.
    """
    try:
        resp = table.query(
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        items = resp.get("Items", [])
        liked = [item for item in items if item.get("liked") is True]
        return liked
    except ClientError as e:
        raise RecommendationWorkerError(f"Failed to get user interactions: {e}")


def fetch_candidate_anime(table, limit: int = 200) -> List[Dict]:
    """Fetch candidate anime items. Uses scan with limit for MVP.
    In production, use indexed queries or cached candidate pools.
    """
    items = []
    scan_kwargs = {"Limit": limit}

    while True:
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp or len(items) >= limit:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return items[:limit]


def _to_dynamodb_safe(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, dict):
        return {k: _to_dynamodb_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_dynamodb_safe(v) for v in obj]
    return obj


def _to_json_safe(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_safe(v) for v in obj]
    return obj


def write_cache(table, user_id: str, recommendations: List[Dict], ttl_seconds: int):
    now = int(time.time())
    ttl = now + ttl_seconds
    cache_item = {
        "user_id": user_id,
        "created_at": now,
        "ttl": ttl,
        "recommendations": _to_dynamodb_safe(recommendations),
    }
    table.put_item(Item=cache_item)
    return cache_item


def handler(event, context):
    logger.info("Recommendation worker triggered. Event: %s", event)

    user_id = event.get("user_id") or event.get("userId")
    if not user_id:
        return {"status": "error", "error": "user_id is required"}

    top_n = int(event.get("top_n") or DEFAULT_TOP_N)
    opt_in_popularity = bool(event.get("opt_in_popularity", True))

    try:
        # Prefer event-provided data (for local testing)
        user_prefs = event.get("user_preferences")
        user_liked = event.get("user_liked_anime")
        candidates = event.get("candidate_anime")

        dynamodb = boto3.resource("dynamodb")
        cache_table = dynamodb.Table(CACHE_TABLE)

        if user_prefs is None or user_liked is None or candidates is None:
            users_table = dynamodb.Table(USERS_TABLE)
            interactions_table = dynamodb.Table(INTERACTIONS_TABLE)
            anime_table = dynamodb.Table(ANIME_TABLE)

            if user_prefs is None:
                user_prefs = get_user_preferences(users_table, user_id)
            if user_liked is None:
                user_liked = get_user_liked_anime(interactions_table, user_id)
            if candidates is None:
                candidates = fetch_candidate_anime(anime_table, limit=500)

        # Compute recommendations
        recs = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=user_liked,
            candidate_anime=candidates,
            top_n=top_n,
            opt_in_popularity=opt_in_popularity,
        )

        # Write to cache with TTL
        cache_item = write_cache(cache_table, user_id, recs, CACHE_TTL_SECONDS)

        return {
            "status": "ok",
            "user_id": user_id,
            "recommendations": _to_json_safe(recs),
            "cache_ttl": cache_item["ttl"],
        }

    except RecommendationWorkerError as e:
        logger.error("Recommendation worker error: %s", e)
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "error": str(e)}
