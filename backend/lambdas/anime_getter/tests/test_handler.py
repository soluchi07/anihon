"""Unit tests for anime getter API handler."""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import handler


def _make_event(path_params=None, query_params=None, path="/anime"):
    return {
        "httpMethod": "GET",
        "path": path,
        "pathParameters": path_params or {},
        "queryStringParameters": query_params,
    }


def test_get_anime_by_id_success():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.get_item.return_value = {"Item": {"anime_id": 1, "title": "One"}}
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        resp = handler(_make_event(path_params={"animeId": "1"}, path="/anime/1"), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["anime"]["title"] == "One"


def test_get_anime_by_genre_success():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.query.return_value = {"Items": [{"anime_id": 2}]}
    mock_dynamodb.Table.return_value = mock_table
    mock_dynamodb.batch_get_item.return_value = {
        "Responses": {"Anime": [{"anime_id": 2, "title": "Two"}]}
    }

    with patch("boto3.resource", return_value=mock_dynamodb), patch.dict("os.environ", {"ANIME_TABLE": "Anime"}):
        resp = handler(_make_event(query_params={"genre": "Action"}), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["status"] == "ok"
    assert len(body["anime"]) == 1


def test_get_similar_anime_success():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.get_item.return_value = {
        "Item": {"anime_id": 1, "title": "Base", "genres": ["Action"], "studios": ["MAPPA"], "score": 8.0}
    }
    mock_table.query.return_value = {"Items": [{"anime_id": 2}]}
    mock_dynamodb.Table.return_value = mock_table
    mock_dynamodb.batch_get_item.return_value = {
        "Responses": {
            "Anime": [{"anime_id": 2, "title": "Peer", "genres": ["Action"], "studios": ["MAPPA"], "score": 8.1}]
        }
    }

    with patch("boto3.resource", return_value=mock_dynamodb), patch.dict("os.environ", {"ANIME_TABLE": "Anime"}):
        resp = handler(_make_event(path_params={"animeId": "1"}, path="/anime/1/similar"), None)
        body = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert body["status"] == "ok"
    assert len(body["similar_anime"]) == 1
    assert body["similar_anime"][0]["anime_id"] == 2


def test_invalid_anime_id():
    resp = handler(_make_event(path_params={"animeId": "abc"}, path="/anime/abc"), None)
    body = json.loads(resp["body"])
    assert resp["statusCode"] == 400
    assert body["status"] == "error"
