"""Unit tests for auth API handler."""
import base64
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from handler import handler


def _make_event(path, body=None):
    return {
        "httpMethod": "POST",
        "path": path,
        "body": json.dumps(body) if body is not None else None,
    }


def _fake_id_token(sub="user-123", email="user@example.com", name="Test User"):
    payload = {
        "sub": sub,
        "email": email,
        "name": name,
    }
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    return f"header.{encoded_payload}.sig"


def test_missing_cognito_config():
    event = _make_event("/auth/login", {"email": "a@b.com", "password": "TestPass123"})
    with patch.dict(os.environ, {"COGNITO_USER_POOL_ID": "", "COGNITO_CLIENT_ID": ""}):
        resp = handler(event, None)
        body = json.loads(resp["body"])
        assert resp["statusCode"] == 500
        assert body["status"] == "error"


def test_signup_success():
    mock_client = Mock()
    mock_client.admin_initiate_auth.return_value = {
        "AuthenticationResult": {"IdToken": _fake_id_token()}
    }

    with patch("boto3.client", return_value=mock_client), patch.dict(
        os.environ, {"COGNITO_USER_POOL_ID": "pool", "COGNITO_CLIENT_ID": "client"}
    ):
        event = _make_event("/auth/signup", {"email": "a@b.com", "password": "TestPass123", "name": "Test"})
        resp = handler(event, None)
        body = json.loads(resp["body"])

        assert resp["statusCode"] == 200
        assert body["status"] == "ok"
        assert body["userId"] == "user-123"
        mock_client.sign_up.assert_called_once()
        mock_client.admin_confirm_sign_up.assert_called_once()
        mock_client.admin_initiate_auth.assert_called_once()


def test_login_success():
    mock_client = Mock()
    mock_client.admin_initiate_auth.return_value = {
        "AuthenticationResult": {"IdToken": _fake_id_token()}
    }

    with patch("boto3.client", return_value=mock_client), patch.dict(
        os.environ, {"COGNITO_USER_POOL_ID": "pool", "COGNITO_CLIENT_ID": "client"}
    ):
        event = _make_event("/auth/login", {"email": "a@b.com", "password": "TestPass123"})
        resp = handler(event, None)
        body = json.loads(resp["body"])

        assert resp["statusCode"] == 200
        assert body["status"] == "ok"
        assert body["userId"] == "user-123"
        mock_client.admin_initiate_auth.assert_called_once()


def test_missing_credentials():
    with patch.dict(os.environ, {"COGNITO_USER_POOL_ID": "pool", "COGNITO_CLIENT_ID": "client"}):
        event = _make_event("/auth/login", {"email": "a@b.com"})
        resp = handler(event, None)
        body = json.loads(resp["body"])

        assert resp["statusCode"] == 400
        assert body["status"] == "error"
