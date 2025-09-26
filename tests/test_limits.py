import pytest
from unittest.mock import Mock
from zoo_mcp.limits import (
    RateLimitError,
    handle_rate_limit_headers,
    parse_rate_limit,
    generate_time_windows,
    PageCache,
)


def test_handle_rate_limit_headers():
    response = Mock()
    response.status_code = 429
    response.headers = {"Retry-After": "60"}
    assert handle_rate_limit_headers(response) == 60

    response.status_code = 200
    assert handle_rate_limit_headers(response) is None


def test_parse_rate_limit():
    response = Mock()
    response.headers = {"X-RateLimit-Remaining": "100", "X-RateLimit-Reset": "1234567890"}
    result = parse_rate_limit(response)
    assert result["remaining"] == 100
    assert result["reset"] == 1234567890


def test_generate_time_windows():
    windows = generate_time_windows("2024-01-01", "2024-03-01", window_days=30)
    assert len(windows) > 0
    assert "2024-01-01" in windows[0]


def test_page_cache():
    cache = PageCache(max_size=2)

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    cache.set("key2", "value2")
    cache.set("key3", "value3")

    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

    cache.clear()
    assert cache.get("key2") is None