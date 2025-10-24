"""Logging plugin that logs HTTP requests and responses.

This example demonstrates implementing both request and response flows
for observability purposes.
"""

import asyncio
import logging
import sys

from google.protobuf.empty_pb2 import Empty
from grpc import ServicerContext

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
        return Metadata(
            name="logging-plugin",
            version="1.0.0",
            description="Logs HTTP request and response details for observability",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for both request and response flows."""
        return Capabilities(flows=[FLOW_REQUEST, FLOW_RESPONSE])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Log incoming request details."""
        logger.info("=" * 80)
        logger.info("INCOMING REQUEST")
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Path: {request.path}")
        logger.info(f"Remote Address: {request.remote_addr}")

        # Log headers.
        logger.info("Headers:")
        for key, value in request.headers.items():
            # Mask sensitive headers.
            if key.lower() in ("authorization", "cookie"):
                value = "***REDACTED***"
            logger.info(f"  {key}: {value}")

        # Log body size.
        if request.body:
            logger.info(f"Body size: {len(request.body)} bytes")

        logger.info("=" * 80)

        # Continue processing.
        return HTTPResponse(**{"continue": True})

    async def HandleResponse(self, request: HTTPResponse, context: ServicerContext) -> HTTPResponse:
        """Log outgoing response details."""
        logger.info("=" * 80)
        logger.info("OUTGOING RESPONSE")
        logger.info(f"Status Code: {request.status_code}")

        # Log headers.
        logger.info("Headers:")
        for key, value in request.headers.items():
            logger.info(f"  {key}: {value}")

        # Log body size.
        if request.body:
            logger.info(f"Body size: {len(request.body)} bytes")

        logger.info("=" * 80)

        # Continue processing.
        return HTTPResponse(**{"continue": True})


if __name__ == "__main__":
    asyncio.run(serve(LoggingPlugin(), sys.argv))
