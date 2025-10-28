"""Simple plugin that adds a custom header to HTTP requests.

This example demonstrates the minimal implementation needed for a plugin.
It adds a custom header to all incoming requests.
"""

import asyncio
import logging
import sys

from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext

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


class SimplePlugin(BasePlugin):
    """A simple plugin that adds a custom header to requests."""

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Return plugin metadata."""
        _ = (request, context)
        return Metadata(
            name="simple-plugin",
            version="1.0.0",
            description="Adds a custom header to HTTP requests",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for request flow."""
        _ = (request, context)
        return Capabilities(flows=[FLOW_REQUEST])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Add a custom header to the request."""
        _ = context
        logger.info("Processing request: %s %s", request.method, request.url)

        # Create response with Continue=True to pass the request through.
        response = HTTPResponse(**{"continue": True})

        # Start from the original request, then mutate headers.
        response.modified_request.CopyFrom(request)
        response.modified_request.headers["X-Simple-Plugin"] = "processed"

        logger.info("Added X-Simple-Plugin header")
        return response


if __name__ == "__main__":
    asyncio.run(serve(SimplePlugin(), sys.argv))
