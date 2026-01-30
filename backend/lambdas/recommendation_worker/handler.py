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

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import sys
from pathlib import Path

# Ensure algorithm import works
sys.path.insert(0, str(Path(__file__).parent.parent / "recommendation"))
from algorithm import recommend_anime

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


def write_cache(table, user_id: str, recommendations: List[Dict], ttl_seconds: int):
    now = int(time.time())
    ttl = now + ttl_seconds
    cache_item = {
        "user_id": user_id,
        "created_at": now,
        "ttl": ttl,
        "recommendations": recommendations,
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
            "recommendations": recs,
            "cache_ttl": cache_item["ttl"],
        }

    except RecommendationWorkerError as e:
        logger.error("Recommendation worker error: %s", e)
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "error": str(e)}
