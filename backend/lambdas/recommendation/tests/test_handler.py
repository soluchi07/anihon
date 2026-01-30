"""Unit tests for recommendation API handler."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import handler


def _make_event(method, user_id, body=None):
    return {
        "httpMethod": method,
        "pathParameters": {"userId": user_id},
        "body": json.dumps(body) if body is not None else None,
    }


def test_get_recommendations_empty():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.get_item.return_value = {}
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        event = _make_event("GET", "user1")
        resp = handler(event, None)
        body = json.loads(resp["body"])
        assert resp["statusCode"] == 200
        assert body["recommendations"] == []


def test_get_recommendations_cached():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.get_item.return_value = {"Item": {"recommendations": [{"anime_id": 1}]}}
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        event = _make_event("GET", "user1")
        resp = handler(event, None)
        body = json.loads(resp["body"])
        assert resp["statusCode"] == 200
        assert body["recommendations"] == [{"anime_id": 1}]


def test_post_recommendations_triggers_worker():
    with patch("boto3.client") as mock_client, patch.dict("os.environ", {"RECOMMENDATION_WORKER_FUNCTION": "worker-fn"}):
        mock_lambda = Mock()
        mock_client.return_value = mock_lambda

        event = _make_event("POST", "user1", {"opt_in_popularity": True, "top_n": 5})
        resp = handler(event, None)
        body = json.loads(resp["body"])

        assert resp["statusCode"] == 202
        assert body["status"] == "accepted"
        mock_lambda.invoke.assert_called_once()


def test_missing_user_id():
    event = {"httpMethod": "GET"}
    resp = handler(event, None)
    body = json.loads(resp["body"])
    assert resp["statusCode"] == 400
    assert body["status"] == "error"
