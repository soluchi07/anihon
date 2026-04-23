"""Unit tests for lists API handler."""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import handler


def _make_event(method, user_id="user1", body=None, query=None, list_key=None):
    path_params = {"userId": user_id}
    if list_key is not None:
        path_params["listKey"] = list_key
    return {
        "httpMethod": method,
        "pathParameters": path_params,
        "queryStringParameters": query,
        "body": json.dumps(body) if body is not None else None,
    }


def test_get_lists_grouped():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.query.return_value = {
        "Items": [
            {"anime_id": 1, "list_type": "watching", "list_key": "watching#1"},
            {"anime_id": 2, "list_type": "completed", "list_key": "completed#2"},
        ]
    }
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("GET"), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["status"] == "ok"
    assert len(body["lists"]["watching"]) == 1
    assert len(body["lists"]["completed"]) == 1


def test_post_add_list_item():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.query.return_value = {"Items": []}
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("POST", body={"anime_id": 25, "list_type": "watching"}), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["status"] == "ok"
    assert body["item"]["list_key"] == "watching#25"
    mock_table.put_item.assert_called_once()


def test_delete_list_item_decodes_key():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event("DELETE", list_key="watching%231"), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["deleted"]["list_key"] == "watching#1"
    mock_table.delete_item.assert_called_once_with(Key={"user_id": "user1", "list_key": "watching#1"})


def test_post_requires_fields():
    resp = handler(_make_event("POST", body={"anime_id": 1}), None)
    body = json.loads(resp["body"])
    assert resp["statusCode"] == 400
    assert body["status"] == "error"
