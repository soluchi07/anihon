"""Recommendation API handler

GET /recommendations/{userId}: returns cached recommendations (if available)
POST /recommendations/{userId}: triggers async recommendation worker
"""
import os
import json
import time
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("recommendation_api")
logging.basicConfig(level=logging.INFO)

CACHE_TABLE = os.environ.get("RECOMMENDATION_CACHE_TABLE", "RecommendationCache")
DEFAULT_TOP_N = int(os.environ.get("TOP_N", "20"))


def _get_http_method(event):
    return event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")


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


def _get_cached_recommendations(user_id):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(CACHE_TABLE) # type: ignore
    resp = table.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    if not item:
        return None
    ttl = item.get("ttl", 0)
    if ttl and int(ttl) < int(time.time()):
        return None
    return item.get("recommendations", [])


def _trigger_worker(user_id, opt_in_popularity, top_n):
    worker_function = os.environ.get("RECOMMENDATION_WORKER_FUNCTION", "")
    payload = {
        "user_id": user_id,
        "opt_in_popularity": opt_in_popularity,
        "top_n": top_n,
    }

    if worker_function:
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName=worker_function,
            InvocationType="Event",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        return {"job_id": f"worker:{worker_function}"}

    # Fallback: direct invocation for local testing
    try:
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "recommendation_worker"))
        from handler import handler as worker_handler
        worker_handler(payload, None)
        return {"job_id": "local-worker"}
    except Exception as e:
        logger.warning("Failed to call worker directly: %s", e)
        return {"job_id": "unknown"}


def handler(event, context):
    logger.info("Recommendation API invoked. Event: %s", event)
    method = _get_http_method(event).upper()
    user_id = _get_user_id(event)

    if not user_id:
        return _response(400, {"status": "error", "error": "user_id is required"})

    if method == "GET":
        try:
            recs = _get_cached_recommendations(user_id)
            if recs is None:
                return _response(200, {"status": "ok", "recommendations": []})
            return _response(200, {"status": "ok", "recommendations": recs})
        except ClientError as e:
            return _response(500, {"status": "error", "error": str(e)})

    if method == "POST":
        body = _parse_body(event)
        opt_in_popularity = bool(body.get("opt_in_popularity", True))
        top_n = int(body.get("top_n", DEFAULT_TOP_N))
        job = _trigger_worker(user_id, opt_in_popularity, top_n)
        return _response(202, {"status": "accepted", "job_id": job.get("job_id")})

    return _response(405, {"status": "error", "error": f"Method {method} not allowed"})
