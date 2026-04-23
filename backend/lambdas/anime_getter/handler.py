"""Anime getter handler

GET /anime/{animeId} - fetch a single anime by ID
GET /anime?genre=X   - list anime by genre (up to 50)
"""
import json
import logging
import os
from decimal import Decimal
from typing import Dict, List

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger("anime_getter")
logging.basicConfig(level=logging.INFO)

ANIME_TABLE = os.environ.get("ANIME_TABLE", "Anime")


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        n = float(obj)
        return int(n) if n == int(n) else n
    raise TypeError(f"Not serializable: {type(obj)}")


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=_decimal_default),
    }


def _get_path(event):
    return (event.get("resource") or event.get("path") or "").lower()


def _is_similar_request(event):
    path = _get_path(event)
    return path.endswith("/similar")


def _as_set(values):
    return {v for v in (values or []) if isinstance(v, str) and v.strip()}


def _similarity_score(base: Dict, candidate: Dict) -> float:
    base_genres = _as_set(base.get("genres"))
    cand_genres = _as_set(candidate.get("genres"))
    base_studios = _as_set(base.get("studios"))
    cand_studios = _as_set(candidate.get("studios"))

    genre_score = 0.0
    if base_genres and cand_genres:
        overlap = len(base_genres.intersection(cand_genres))
        genre_score = overlap / max(1, len(base_genres.union(cand_genres)))

    studio_score = 0.0
    if base_studios and cand_studios:
        overlap = len(base_studios.intersection(cand_studios))
        studio_score = overlap / max(1, len(base_studios.union(cand_studios)))

    base_score = float(base.get("score") or 0.0)
    cand_score = float(candidate.get("score") or 0.0)
    score_distance = abs(base_score - cand_score)
    score_proximity = max(0.0, 1.0 - (score_distance / 10.0))

    return (0.6 * genre_score) + (0.25 * studio_score) + (0.15 * score_proximity)


def _fetch_items_by_ids(dynamodb, anime_ids: List[int]):
    if not anime_ids:
        return []
    keys = [{"anime_id": anime_id} for anime_id in anime_ids[:100]]
    batch_response = dynamodb.batch_get_item(RequestItems={ANIME_TABLE: {"Keys": keys}})
    return batch_response.get("Responses", {}).get(ANIME_TABLE, [])


def _get_similar_anime(dynamodb, table, anime_id: int, limit: int = 12):
    base_result = table.get_item(Key={"anime_id": anime_id})
    base_anime = base_result.get("Item")
    if not base_anime:
        return None, []

    genre_candidates = set()
    for genre in _as_set(base_anime.get("genres")):
        resp = table.query(
            IndexName="genre-index",
            KeyConditionExpression=Key("genre").eq(genre),
            Limit=50,
        )
        for item in resp.get("Items", []):
            candidate_id = item.get("anime_id")
            if isinstance(candidate_id, int) and candidate_id != anime_id:
                genre_candidates.add(candidate_id)

    candidates = _fetch_items_by_ids(dynamodb, list(genre_candidates))
    ranked = []
    for candidate in candidates:
        sim = _similarity_score(base_anime, candidate)
        ranked.append((sim, candidate))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return base_anime, [item for _, item in ranked[:limit]]


def handler(event, context):
    logger.info("Anime getter invoked. Event: %s", event)

    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    anime_id = path_params.get("animeId")
    genre = query_params.get("genre")

    # GET /anime/{animeId}/similar
    if anime_id and _is_similar_request(event):
        try:
            anime_id_int = int(anime_id)
        except (ValueError, TypeError):
            return _response(400, {"status": "error", "error": "animeId must be a number"})
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(ANIME_TABLE)
            base_anime, similar = _get_similar_anime(dynamodb, table, anime_id_int)
            if not base_anime:
                return _response(404, {"status": "error", "error": "Anime not found"})
            return _response(200, {"status": "ok", "anime_id": anime_id_int, "similar_anime": similar})
        except ClientError as e:
            logger.error("DynamoDB error: %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    # GET /anime/{animeId}
    if anime_id:
        try:
            anime_id_int = int(anime_id)
        except (ValueError, TypeError):
            return _response(400, {"status": "error", "error": "animeId must be a number"})
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(ANIME_TABLE)
            result = table.get_item(Key={"anime_id": anime_id_int})
            item = result.get("Item")
            if not item:
                return _response(404, {"status": "error", "error": "Anime not found"})
            return _response(200, {"status": "ok", "anime": item})
        except ClientError as e:
            logger.error("DynamoDB error: %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    # GET /anime?genre=X
    if genre:
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(ANIME_TABLE)
            # genre-index is KEYS_ONLY; query returns {anime_id, genre} keys
            result = table.query(
                IndexName="genre-index",
                KeyConditionExpression=Key("genre").eq(genre),
                Limit=50,
            )
            keys = [{"anime_id": item["anime_id"]} for item in result.get("Items", [])]
            if not keys:
                return _response(200, {"status": "ok", "anime": []})
            # BatchGetItem to fetch full records
            batch_response = dynamodb.batch_get_item(
                RequestItems={ANIME_TABLE: {"Keys": keys}}
            )
            items = batch_response.get("Responses", {}).get(ANIME_TABLE, [])
            return _response(200, {"status": "ok", "anime": items})
        except ClientError as e:
            logger.error("DynamoDB error: %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    return _response(400, {"status": "error", "error": "Provide animeId path param or genre query param"})
