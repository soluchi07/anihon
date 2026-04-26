"""Lists API handler.

GET    /lists/{userId}                - list all user lists (grouped) or filter by list_type
POST   /lists/{userId}                - add/update anime in a list
DELETE /lists/{userId}/{listKey}      - remove anime from a list
"""
import json
import logging
import os
import time
from decimal import Decimal
from urllib.parse import unquote

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger("lists")
logging.basicConfig(level=logging.INFO)

LISTS_TABLE = os.environ.get("LISTS_TABLE", "UserAnimeLists")
DEFAULT_LISTS = ["watching", "completed", "plan_to_watch", "on_hold"]


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


def _get_list_key(event):
    path_params = event.get("pathParameters") or {}
    raw = path_params.get("listKey") or path_params.get("list_id") or path_params.get("compositeKey")
    if not raw:
        return None
    return unquote(raw)


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


def _build_lists_payload(items):
    grouped = {k: [] for k in DEFAULT_LISTS}
    for item in items:
        list_type = item.get("list_type")
        if list_type not in grouped:
            grouped[list_type] = []
        grouped[list_type].append(item)
    return grouped


def handler(event, context):
    logger.info("Lists handler invoked. Event: %s", event)

    method = (event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")).upper()
    user_id = _get_user_id(event)
    if not user_id:
        return _response(400, {"status": "error", "error": "user_id is required"})

    if method == "GET":
        list_type = (event.get("queryStringParameters") or {}).get("list_type")
        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(LISTS_TABLE)
            resp = table.query(KeyConditionExpression=Key("user_id").eq(user_id))
            items = resp.get("Items", [])
            if list_type:
                filtered = [item for item in items if item.get("list_type") == list_type]
                return _response(200, {"status": "ok", "list_type": list_type, "items": filtered})
            return _response(200, {"status": "ok", "lists": _build_lists_payload(items)})
        except ClientError as e:
            logger.error("DynamoDB error (GET lists): %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    if method == "POST":
        body = _parse_body(event)
        anime_id = body.get("anime_id")
        list_type = body.get("list_type")
        if anime_id is None or not list_type:
            return _response(400, {"status": "error", "error": "anime_id and list_type are required"})

        try:
            anime_id = int(anime_id)
        except (ValueError, TypeError):
            return _response(400, {"status": "error", "error": "anime_id must be a number"})

        list_key = f"{list_type}#{anime_id}"

        item = {
            "user_id": user_id,
            "list_key": list_key,
            "anime_id": anime_id,
            "list_type": str(list_type),
            "updated_at": int(time.time()),
        }

        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(LISTS_TABLE)
            existing = table.query(KeyConditionExpression=Key("user_id").eq(user_id)).get("Items", [])
            for row in existing:
                if row.get("anime_id") == anime_id and row.get("list_key") != list_key:
                    table.delete_item(Key={"user_id": user_id, "list_key": row["list_key"]})

            table.put_item(Item=item)
            return _response(200, {"status": "ok", "item": item})
        except ClientError as e:
            logger.error("DynamoDB error (POST list item): %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    if method == "DELETE":
        list_key = _get_list_key(event)
        if not list_key:
            return _response(400, {"status": "error", "error": "listKey is required"})

        try:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(LISTS_TABLE)
            table.delete_item(Key={"user_id": user_id, "list_key": list_key})
            return _response(200, {"status": "ok", "deleted": {"user_id": user_id, "list_key": list_key}})
        except ClientError as e:
            logger.error("DynamoDB error (DELETE list item): %s", e)
            return _response(500, {"status": "error", "error": str(e)})

    return _response(405, {"status": "error", "error": f"Method {method} not allowed"})
