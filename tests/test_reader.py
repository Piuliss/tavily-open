"""
Tests for reader helpers.
"""

from searcrawl.reader import build_reader_api_url


def test_build_reader_api_url_encodes_target_url():
    """Reader URL builder should safely encode the upstream URL."""
    target_url = "https://example.com/path?q=hello world&lang=zh-CN"

    result = build_reader_api_url(target_url, reader_url="http://reader:3000")

    assert result.startswith("http://reader:3000/")
    assert "https%3A%2F%2Fexample.com%2Fpath%3Fq%3Dhello%20world%26lang%3Dzh-CN" in result
