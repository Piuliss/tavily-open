"""
Tests for search flow modes and timing metadata.
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import searcrawl.main as main_module


class FakeProvider:
    """Simple async provider stub for API tests."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    async def search(self, request):
        self.calls.append(request)
        return self.response


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(main_module.app)


def test_search_mode_returns_normalized_results_without_crawling(client, monkeypatch):
    """Search-only mode should skip crawling and return normalized hits."""
    provider = FakeProvider(
        SimpleNamespace(
            provider="searxng",
            request_ms=12.5,
            hits=[
                SimpleNamespace(
                    url="https://example.com/result",
                    title="Example Result",
                    snippet="A normalized snippet",
                    provider="searxng",
                )
            ],
        )
    )

    def fail_if_crawl_called(_request):
        raise AssertionError("crawl should not run in search mode")

    monkeypatch.setattr(
        main_module,
        "get_search_provider",
        lambda provider_name, client: provider,
        raising=False,
    )
    monkeypatch.setattr(main_module, "cache_manager", None)
    monkeypatch.setattr(main_module, "crawl", fail_if_crawl_called)

    response = client.post(
        "/search",
        json={"query": "example", "mode": "search", "provider": "searxng"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["mode"] == "search"
    assert payload["provider"] == "searxng"
    assert payload["success_count"] == 1
    assert payload["results"] == [
        {
            "url": "https://example.com/result",
            "title": "Example Result",
            "snippet": "A normalized snippet",
            "provider": "searxng",
        }
    ]
    assert payload["timings_ms"]["search_provider_request"] == 12.5
    assert payload["timings_ms"]["search_total"] >= 0


def test_crawl_mode_preserves_crawl_pipeline_and_adds_search_timings(client, monkeypatch):
    """Default crawl mode should use provider hits as crawl inputs and report provider timing."""
    provider = FakeProvider(
        SimpleNamespace(
            provider="brave",
            request_ms=7.25,
            hits=[
                SimpleNamespace(
                    url="https://example.com/a",
                    title="A",
                    snippet="A snippet",
                    provider="brave",
                ),
                SimpleNamespace(
                    url="https://example.com/b",
                    title="B",
                    snippet="B snippet",
                    provider="brave",
                ),
            ],
        )
    )
    captured = {}

    async def fake_crawl(request):
        captured["request"] = request
        return {
            "results": [{"content": "page body", "reference": "https://example.com/a"}],
            "success_count": 1,
            "failed_urls": [],
            "cache_hits": 0,
            "newly_crawled": 1,
            "timings_ms": {"total": 50.0},
        }

    monkeypatch.setattr(
        main_module,
        "get_search_provider",
        lambda provider_name, client: provider,
        raising=False,
    )
    monkeypatch.setattr(main_module, "cache_manager", None)
    monkeypatch.setattr(main_module, "crawl", fake_crawl)

    response = client.post("/search", json={"query": "example", "provider": "brave"})

    assert response.status_code == 200
    payload = response.json()

    assert payload["search_provider"] == "brave"
    assert payload["timings_ms"]["search_provider_request"] == 7.25
    assert payload["timings_ms"]["search_total"] >= payload["timings_ms"]["search_provider_request"]
    assert captured["request"].instruction == "example"
    assert captured["request"].urls == ["https://example.com/a", "https://example.com/b"]
