"""
Sear-Crawl4AI - An open-source search and crawling tool based on SearXNG and Crawl4AI.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional

import aiohttp
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

import searcrawl.logger as log_module
from searcrawl.cache import CacheManager
from searcrawl.config import (
    API_HOST,
    API_PORT,
    CACHE_ENABLED,
    CACHE_TTL_HOURS,
    DEFAULT_SEARCH_LIMIT,
    DISABLED_ENGINES,
    ENABLED_ENGINES,
    HTTP_EXTRACTOR_ENABLED,
    HTTP_EXTRACTOR_MAX_CONCURRENCY,
    HTTP_EXTRACTOR_TIMEOUT_SECONDS,
    READER_ENABLED,
    READER_MAX_CONCURRENCY,
    READER_TIMEOUT_SECONDS,
    REDIS_URL,
    SEARCH_CACHE_TTL_SECONDS,
    SEARXNG_TIMEOUT_SECONDS,
)
from searcrawl.crawler import WebCrawler

cache_manager: Optional[CacheManager] = None
searxng_client: Optional[httpx.AsyncClient] = None
page_client: Optional[httpx.AsyncClient] = None
reader_session: Optional[aiohttp.ClientSession] = None
reader_semaphore: Optional[asyncio.Semaphore] = None
http_semaphore: Optional[asyncio.Semaphore] = None
crawler_service: Optional[WebCrawler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    global cache_manager, crawler_service, http_semaphore, page_client, reader_semaphore, reader_session, searxng_client

    log_module.setup_logger("INFO")
    logger.info("Sear-Crawl4AI service starting...")

    if CACHE_ENABLED:
        try:
            logger.info(f"Initializing cache manager with Redis: {REDIS_URL}")
            cache_manager = CacheManager(REDIS_URL, CACHE_TTL_HOURS, SEARCH_CACHE_TTL_SECONDS)
            if await cache_manager.initialize():
                logger.info("Cache manager initialized successfully")
                logger.info(f"Cache stats: {await cache_manager.get_cache_stats()}")
            else:
                logger.warning("Cache manager initialized but Redis is not available")
                cache_manager = None
        except Exception as exc:
            logger.error(f"Failed to initialize cache manager: {str(exc)}")
            logger.warning("Continuing without cache")
            cache_manager = None

    searxng_client = httpx.AsyncClient(
        timeout=httpx.Timeout(SEARXNG_TIMEOUT_SECONDS),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    )
    page_client = httpx.AsyncClient(
        timeout=httpx.Timeout(HTTP_EXTRACTOR_TIMEOUT_SECONDS),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=200),
    )
    logger.info("Initialized shared HTTP clients for SearXNG and page extraction")

    if READER_ENABLED:
        reader_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=READER_TIMEOUT_SECONDS),
            connector=aiohttp.TCPConnector(
                limit=READER_MAX_CONCURRENCY,
                limit_per_host=READER_MAX_CONCURRENCY,
            ),
        )
        reader_semaphore = asyncio.Semaphore(READER_MAX_CONCURRENCY)
    else:
        reader_session = None
        reader_semaphore = None

    http_semaphore = (
        asyncio.Semaphore(HTTP_EXTRACTOR_MAX_CONCURRENCY) if HTTP_EXTRACTOR_ENABLED else None
    )
    crawler_service = WebCrawler(
        cache_manager=cache_manager,
        reader_session=reader_session,
        reader_semaphore=reader_semaphore,
        page_client=page_client,
        http_semaphore=http_semaphore,
    )
    logger.info(f"API service running at: http://{API_HOST}:{API_PORT}")
    logger.info("Sear-Crawl4AI service startup completed")

    yield

    logger.info("Starting graceful shutdown...")
    if crawler_service:
        await crawler_service.close()
        crawler_service = None
    if reader_session:
        await reader_session.close()
        reader_session = None
    if page_client:
        await page_client.aclose()
        page_client = None
    if searxng_client:
        await searxng_client.aclose()
        searxng_client = None
    if cache_manager:
        await cache_manager.close()
        cache_manager = None
    logger.info("Sear-Crawl4AI service shut down")


# Initialize FastAPI application with lifespan
app = FastAPI(
    title="Sear-Crawl4AI API",
    description="An open-source search and crawling tool based on SearXNG and Crawl4AI, "
    "serving as an open-source alternative to Tavily",
    version="1.0.0",
    lifespan=lifespan,
)


# Request model definitions
class SearchRequest(BaseModel):
    """Search request model

    Attributes:
        query: Search query string
        limit: Limit on number of results to return, default is 10
        disabled_engines: List of disabled search engines, comma-separated
        enabled_engines: List of enabled search engines, comma-separated
    """

    query: str
    limit: int = DEFAULT_SEARCH_LIMIT
    disabled_engines: str = DISABLED_ENGINES
    enabled_engines: str = ENABLED_ENGINES


class CrawlRequest(BaseModel):
    """
    Crawl request model

    Attributes:
        urls: List of URLs to crawl
        instruction: Crawling instruction, typically a search query
    """

    urls: list[str]
    instruction: str


async def crawl(request: CrawlRequest):
    """
    API endpoint function to crawl multiple URLs and process content

    Args:
        request: Crawl request containing URLs and instruction

    Returns:
        Dict: Dictionary containing processed content, success count, and failed URLs

    Raises:
        HTTPException: Raised when an error occurs during crawling
    """
    global crawler_service
    if crawler_service is None:
        raise HTTPException(status_code=503, detail="Crawler service not initialized")

    result = await crawler_service.crawl_urls(request.urls, request.instruction)
    result.setdefault("timings_ms", {})["pool_wait"] = 0.0
    return result


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics endpoint

    Returns cache statistics including total entries and memory usage

    Returns:
        Dict: Cache statistics
    """
    global cache_manager
    try:
        if not cache_manager:
            logger.warning("Cache manager not available")
            return {"status": "unavailable", "message": "Cache is not enabled or not available"}

        stats = await cache_manager.get_cache_stats()
        logger.info(f"Cache stats retrieved: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/cache/clear")
async def clear_cache():
    """
    Clear all cache entries endpoint

    Clears all cached crawl results

    Returns:
        Dict: Operation result
    """
    global cache_manager
    try:
        if not cache_manager:
            logger.warning("Cache manager not available")
            return {"status": "unavailable", "message": "Cache is not enabled or not available"}

        success = await cache_manager.clear_all()
        if success:
            logger.info("Cache cleared successfully")
            return {"status": "success", "message": "Cache cleared successfully"}
        else:
            logger.warning("Failed to clear cache")
            return {"status": "error", "message": "Failed to clear cache"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/search")
async def search(request: SearchRequest):
    """
    Search API endpoint

    Receives search request, calls SearXNG search engine to get results,
    then crawls the search result pages

    Args:
        request: Search request object containing query string and configuration parameters

    Returns:
        Dict: Dictionary containing processed content, success count, and failed URLs

    Raises:
        HTTPException: Raised when an error occurs during search or crawling
    """
    global cache_manager
    global searxng_client
    search_started = time.perf_counter()
    try:
        # Add status feedback
        logger.info(f"Starting search: {request.query}")

        # Check cache for search results
        if cache_manager:
            cached_result = await cache_manager.get_search_cache(request.query)
            if cached_result:
                logger.info(f"Search cache hit for query: {request.query}")
                cached_result.setdefault("timings_ms", {})["search_total"] = round(
                    (time.perf_counter() - search_started) * 1000,
                    2,
                )
                return cached_result

        # Call SearXNG search engine (now async)
        response = await WebCrawler.make_searxng_request(
            query=request.query,
            limit=request.limit,
            disabled_engines=request.disabled_engines,
            enabled_engines=request.enabled_engines,
            client=searxng_client,
        )

        # Check search results
        results = response.get("results", [])
        if not results:
            logger.warning("No search results found")
            raise HTTPException(status_code=404, detail="No search results found")

        # Limit result count and extract URLs
        urls = [result["url"] for result in results[: request.limit] if "url" in result]
        if not urls:
            logger.warning("No valid URLs found")
            raise HTTPException(status_code=404, detail="No valid URLs found")

        logger.info(f"Found {len(urls)} URLs, starting to crawl")

        # Call crawl function to process URLs
        crawl_result = await crawl(CrawlRequest(urls=urls, instruction=request.query))
        crawl_result.setdefault("timings_ms", {})["search_total"] = round(
            (time.perf_counter() - search_started) * 1000,
            2,
        )

        # Cache the search result
        if cache_manager:
            await cache_manager.set_search_cache(request.query, crawl_result)

        return crawl_result
    except HTTPException:
        # Directly re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log other exceptions and convert to HTTP exception
        logger.error(f"Exception occurred during search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def main():
    """Main entry point for the application"""
    logger.info("Starting Sear-Crawl4AI service via command line")
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    main()
