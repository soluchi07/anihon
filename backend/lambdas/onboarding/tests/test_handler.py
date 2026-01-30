"""Unit tests for onboarding API handler."""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import handler


def _make_event(user_id, body=None):
    return {
        "httpMethod": "POST",
        "pathParameters": {"userId": user_id},
        "body": json.dumps(body) if body is not None else None,
    }


def test_onboarding_missing_user_id():
    event = {"httpMethod": "POST"}
    resp = handler(event, None)
    body = json.loads(resp["body"])
    assert resp["statusCode"] == 400
    assert body["status"] == "error"


def test_onboarding_success():
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table

    with patch("boto3.resource", return_value=mock_dynamodb):
        event = _make_event("user123", {"genres": ["Action"], "studios": [], "opt_in_popularity": True})
        resp = handler(event, None)
        body = json.loads(resp["body"])

        assert resp["statusCode"] == 200
        assert body["status"] == "ok"
        assert body["user_id"] == "user123"
        mock_table.put_item.assert_called_once()
