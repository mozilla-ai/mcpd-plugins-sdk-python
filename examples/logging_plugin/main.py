"""Logging plugin that logs HTTP requests and responses.

This example demonstrates implementing both request and response flows
for observability purposes.
"""

import asyncio
import logging
import sys

from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext

from mcpd_plugins import BasePlugin, serve
from mcpd_plugins.v1.plugins.plugin_pb2 import (
    FLOW_REQUEST,
    FLOW_RESPONSE,
    Capabilities,
    HTTPRequest,
    HTTPResponse,
    Metadata,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LoggingPlugin(BasePlugin):
    """Plugin that logs HTTP request and response details."""

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Return plugin metadata."""
        _ = (request, context)
        return Metadata(
            name="logging-plugin",
            version="1.0.0",
            description="Logs HTTP request and response details for observability",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for both request and response flows."""
        _ = (request, context)
        return Capabilities(flows=[FLOW_REQUEST, FLOW_RESPONSE])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Log incoming request details."""
        _ = context
        logger.info("=" * 80)
        logger.info("INCOMING REQUEST")
        logger.info("Method: %s", request.method)
        logger.info("URL: %s", request.url)
        logger.info("Path: %s", request.path)
        logger.info("Remote Address: %s", request.remote_addr)

        # Log headers.
        logger.info("Headers:")
        for key, value in request.headers.items():
            # Mask sensitive headers.
            if key.lower() in ("authorization", "cookie"):
                value = "***REDACTED***"
            logger.info("  %s: %s", key, value)

        # Log body size.
        if request.body:
            logger.info("Body size: %s bytes", len(request.body))

        logger.info("=" * 80)

        # Continue processing.
        return HTTPResponse(**{"continue": True})

    async def HandleResponse(self, response: HTTPResponse, context: ServicerContext) -> HTTPResponse:
        """Log outgoing response details."""
        _ = context
        logger.info("=" * 80)
        logger.info("OUTGOING RESPONSE")
        logger.info("Status Code: %s", response.status_code)

        # Log headers.
        logger.info("Headers:")
        for key, value in response.headers.items():
            logger.info("  %s: %s", key, value)

        # Log body size.
        if response.body:
            logger.info("Body size: %s bytes", len(response.body))

        logger.info("=" * 80)

        # Continue processing.
        return HTTPResponse(**{"continue": True})


if __name__ == "__main__":
    asyncio.run(serve(LoggingPlugin(), sys.argv))
