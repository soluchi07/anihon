"""Interactions handler (stub)

Handles like/rate/list operations by users.
"""
import os
import logging

logger = logging.getLogger("interactions")
logging.basicConfig(level=logging.INFO)

INTERACTIONS_TABLE = os.environ.get("INTERACTIONS_TABLE", "UserAnimeInteractions")


def handler(event, context):
    logger.info("Interactions handler invoked (stub). Event: %s", event)
    # TODO: parse event and update interactions table
    return {"status": "ok"}
