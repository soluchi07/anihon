"""Anime getter handler

GET /anime/{animeId} - fetch a single anime by ID
GET /anime?genre=X   - list anime by genre (up to 50)
"""
import json
import logging
import os
from decimal import Decimal

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


def handler(event, context):
    logger.info("Anime getter invoked. Event: %s", event)
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(ANIME_TABLE)

    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    anime_id = path_params.get("animeId")
    genre = query_params.get("genre")

    # GET /anime/{animeId}
    if anime_id:
        try:
            anime_id_int = int(anime_id)
        except (ValueError, TypeError):
            return _response(400, {"status": "error", "error": "animeId must be a number"})
        try:
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
