"""
Tests for rate limiting
"""
import pytest


def test_rate_limit_allows_normal_read_traffic(client):
    """Test that normal read traffic is not rate limited"""
    # Global rate limit is 200/min, so 15 requests should pass easily
    for i in range(15):
        response = client.get("/api/activities")
        assert response.status_code != 429, f"Rate limited at request {i+1}"
