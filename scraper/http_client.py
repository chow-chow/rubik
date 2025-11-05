"""
HTTP client for making web requests.
"""

import logging
import random
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import get_config

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with retry logic and rate limiting."""

    def __init__(self):
        """Initialize HTTP client."""
        self.config = get_config()
        self.session = self._create_session()
        self.request_count = 0

    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _apply_rate_limit(self) -> None:
        """Apply delay between requests."""
        if self.request_count > 0:
            delay = random.uniform(*self.config.DELAY_RANGE)
            time.sleep(delay)

    def get(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        self._apply_rate_limit()
        self.request_count += 1

        headers = {
            "User-Agent": random.choice(self.config.USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml",
        }

        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(
                url, headers=headers, timeout=self.config.TIMEOUT
            )
            response.raise_for_status()

            logger.debug(f"Success: {url} (Status: {response.status_code})")
            return BeautifulSoup(response.text, "html.parser")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def get_stats(self) -> dict:
        """Get client statistics."""
        return {"total_requests": self.request_count}
