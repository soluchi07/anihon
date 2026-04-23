"""Unit tests for onboarding API handler."""
import json
import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

_HANDLER_PATH = Path(__file__).parent.parent / "handler.py"
_SPEC = importlib.util.spec_from_file_location("onboarding_handler", _HANDLER_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MODULE)
handler = _MODULE.handler


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
