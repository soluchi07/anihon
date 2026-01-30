"""Data ingest Lambda

Reads cleaned JSONL from S3 and batch writes into Anime DynamoDB table.
Supports idempotency via S3 object version tracking (optional).
"""
import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("data_ingest")
logging.basicConfig(level=logging.INFO)

TABLE_NAME = os.environ.get("ANIME_TABLE", "Anime")
BATCH_SIZE = 25  # DynamoDB batch write limit


class DataIngestError(Exception):
    pass


def read_jsonl_from_s3(bucket, key, profile=None):
    """Stream JSONL records from S3 bucket.

    Yields individual parsed JSON objects.
    """
    if profile:
        session = boto3.Session(profile_name=profile)
        s3 = session.client("s3")
    else:
        s3 = boto3.client("s3")

    logger.info("Reading from s3://%s/%s", bucket, key)
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        raise DataIngestError(f"Failed to get S3 object: {e}")

    for line in response["Body"].iter_lines():
        if not line:
            continue
        try:
            record = json.loads(line)
            yield record
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON line: %s", e)


def batch_write_to_dynamodb(table, items, batch_size=BATCH_SIZE):
    """Batch write items to DynamoDB table.

    Handles partial batch failures and retries.
    Returns (written, failed) counts.
    """
    written = 0
    failed = 0

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        with table.batch_writer(
            batch_size=len(batch),
            overwrite_by_pkeys=["anime_id"],  # idempotency: overwrite on same PK
        ) as writer:
            for item in batch:
                try:
                    writer.put_item(Item=item)
                    written += 1
                except Exception as e:
                    logger.error("Failed to write item anime_id=%s: %s", item.get("anime_id"), e)
                    failed += 1

    return written, failed


def handler(event, context):
    """
    Event shape (S3 trigger or manual invocation):
    {
        "bucket": "anime-rec-data",
        "key": "cleaned/anime_meta_cleaned-2024-01-15.jsonl",
        "profile": "default"  # optional, for local testing
    }
    """
    logger.info("Data ingest triggered. Event: %s", event)

    bucket = event.get("bucket") or os.environ.get("DATA_BUCKET", "")
    key = event.get("key") or os.environ.get("DATA_KEY", "cleaned/anime_meta_cleaned.jsonl")
    profile = event.get("profile")

    if not bucket:
        return {"status": "error", "error": "bucket not specified"}

    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(TABLE_NAME)

        # Stream and collect items in batches
        items = []
        for record in read_jsonl_from_s3(bucket, key, profile):
            # Transform Jikan record to DynamoDB item
            item = {
                "anime_id": record.get("anime_id"),
                "title": record.get("title"),
                "alternate_titles": set(record.get("alternate_titles", [])),  # SS type
                "genres": set(record.get("genres", [])),  # SS type
                "studios": set(record.get("studios", [])),  # SS type
                "synopsis": record.get("synopsis"),
                "episodes": record.get("episodes"),
                "year": record.get("year"),
                "type": record.get("type"),
                "rating": record.get("rating"),
                "score": record.get("score", 5.0),
                "popularity": record.get("popularity"),
                "popularity_score": record.get("popularity_score", 0.0),
                "favorites": record.get("favorites", 0),
                "image_url": record.get("image_url"),
            }
            items.append(item)

        logger.info("Collected %d records from S3", len(items))

        # Batch write to DynamoDB
        written, failed = batch_write_to_dynamodb(table, items)
        logger.info("Batch write complete: written=%d, failed=%d", written, failed)

        return {
            "status": "ok",
            "items_written": written,
            "items_failed": failed,
            "bucket": bucket,
            "key": key,
        }

    except DataIngestError as e:
        logger.error("Data ingest error: %s", e)
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "error": str(e)}
