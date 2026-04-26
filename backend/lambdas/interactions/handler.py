"""Interactions handler

POST /interactions/{userId} - like or rate an anime
  body: { "anime_id": 123, "liked": true, "rating": 8 }
GET  /interactions/{userId} - list a user's interactions
"""
import json
import logging
import os
import time
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger("interactions")
logging.basicConfig(level=logging.INFO)

INTERACTIONS_TABLE = os.environ.get("INTERACTIONS_TABLE", "UserAnimeInteractions")


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        n = float(obj)
        return int(n) if n == int(n) else n
    if isinstance(obj, set):
        return list(obj)
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


def _get_user_id(event):
    if event.get("pathParameters"):
        return event["pathParameters"].get("userId") or event["pathParameters"].get("user_id")
    return None


def _parse_body(event):
    body = event.get("body")
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except Exception:
        return {}


def handler(event, context):
    logger.info("Interactions handler invoked. Event: %s", event)
    method = event.get("httpMethod", "GET")
    user_id = _get_user_id(event)
    if not user_id:
        return _response(400, {"status": "error", "error": "user_id is required"})

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(INTERACTIONS_TABLE)

    if method == "POST":
        body = _parse_body(event)
        anime_id = body.get("anime_id")
        if anime_id is None:
            return _response(400, {"status": "error", "error": "anime_id is required"})
        try:
            anime_id = int(anime_id)
        except (ValueError, TypeError):
            return _response(400, {"status": "error", "error": "anime_id must be a number"})

        item = {
            "user_id": user_id,
            "anime_id": anime_id,
            "liked": bool(body.get("liked", True)),
            "updated_at": int(time.time()),
        }
        if "rating" in body:
            try:
                rating = int(body["rating"])
                if 1 <= rating <= 10:
                    item["rating"] = rating
            except (ValueError, TypeError):
                pass

        try:
            table.put_item(Item=item)
            return _response(200, {"status": "ok", "interaction": item})
        except ClientError as e:
            logger.error("DynamoDB error: %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    # GET
    try:
        result = table.query(
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        return _response(200, {"status": "ok", "interactions": result.get("Items", [])})
    except ClientError as e:
        logger.error("DynamoDB error: %s", e)
        return _response(500, {"status": "error", "error": str(e)})
