"""Recommendation worker (stub)

Triggered by CloudWatch Events or on-demand to compute and store top-20 recommendations in RecommendationCache table.
"""
import os
import logging

logger = logging.getLogger("recommendation_worker")
logging.basicConfig(level=logging.INFO)

CACHE_TABLE = os.environ.get("RECOMMENDATION_CACHE_TABLE", "RecommendationCache")


def handler(event, context):
    logger.info("Recommendation worker triggered (stub). Event: %s", event)
    # TODO: compute top-20 using algorithm and write to DynamoDB with TTL
    return {"status": "ok", "userId": event.get("userId", "unknown"), "recommendations": []}
