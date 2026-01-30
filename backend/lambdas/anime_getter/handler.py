"""Anime getter handler (stub)

GET /anime/{animeId}
GET /anime?genre=...
"""
import os
import logging

logger = logging.getLogger("anime_getter")
logging.basicConfig(level=logging.INFO)

ANIME_TABLE = os.environ.get("ANIME_TABLE", "Anime")


def handler(event, context):
    logger.info("Anime getter invoked (stub). Event: %s", event)
    # TODO: implement GetItem and Query logic against DynamoDB
    return {"status": "ok", "anime": None}
