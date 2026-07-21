"""
Tests for dynamic Reader endpoint discovery in the crawler.
"""

import pytest

import searcrawl.crawler as crawler_module
from searcrawl.crawler import WebCrawler


@pytest.mark.asyncio
async def test_crawler_passes_dynamic_reader_urls(monkeypatch):
    """Crawler should pass discovered Reader endpoints into the Reader client."""
    captured_reader_urls = []

    async def fake_fetch_with_reader(url, **kwargs):
        captured_reader_urls.append(kwargs.get("reader_urls"))
        return {"content": "Recovered content " * 40, "reference": url}

    async def reader_url_provider():
        return ["http://reader-a:3000", "http://reader-b:3000"]

    monkeypatch.setattr(crawler_module, "fetch_with_reader", fake_fetch_with_reader)

    crawler = WebCrawler(reader_url_provider=reader_url_provider)
    try:
        results, pending_urls = await crawler._run_reader_stage(
            ["https://example.com/page"],
            instruction="example",
        )
    finally:
        await crawler.close()

    assert pending_urls == []
    assert len(results) == 1
    assert captured_reader_urls == [["http://reader-a:3000", "http://reader-b:3000"]]


@pytest.mark.asyncio
async def test_reader_first_accepts_reader_content_without_quality_gate(monkeypatch):
    """reader_first should not reject usable Reader content only because query terms differ."""

    async def fake_fetch_with_reader(url, **kwargs):
        return {"content": "Useful reader content without matching query terms. " * 40, "reference": url}

    async def fail_if_http_stage_runs(*args, **kwargs):
        raise AssertionError("HTTP fallback should not run after a usable Reader result")

    monkeypatch.setattr(crawler_module, "CRAWL_EXTRACTION_STRATEGY", "reader_first")
    monkeypatch.setattr(crawler_module, "CRAWL_QUALITY_GATE_ENABLED", True)
    monkeypatch.setattr(crawler_module, "fetch_with_reader", fake_fetch_with_reader)
    monkeypatch.setattr(crawler_module, "fetch_with_http_extractor", fail_if_http_stage_runs)

    crawler = WebCrawler()
    timings_ms = {"reader": 0.0, "fast_http": 0.0}
    stage_counts = {"reader_hits": 0, "fast_path_hits": 0}
    try:
        results, pending_urls = await crawler._run_configured_extraction_stages(
            ["https://example.com/page"],
            instruction="unmatched query",
            timings_ms=timings_ms,
            stage_counts=stage_counts,
        )
    finally:
        await crawler.close()

    assert pending_urls == []
    assert len(results) == 1
    assert results[0]["source_stage"] == "reader"
    assert stage_counts["reader_hits"] == 1
