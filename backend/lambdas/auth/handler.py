"""Authentication handler

POST /auth/signup
POST /auth/login

Uses Cognito User Pool to create and authenticate users.
"""
import os
import json
import logging
import base64

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("auth")
logging.basicConfig(level=logging.INFO)

COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "")


def _parse_body(event):
    body = event.get("body")
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except Exception:
        return {}


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _get_path(event):
    return event.get("resource") or event.get("path") or ""


def _decode_id_token(id_token):
    try:
        parts = id_token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        # Add padding for base64 decoding
        padding = "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode("utf-8"))
    except Exception as exc:
        logger.warning("Failed to decode id token: %s", exc)
        return {}


def _signup(client, email, password, name):
    client.sign_up(
        ClientId=COGNITO_CLIENT_ID,
        Username=email,
        Password=password,
        UserAttributes=[
            {"Name": "email", "Value": email},
            {"Name": "name", "Value": name or ""},
        ],
    )
    # Auto-confirm for MVP
    client.admin_confirm_sign_up(UserPoolId=COGNITO_USER_POOL_ID, Username=email)

    auth = client.admin_initiate_auth(
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": email,
            "PASSWORD": password,
        },
    )
    return auth.get("AuthenticationResult", {})


def _login(client, email, password):
    auth = client.admin_initiate_auth(
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": email,
            "PASSWORD": password,
        },
    )
    return auth.get("AuthenticationResult", {})


def handler(event, context):
    logger.info("Auth handler invoked. Event: %s", event)

    if not COGNITO_USER_POOL_ID or not COGNITO_CLIENT_ID:
        return _response(500, {"status": "error", "message": "Cognito not configured"})

    body = _parse_body(event)
    email = body.get("email")
    password = body.get("password")
    name = body.get("name", "")

    if not email or not password:
        return _response(400, {"status": "error", "message": "email and password are required"})

    client = boto3.client("cognito-idp")
    path = _get_path(event)

    try:
        if path.endswith("/signup"):
            result = _signup(client, email, password, name)
        elif path.endswith("/login"):
            result = _login(client, email, password)
        else:
            return _response(404, {"status": "error", "message": "Not found"})

        id_token = result.get("IdToken")
        access_token = result.get("AccessToken")
        refresh_token = result.get("RefreshToken")

        if not id_token:
            return _response(500, {"status": "error", "message": "Missing IdToken"})

        claims = _decode_id_token(id_token)
        return _response(200, {
            "status": "ok",
            "userId": claims.get("sub"),
            "email": claims.get("email", email),
            "name": claims.get("name", name),
            "idToken": id_token,
            "accessToken": access_token,
            "refreshToken": refresh_token,
        })

    except ClientError as exc:
        logger.error("Cognito error: %s", exc)
        return _response(400, {"status": "error", "message": str(exc)})
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        return _response(500, {"status": "error", "message": "Internal server error"})
