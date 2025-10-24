"""Rate limiting plugin using a simple token bucket algorithm.

This example demonstrates stateful request processing and rate limiting.
"""

import asyncio
import logging
import sys
import time
from collections import defaultdict

from google.protobuf.empty_pb2 import Empty
from grpc import ServicerContext

from mcpd_plugins import BasePlugin, serve
from mcpd_plugins.v1.plugins.plugin_pb2 import (
    FLOW_REQUEST,
    Capabilities,
    HTTPRequest,
    HTTPResponse,
    Metadata,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimitPlugin(BasePlugin):
    """Plugin that implements rate limiting using token bucket algorithm."""

    def __init__(self, requests_per_minute: int = 60):
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute per client.
        """
        super().__init__()
        self.requests_per_minute = requests_per_minute
        self.rate_per_second = requests_per_minute / 60.0

        # Track tokens for each client IP.
        self.buckets: dict[str, float] = defaultdict(lambda: float(requests_per_minute))
        self.last_update: dict[str, float] = defaultdict(time.time)

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Return plugin metadata."""
        return Metadata(
            name="rate-limit-plugin",
            version="1.0.0",
            description=f"Rate limits requests to {self.requests_per_minute} per minute per client",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for request flow."""
        return Capabilities(flows=[FLOW_REQUEST])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Apply rate limiting based on client IP."""
        client_ip = request.remote_addr or "unknown"
        logger.info(f"Rate limit check for {client_ip}: {request.method} {request.url}")

        # Refill tokens based on time elapsed.
        now = time.time()
        elapsed = now - self.last_update[client_ip]
        self.buckets[client_ip] = min(
            self.requests_per_minute,
            self.buckets[client_ip] + elapsed * self.rate_per_second,
        )
        self.last_update[client_ip] = now

        # Check if client has tokens available.
        if self.buckets[client_ip] < 1.0:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return self._rate_limit_response(client_ip)

        # Consume one token.
        self.buckets[client_ip] -= 1.0
        logger.info(f"Request allowed for {client_ip} (tokens remaining: {self.buckets[client_ip]:.2f})")

        # Add rate limit headers to response.
        response = HTTPResponse(**{"continue": True})
        response.modified_request.CopyFrom(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(self.buckets[client_ip]))

        return response

    def _rate_limit_response(self, client_ip: str) -> HTTPResponse:
        """Create a 429 Too Many Requests response."""
        # Calculate retry-after in seconds.
        tokens_needed = 1.0 - self.buckets[client_ip]
        retry_after = int(tokens_needed / self.rate_per_second) + 1

        response = HTTPResponse(
            **{"continue": False},
            status_code=429,
            body=b'{"error": "Rate limit exceeded"}',
        )
        response.headers["Content-Type"] = "application/json"
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["Retry-After"] = str(retry_after)

        return response


if __name__ == "__main__":
    asyncio.run(serve(RateLimitPlugin(requests_per_minute=60), sys.argv))
