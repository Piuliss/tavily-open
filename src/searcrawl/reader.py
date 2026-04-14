import asyncio
from typing import Any, Optional
from urllib.parse import quote

import aiohttp

from .config import READER_API_KEY, READER_MIN_CONTENT_LENGTH, READER_TIMEOUT_SECONDS, READER_URL
from .extractor import is_content_usable
from .logger import logger


def build_reader_api_url(url: str, reader_url: str = READER_URL) -> str:
    """Build a Reader API URL with a safely encoded target URL."""
    return f"{reader_url.rstrip('/')}/{quote(url, safe='')}"


async def _fetch_with_session(
    session: aiohttp.ClientSession,
    url: str,
    timeout_seconds: float,
    min_content_length: int,
) -> Optional[dict[str, Any]]:
    """Fetch a URL using a provided aiohttp session."""
    reader_api_url = build_reader_api_url(url)
    headers = {
        "Accept": "application/json",
        "X-Respond-With": "markdown",
    }
    if READER_API_KEY:
        headers["Authorization"] = f"Bearer {READER_API_KEY}"

    try:
        async with session.get(
            reader_api_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout_seconds),
        ) as response:
            if response.status == 200:
                content = await response.text()
                if is_content_usable(content, min_content_length):
                    logger.debug(f"Successfully fetched content for {url} with Reader.")
                    return {"content": content, "reference": url}

                logger.warning(f"Reader returned no content for {url}.")
                return None

            error_text = await response.text()
            logger.error(
                f"Failed to fetch {url} with Reader. Status: {response.status}, Response: {error_text}"
            )
            return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout error when fetching {url} with Reader.")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"AIOHTTP client error when fetching {url} with Reader: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred when fetching {url} with Reader: {e}")
        return None


async def fetch_with_reader(
    url: str,
    session: Optional[aiohttp.ClientSession] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
    timeout_seconds: float = READER_TIMEOUT_SECONDS,
    min_content_length: int = READER_MIN_CONTENT_LENGTH,
) -> Optional[dict[str, Any]]:
    """
    Asynchronously fetches the content of a URL using the Reader service.

    Args:
        url (str): The URL to fetch.
        session: Optional shared aiohttp session for connection reuse.
        semaphore: Optional semaphore to cap concurrent Reader requests.
        timeout_seconds: Per-request timeout.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the fetched content and metadata,
                                     or None if the fetch failed.
    """

    async def _run_request(request_session: aiohttp.ClientSession) -> Optional[dict[str, Any]]:
        if semaphore is None:
            return await _fetch_with_session(
                request_session, url, timeout_seconds, min_content_length
            )

        async with semaphore:
            return await _fetch_with_session(
                request_session, url, timeout_seconds, min_content_length
            )

    if session is not None:
        return await _run_request(session)

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout_seconds)
    ) as owned_session:
        return await _run_request(owned_session)
