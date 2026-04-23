"""Unit tests for interactions API handler."""
import json
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

_HANDLER_PATH = Path(__file__).parent.parent / "handler.py"
_SPEC = importlib.util.spec_from_file_location("interactions_handler", _HANDLER_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MODULE)
handler = _MODULE.handler


def _make_event(method, user_id="user1", body=None):
    return {
        "httpMethod": method,
        "pathParameters": {"userId": user_id},
        "body": json.dumps(body) if body is not None else None,
    }


def test_post_success_with_rating():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("POST", body={"anime_id": 12, "liked": True, "rating": 9}), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["status"] == "ok"
    assert body["interaction"]["anime_id"] == 12
    assert body["interaction"]["rating"] == 9
    mock_table.put_item.assert_called_once()


def test_post_rejects_invalid_anime_id():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("POST", body={"anime_id": "abc"}), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 400
    assert body["status"] == "error"
    assert "anime_id must be a number" in body["error"]


def test_post_ignores_out_of_range_rating():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("POST", body={"anime_id": 42, "rating": 99}), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert "rating" not in body["interaction"]


def test_get_returns_user_interactions():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.query.return_value = {"Items": [{"anime_id": 1, "liked": True}]}
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("GET"), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["status"] == "ok"
    assert len(body["interactions"]) == 1


def test_dynamodb_error_returns_500():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.query.side_effect = ClientError({"Error": {"Code": "InternalError"}}, "Query")
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("GET"), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 500
    assert body["status"] == "error"
