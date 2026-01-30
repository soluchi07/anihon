"""Unit tests for recommendation_worker handler."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import handler


@pytest.fixture
def sample_event():
    return {
        "user_id": "user123",
        "opt_in_popularity": True,
        "top_n": 2,
        "user_preferences": {"genres": ["Action"], "studios": []},
        "user_liked_anime": [],
        "candidate_anime": [
            {
                "anime_id": 1,
                "title": "Action Hero",
                "genres": ["Action"],
                "studios": ["Studio A"],
                "score": 8.0,
                "popularity_score": 80.0,
                "image_url": "http://example.com/1.jpg",
            },
            {
                "anime_id": 2,
                "title": "Drama Love",
                "genres": ["Drama"],
                "studios": ["Studio B"],
                "score": 7.0,
                "popularity_score": 60.0,
                "image_url": "http://example.com/2.jpg",
            },
        ],
    }


def test_handler_missing_user_id():
    result = handler({}, None)
    assert result["status"] == "error"
    assert "user_id" in result["error"]


def test_handler_with_event_data(sample_event):
    # Mock DynamoDB
    mock_dynamodb = Mock()
    mock_cache_table = Mock()
    mock_dynamodb.Table.return_value = mock_cache_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        result = handler(sample_event, None)
        assert result["status"] == "ok"
        assert result["user_id"] == "user123"
        assert len(result["recommendations"]) <= 2
        assert "cache_ttl" in result
        mock_cache_table.put_item.assert_called_once()


def test_handler_with_dynamo_fetch(sample_event):
    # Simulate DynamoDB tables
    mock_dynamodb = Mock()
    mock_cache_table = Mock()
    mock_users_table = Mock()
    mock_interactions_table = Mock()
    mock_anime_table = Mock()

    # Users table returns preferences
    mock_users_table.get_item.return_value = {
        "Item": {"preferences": {"genres": ["Action"], "studios": []}}
    }

    # Interactions table returns empty list
    mock_interactions_table.query.return_value = {"Items": []}

    # Anime table scan returns candidate items
    mock_anime_table.scan.return_value = {"Items": sample_event["candidate_anime"]}

    # Table selection logic in handler
    def table_side_effect(name):
        return {
            "RecommendationCache": mock_cache_table,
            "Users": mock_users_table,
            "UserAnimeInteractions": mock_interactions_table,
            "Anime": mock_anime_table,
        }[name]

    mock_dynamodb.Table.side_effect = table_side_effect

    with patch("boto3.resource", return_value=mock_dynamodb):
        # Remove embedded data so it fetches from DynamoDB
        event = {
            "user_id": "user123",
            "opt_in_popularity": True,
            "top_n": 2,
        }
        result = handler(event, None)

        assert result["status"] == "ok"
        assert len(result["recommendations"]) <= 2
        mock_users_table.get_item.assert_called_once()
        mock_interactions_table.query.assert_called_once()
        mock_anime_table.scan.assert_called_once()
        mock_cache_table.put_item.assert_called_once()
