"""Unit tests for AgriConnect health and root endpoints."""

from app.api.health import health_check
from app.main import root


def test_health_check_function():
    """Direct unit test of health check function."""
    result = health_check()
    assert result["status"] == "ok"
    assert result["app"] == "AgriConnect"
    assert result["version"] == "1.3.1"
    assert "Milestone 1" in result["milestone"]


def test_root_function():
    """Direct unit test of root info function."""
    result = root()
    assert "AgriConnect" in result["message"]
    assert result["health_check"] == "/api/v1/health"
