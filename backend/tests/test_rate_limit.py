"""Tests for per-client API rate limiting."""

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from backend import main as main_module


@pytest.fixture(autouse=True)
def clear_api_state():
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()
    yield
    main_module.response_cache.clear()
    main_module.rate_limiter.clear()


def set_rate_limit(monkeypatch, limit: int) -> None:
    monkeypatch.setattr(
        main_module,
        "settings",
        replace(main_module.settings, rate_limit_per_min=limit),
    )


def test_requests_below_configured_limit_are_allowed(monkeypatch):
    set_rate_limit(monkeypatch, 2)
    client = TestClient(main_module.app, client=("192.0.2.1", 12345))
    payload = {"glosses": ["HELLO"], "lang": "en"}

    first = client.post("/api/sentence", json=payload)
    second = client.post("/api/sentence", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200


def test_request_over_configured_limit_returns_clear_429(monkeypatch):
    set_rate_limit(monkeypatch, 1)
    client = TestClient(main_module.app, client=("192.0.2.1", 12345))
    payload = {"glosses": ["HELLO"], "lang": "en"}

    assert client.post("/api/sentence", json=payload).status_code == 200
    limited = client.post("/api/sentence", json=payload)

    assert limited.status_code == 429
    assert limited.json() == {
        "message": "Rate limit exceeded. Maximum 1 requests per minute."
    }
    assert int(limited.headers["Retry-After"]) >= 1


def test_different_clients_have_independent_limits(monkeypatch):
    set_rate_limit(monkeypatch, 1)
    first_client = TestClient(main_module.app, client=("192.0.2.1", 12345))
    second_client = TestClient(main_module.app, client=("192.0.2.2", 12345))

    first_response = first_client.post(
        "/api/sentence",
        json={"glosses": ["HELLO"], "lang": "en"},
    )
    second_response = second_client.post(
        "/api/sentence",
        json={"glosses": ["THANK_YOU"], "lang": "en"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200


def test_arbitrary_forwarding_headers_do_not_change_client_bucket(monkeypatch):
    set_rate_limit(monkeypatch, 1)
    client = TestClient(main_module.app, client=("192.0.2.1", 12345))
    payload = {"glosses": ["HELLO"], "lang": "en"}

    first = client.post(
        "/api/sentence",
        json=payload,
        headers={"X-Forwarded-For": "198.51.100.1"},
    )
    second = client.post(
        "/api/sentence",
        json=payload,
        headers={"X-Forwarded-For": "198.51.100.2"},
    )

    assert first.status_code == 200
    assert second.status_code == 429


def test_limiter_expires_requests_after_one_minute():
    limiter = main_module.ClientRateLimiter()

    assert limiter.allow_request("client-a", 1, now=100.0)
    assert not limiter.allow_request("client-a", 1, now=159.0)
    assert limiter.allow_request("client-a", 1, now=160.0)


def test_limiter_bounds_tracked_client_state():
    limiter = main_module.ClientRateLimiter(max_clients=1)

    assert limiter.allow_request("client-a", 1, now=100.0)
    assert not limiter.allow_request("client-b", 1, now=101.0)
    assert limiter.allow_request("client-b", 1, now=160.0)


def test_retry_delay_tracks_oldest_request_in_sliding_window():
    limiter = main_module.ClientRateLimiter()

    assert limiter.try_acquire("client-a", 2, now=100.25) is None
    assert limiter.try_acquire("client-a", 2, now=110.0) is None
    assert limiter.try_acquire("client-a", 2, now=120.0) == 41
    assert limiter.try_acquire("client-a", 2, now=160.25) is None


def test_concurrent_requests_never_exceed_one_client_limit():
    limiter = main_module.ClientRateLimiter()
    request_count = 32
    request_limit = 7
    start = Barrier(request_count)

    def request_quota(_: int) -> bool:
        start.wait()
        return limiter.try_acquire("shared-client", request_limit, now=100.0) is None

    with ThreadPoolExecutor(max_workers=request_count) as executor:
        allowed = list(executor.map(request_quota, range(request_count)))

    assert sum(allowed) == request_limit
    assert all(
        limiter.try_acquire("shared-client", request_limit, now=100.0) is not None
        for _ in range(2)
    )
