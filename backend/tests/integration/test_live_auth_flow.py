"""Integration tests for live auth/onboarding/recommendations.

These tests run against the deployed API Gateway. They are skipped unless
INTEGRATION_TESTS=1 and API_BASE is set.
"""
import json
import os
import time
import urllib.request

import pytest

API_BASE = os.environ.get("API_BASE")
RUN_INTEGRATION = os.environ.get("INTEGRATION_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not (RUN_INTEGRATION and API_BASE),
    reason="Set INTEGRATION_TESTS=1 and API_BASE to run live tests",
)


def _post(path, payload, token=None):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API_BASE}{path}", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body)


def _get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API_BASE}{path}", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body)


def test_auth_onboarding_recommendations_flow():
    email = f"test_{int(time.time())}@example.com"
    password = "TestPass123"

    status, signup_body = _post("/auth/signup", {"email": email, "password": password, "name": "Test User"})
    assert status == 200
    assert signup_body["status"] == "ok"
    user_id = signup_body["userId"]
    token = signup_body["idToken"]

    status, onboarding_body = _post(
        f"/onboarding/{user_id}",
        {"genres": ["Action"], "studios": ["MAPPA"], "opt_in_popularity": True},
        token=token,
    )
    assert status == 200
    assert onboarding_body["status"] == "ok"

    status, job_body = _post(
        f"/recommendations/{user_id}",
        {"opt_in_popularity": True, "top_n": 5},
        token=token,
    )
    assert status in (200, 202)
    assert job_body["status"] in ("accepted", "ok")

    status, recs_body = _get(f"/recommendations/{user_id}", token=token)
    assert status == 200
    assert "recommendations" in recs_body
