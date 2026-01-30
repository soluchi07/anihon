"""Onboarding API handler

POST /onboarding/{userId}
Stores user preferences in Users table.
"""
import os
import json
import logging
import time
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("onboarding_api")
logging.basicConfig(level=logging.INFO)

USERS_TABLE = os.environ.get("USERS_TABLE", "Users")


def _get_user_id(event):
    if event.get("pathParameters"):
        return event["pathParameters"].get("userId") or event["pathParameters"].get("user_id")
    if event.get("queryStringParameters"):
        return event["queryStringParameters"].get("userId") or event["queryStringParameters"].get("user_id")
    return event.get("user_id") or event.get("userId")


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


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    logger.info("Onboarding API invoked. Event: %s", event)
    user_id = _get_user_id(event)
    if not user_id:
        return _response(400, {"status": "error", "error": "user_id is required"})

    body = _parse_body(event)
    preferences = {
        "genres": body.get("genres", []),
        "studios": body.get("studios", []),
        "opt_in_popularity": bool(body.get("opt_in_popularity", True)),
    }

    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(USERS_TABLE)
        table.put_item(
            Item={
                "user_id": user_id,
                "preferences": preferences,
                "updated_at": int(time.time()),
            }
        )
        return _response(200, {"status": "ok", "user_id": user_id, "preferences": preferences})
    except ClientError as e:
        return _response(500, {"status": "error", "error": str(e)})
