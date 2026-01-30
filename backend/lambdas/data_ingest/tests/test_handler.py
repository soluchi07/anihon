"""Unit tests for data_ingest handler."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import (
    read_jsonl_from_s3,
    batch_write_to_dynamodb,
    handler,
    DataIngestError,
)


@pytest.fixture
def sample_jsonl():
    """Sample cleaned JSONL records."""
    return [
        {
            "anime_id": 1,
            "title": "Test Anime 1",
            "alternate_titles": ["Test 1", "Tesuto 1"],
            "genres": ["Action", "Adventure"],
            "studios": ["Studio A"],
            "synopsis": "A great anime",
            "episodes": 12,
            "year": 2024,
            "type": "TV",
            "rating": "PG-13",
            "score": 8.5,
            "popularity": 100,
            "popularity_score": 95.0,
            "favorites": 5000,
            "image_url": "https://example.com/1.jpg",
        },
        {
            "anime_id": 2,
            "title": "Test Anime 2",
            "alternate_titles": [],
            "genres": ["Drama"],
            "studios": [],
            "synopsis": None,
            "episodes": None,
            "year": 2023,
            "type": "Movie",
            "rating": "R",
            "score": 5.0,  # null default
            "popularity": 5000,
            "popularity_score": 10.0,
            "favorites": 100,
            "image_url": None,
        },
    ]


def test_read_jsonl_from_s3_success(sample_jsonl):
    """Test reading JSONL from S3."""
    mock_s3 = Mock()
    mock_body = MagicMock()
    mock_body.iter_lines.return_value = [json.dumps(item).encode() for item in sample_jsonl]
    mock_s3.get_object.return_value = {"Body": mock_body}

    with patch("boto3.client", return_value=mock_s3):
        records = list(read_jsonl_from_s3("test-bucket", "test-key"))
        assert len(records) == 2
        assert records[0]["anime_id"] == 1
        assert records[1]["anime_id"] == 2


def test_read_jsonl_from_s3_malformed_line(sample_jsonl):
    """Test handling of malformed JSON lines."""
    mock_s3 = Mock()
    mock_body = MagicMock()
    lines = [
        json.dumps(sample_jsonl[0]).encode(),
        b"not valid json",
        json.dumps(sample_jsonl[1]).encode(),
    ]
    mock_body.iter_lines.return_value = lines
    mock_s3.get_object.return_value = {"Body": mock_body}

    with patch("boto3.client", return_value=mock_s3):
        records = list(read_jsonl_from_s3("test-bucket", "test-key"))
        # Should skip malformed line
        assert len(records) == 2


def test_read_jsonl_from_s3_s3_error():
    """Test S3 client error handling."""
    from botocore.exceptions import ClientError
    mock_s3 = Mock()
    mock_s3.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey"}}, "GetObject"
    )

    with patch("boto3.client", return_value=mock_s3):
        with pytest.raises(DataIngestError):
            list(read_jsonl_from_s3("test-bucket", "nonexistent-key"))


def test_batch_write_to_dynamodb_success(sample_jsonl):
    """Test batch write to DynamoDB."""
    mock_table = Mock()
    mock_writer = MagicMock()
    mock_table.batch_writer.return_value.__enter__.return_value = mock_writer

    written, failed = batch_write_to_dynamodb(mock_table, sample_jsonl)
    assert written == 2
    assert failed == 0
    assert mock_writer.put_item.call_count == 2


def test_batch_write_to_dynamodb_partial_failure(sample_jsonl):
    """Test batch write with partial failures."""
    mock_table = Mock()
    mock_writer = MagicMock()

    # Simulate failure on second item
    def put_item_side_effect(**kwargs):
        item = kwargs.get("Item")
        if item and item.get("anime_id") == 2:
            raise Exception("DynamoDB write failed")

    mock_writer.put_item.side_effect = put_item_side_effect
    mock_table.batch_writer.return_value.__enter__.return_value = mock_writer

    written, failed = batch_write_to_dynamodb(mock_table, sample_jsonl)
    assert written == 1
    assert failed == 1


def test_handler_success(sample_jsonl):
    """Test handler with valid event."""
    mock_s3 = Mock()
    mock_body = MagicMock()
    mock_body.iter_lines.return_value = [json.dumps(item).encode() for item in sample_jsonl]
    mock_s3.get_object.return_value = {"Body": mock_body}

    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_writer = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_table.batch_writer.return_value.__enter__.return_value = mock_writer

    with patch("boto3.client", return_value=mock_s3), patch(
        "boto3.resource", return_value=mock_dynamodb
    ):
        event = {"bucket": "test-bucket", "key": "test-key.jsonl"}
        result = handler(event, None)

        assert result["status"] == "ok"
        assert result["items_written"] == 2
        assert result["items_failed"] == 0
        assert result["bucket"] == "test-bucket"


def test_handler_missing_bucket():
    """Test handler with missing bucket."""
    result = handler({}, None)
    assert result["status"] == "error"
    assert "bucket" in result["error"]


def test_handler_s3_error(sample_jsonl):
    """Test handler with S3 error."""
    from botocore.exceptions import ClientError
    mock_s3 = Mock()
    mock_s3.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchBucket"}}, "GetObject"
    )

    with patch("boto3.client", return_value=mock_s3):
        event = {"bucket": "nonexistent-bucket", "key": "test-key.jsonl"}
        result = handler(event, None)

        assert result["status"] == "error"
        assert "Failed to get S3 object" in result["error"]
