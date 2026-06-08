"""Secure HTTP client for MyAgent with SSRF protection.

Provides a safe HTTP client with:
- SSRF (Server-Side Request Forgery) protection
- Retry with exponential backoff
- Timeouts
- Request/response logging
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import random
import socket
from typing import Any, cast
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Private network ranges to block for SSRF protection
PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 private ranges
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fd00::/8"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
]

# Safe ports that can be accessed
SAFE_PORTS = {80, 443, 8080, 8443}


class SSRFProtectionError(Exception):
    """Raised when a request is blocked by SSRF protection."""
    pass


def is_private_ip(host: str) -> bool:
    """Check if a hostname resolves to a private IP address.

    Args:
        host: The hostname or IP address to check.

    Returns:
        True if the host is private, False otherwise.
    """
    try:
        ip_addr = ipaddress.ip_address(host)
        return any(ip_addr in net for net in PRIVATE_NETWORKS)
    except ValueError:
        # Not a direct IP, try to resolve
        try:
            addrinfo_list = socket.getaddrinfo(host, None, socket.AF_UNSPEC)
            for addrinfo in addrinfo_list:
                ip_str = addrinfo[4][0]
                try:
                    ip_addr = ipaddress.ip_address(ip_str)
                    if any(ip_addr in net for net in PRIVATE_NETWORKS):
                        return True
                except ValueError:
                    continue
            return False
        except socket.gaierror:
            return False


def validate_url(url: str, allow_private: bool = False) -> tuple[str, int]:
    """Validate a URL for safety against SSRF attacks.

    Args:
        url: The URL to validate.
        allow_private: Whether to allow private network access.

    Returns:
        Tuple of (hostname, port) if valid.

    Raises:
        SSRFProtectionError: If the URL is blocked.
    """
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise SSRFProtectionError(f"Invalid URL scheme: {parsed.scheme}")

    hostname = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    if port not in SAFE_PORTS:
        raise SSRFProtectionError(f"Port {port} is not allowed")

    if not allow_private and is_private_ip(hostname):
        raise SSRFProtectionError(f"Host '{hostname}' is blocked (private network)")

    return hostname, port


class SafeHTTPClient:
    """Secure HTTP client with SSRF protection and retries."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        allow_private_networks: bool = False,
        **kwargs: Any
    ) -> None:
        """Initialize the safe HTTP client.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            base_delay: Base delay for exponential backoff.
            max_delay: Maximum delay between retries.
            allow_private_networks: Whether to allow access to private networks.
            **kwargs: Additional kwargs passed to httpx.AsyncClient.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.allow_private_networks = allow_private_networks
        self._client_kwargs = kwargs

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> httpx.Response:
        """Make a request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: URL to request.
            **kwargs: Additional kwargs for httpx.request.

        Returns:
            The httpx.Response object.

        Raises:
            httpx.HTTPError: If all retries fail.
        """
        # Validate URL before making request
        validate_url(url, allow_private=self.allow_private_networks)

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, **self._client_kwargs) as client:
                    request = client.build_request(method, url, **kwargs)
                    logger.debug(
                        f"HTTP {method} {url} (attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    response = await client.send(request)
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise
                last_error = e
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
            except Exception as e:
                # Don't retry on validation errors
                if isinstance(e, SSRFProtectionError):
                    raise
                last_error = e

            if attempt < self.max_retries:
                # Exponential backoff with jitter
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                jitter = random.uniform(0, delay * 0.25)
                wait_time = delay + jitter
                logger.debug(f"Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)

        if last_error:
            raise last_error
        raise httpx.HTTPError("Request failed with no retries remaining")

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a GET request."""
        return await self._request_with_retry("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a POST request."""
        return await self._request_with_retry("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a PUT request."""
        return await self._request_with_retry("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a DELETE request."""
        return await self._request_with_retry("DELETE", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a PATCH request."""
        return await self._request_with_retry("PATCH", url, **kwargs)


# Default client instance
_default_client: SafeHTTPClient | None = None


def get_default_client() -> SafeHTTPClient:
    """Get or create the default SafeHTTPClient instance."""
    global _default_client
    if _default_client is None:
        _default_client = SafeHTTPClient()
    return _default_client
