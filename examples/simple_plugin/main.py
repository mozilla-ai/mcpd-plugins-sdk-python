"""Simple plugin that adds a custom header to HTTP requests.

This example demonstrates the minimal implementation needed for a plugin.
It adds a custom header to all incoming requests.
"""

import asyncio
import logging

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


class SimplePlugin(BasePlugin):
    """A simple plugin that adds a custom header to requests."""

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Return plugin metadata."""
        return Metadata(
            name="simple-plugin",
            version="1.0.0",
            description="Adds a custom header to HTTP requests",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for request flow."""
        return Capabilities(flows=[FLOW_REQUEST])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Add a custom header to the request."""
        logger.info(f"Processing request: {request.method} {request.url}")

        # Create response with Continue=True to pass the request through.
        response = HTTPResponse(**{"continue": True})

        # Copy original headers.
        for key, value in request.headers.items():
            response.modified_request.headers[key] = value

        # Add custom header.
        response.modified_request.headers["X-Simple-Plugin"] = "processed"

        # Copy other request fields.
        response.modified_request.method = request.method
        response.modified_request.url = request.url
        response.modified_request.path = request.path
        response.modified_request.body = request.body

        logger.info("Added X-Simple-Plugin header")
        return response


if __name__ == "__main__":
    asyncio.run(serve(SimplePlugin()))
