"""Data ingest Lambda (stub)

Reads cleaned JSONL from S3 and batch writes into Anime DynamoDB table.
"""
import os
import logging

logger = logging.getLogger("data_ingest")
logging.basicConfig(level=logging.INFO)

TABLE_NAME = os.environ.get("ANIME_TABLE", "Anime")


def handler(event, context):
    logger.info("Data ingest triggered (stub). Event: %s", event)
    # TODO: implement reading from S3 and batch writing to DynamoDB
    return {"status": "stub", "items_written": 0}
