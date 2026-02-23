"""Lightweight checks for Terraform auth configuration."""
from pathlib import Path


def test_api_gateway_authorizer_config_present():
    main_tf = Path(__file__).resolve().parents[1] / "terraform" / "main.tf"
    contents = main_tf.read_text(encoding="utf-8")

    assert "aws_api_gateway_authorizer" in contents
    assert "COGNITO_USER_POOLS" in contents


def test_auth_routes_present():
    main_tf = Path(__file__).resolve().parents[1] / "terraform" / "main.tf"
    contents = main_tf.read_text(encoding="utf-8")

    assert "path_part   = \"auth\"" in contents
    assert "path_part   = \"signup\"" in contents
    assert "path_part   = \"login\"" in contents
