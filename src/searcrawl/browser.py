"""
Browser-backed extraction helpers.
"""

import asyncio
import subprocess
import sys
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from loguru import logger

from .anti_crawl import AntiCrawlConfig


class BrowserBackend:
    """Run browser-based extraction against local or remote Chrome backends."""

    _install_lock = asyncio.Lock()
    _local_browser_installed = False

    def __init__(
        self,
        name: str,
        anti_crawl_config: AntiCrawlConfig,
        max_concurrency: int = 1,
        cdp_url: str = "",
        enabled: bool = True,
        install_local_browser: bool = False,
    ) -> None:
        self.name = name
        self.anti_crawl_config = anti_crawl_config
        self.cdp_url = cdp_url
        self.enabled = enabled
        self.install_local_browser = install_local_browser
        self.semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def _ensure_local_browser_installed(self) -> None:
        if not self.install_local_browser or BrowserBackend._local_browser_installed:
            return

        async with BrowserBackend._install_lock:
            if BrowserBackend._local_browser_installed:
                return

            logger.info("Installing local Chromium for fallback browser backend")
            await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
            )
            BrowserBackend._local_browser_installed = True

    def _build_browser_config(self) -> BrowserConfig:
        headers = self.anti_crawl_config.get_headers()
        proxy = self.anti_crawl_config.get_proxy()
        extra_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        if self.cdp_url:
            return BrowserConfig(
                headless=True,
                verbose=False,
                cdp_url=self.cdp_url,
                headers=headers if headers else {},
                proxy=proxy if proxy else "",
            )

        return BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=extra_args,
            headers=headers if headers else {},
            proxy=proxy if proxy else "",
        )

    async def fetch_urls(
        self,
        urls: list[str],
        run_config: CrawlerRunConfig,
    ) -> tuple[list[dict[str, str]], list[str]]:
        """Fetch URLs with a browser backend and normalize successful results."""
        if not self.enabled or not urls:
            return [], urls

        async with self.semaphore:
            try:
                if not self.cdp_url:
                    await self._ensure_local_browser_installed()

                browser_config = self._build_browser_config()
                crawler = await AsyncWebCrawler(config=browser_config).__aenter__()
            except Exception as exc:
                logger.warning(f"Failed to initialize {self.name} browser backend: {exc}")
                return [], urls

            try:
                crawl_result = await crawler.arun_many(urls=urls, config=run_config)
                results: list[Any] = []
                if hasattr(crawl_result, "__aiter__"):
                    async for result in crawl_result:  # type: ignore[union-attr]
                        results.append(result)
                else:
                    results = list(crawl_result) if crawl_result else []  # type: ignore[arg-type]

                return self._normalize_results(urls, results)
            except Exception as exc:
                logger.warning(f"{self.name} browser crawl batch failed: {exc}")
                return [], urls
            finally:
                await crawler.__aexit__(None, None, None)

    def _normalize_results(
        self,
        urls: list[str],
        results: list[Any],
    ) -> tuple[list[dict[str, str]], list[str]]:
        successful_results: list[dict[str, str]] = []
        retry_urls: list[str] = []

        for index, result in enumerate(results):
            url = urls[index]
            try:
                if result is None or not getattr(result, "success", False):
                    retry_urls.append(url)
                    continue

                markdown_result = getattr(result, "markdown", None)
                fit_markdown = getattr(markdown_result, "fit_markdown", None)
                if not fit_markdown:
                    retry_urls.append(url)
                    continue

                successful_results.append(
                    {
                        "content": fit_markdown,
                        "reference": url,
                    }
                )
            except Exception as exc:
                logger.warning(f"{self.name} browser crawl failed for {url}: {exc}")
                retry_urls.append(url)

        remaining_urls = retry_urls + urls[len(results) :]
        return successful_results, remaining_urls

    async def close(self) -> None:
        """Close any owned resources."""
        return None
