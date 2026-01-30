"""Recommendation API handler (stub)

API triggers should put a job or return existing cached recommendations.
"""
import os
import logging

logger = logging.getLogger("recommendation_api")
logging.basicConfig(level=logging.INFO)

CACHE_TABLE = os.environ.get("RECOMMENDATION_CACHE_TABLE", "RecommendationCache")


def handler(event, context):
    logger.info("Recommendation API invoked (stub). Event: %s", event)
    # TODO: validate user, trigger worker via CloudWatch/SQS, return job_id / 202
    return {"status": "accepted", "job_id": "stub-job-1"}
