"""
Tests for config module
"""

from searcrawl.config import get_config_info


def test_get_config_info():
    """Test that get_config_info returns expected structure"""
    config = get_config_info()

    assert isinstance(config, dict)
    assert "searxng" in config
    assert "api" in config
    assert "crawler" in config
    assert "browser" in config
    assert "cache" in config
    assert "reader" in config
    assert "search_engines" in config

    # Check SearXNG config structure
    assert "host" in config["searxng"]
    assert "port" in config["searxng"]
    assert "base_path" in config["searxng"]
    assert "api_base" in config["searxng"]

    # Check API config structure
    assert "host" in config["api"]
    assert "port" in config["api"]

    # Check crawler config structure
    assert "default_search_limit" in config["crawler"]
    assert "content_filter_threshold" in config["crawler"]
    assert "word_count_threshold" in config["crawler"]
    assert "pool_size" in config["crawler"]
    assert "searxng_timeout_seconds" in config["crawler"]
    assert "http_extractor_enabled" in config["crawler"]
    assert "http_extractor_timeout_seconds" in config["crawler"]
    assert "http_extractor_max_concurrency" in config["crawler"]
    assert "http_extractor_min_content_length" in config["crawler"]

    # Check browser config structure
    assert "backend" in config["browser"]
    assert "browserless_ws_url" in config["browser"]
    assert "remote_timeout_seconds" in config["browser"]
    assert "remote_max_concurrency" in config["browser"]
    assert "local_fallback_enabled" in config["browser"]
    assert "local_max_concurrency" in config["browser"]

    # Check cache config structure
    assert "enabled" in config["cache"]
    assert "redis_url" in config["cache"]
    assert "crawl_ttl_hours" in config["cache"]
    assert "search_ttl_seconds" in config["cache"]

    # Check reader config structure
    assert "enabled" in config["reader"]
    assert "url" in config["reader"]
    assert "timeout_seconds" in config["reader"]
    assert "max_concurrency" in config["reader"]
    assert "min_content_length" in config["reader"]

    # Check search engines config structure
    assert "disabled" in config["search_engines"]
    assert "enabled" in config["search_engines"]


def test_config_types():
    """Test that config values have correct types"""
    config = get_config_info()

    assert isinstance(config["searxng"]["host"], str)
    assert isinstance(config["searxng"]["port"], int)
    assert isinstance(config["api"]["port"], int)
    assert isinstance(config["crawler"]["default_search_limit"], int)
    assert isinstance(config["crawler"]["content_filter_threshold"], float)
    assert isinstance(config["crawler"]["pool_size"], int)
    assert isinstance(config["crawler"]["searxng_timeout_seconds"], float)
    assert isinstance(config["crawler"]["http_extractor_enabled"], bool)
    assert isinstance(config["crawler"]["http_extractor_timeout_seconds"], float)
    assert isinstance(config["crawler"]["http_extractor_max_concurrency"], int)
    assert isinstance(config["crawler"]["http_extractor_min_content_length"], int)
    assert isinstance(config["cache"]["search_ttl_seconds"], int)
    assert isinstance(config["browser"]["backend"], str)
    assert isinstance(config["browser"]["remote_timeout_seconds"], float)
    assert isinstance(config["browser"]["remote_max_concurrency"], int)
    assert isinstance(config["browser"]["local_fallback_enabled"], bool)
    assert isinstance(config["browser"]["local_max_concurrency"], int)
    assert isinstance(config["reader"]["timeout_seconds"], float)
    assert isinstance(config["reader"]["max_concurrency"], int)
    assert isinstance(config["reader"]["min_content_length"], int)
