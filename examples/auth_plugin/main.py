"""Authentication plugin that validates Bearer tokens.

This example demonstrates how to reject requests that don't meet security requirements.
"""

import asyncio
import logging
import os

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


class AuthPlugin(BasePlugin):
    """Plugin that validates Bearer token authentication."""

    def __init__(self):
        """Initialize the auth plugin with expected token."""
        super().__init__()
        self.expected_token = os.getenv("AUTH_TOKEN", "secret-token-123")

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Return plugin metadata."""
        return Metadata(
            name="auth-plugin",
            version="1.0.0",
            description="Validates Bearer token authentication",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for request flow."""
        return Capabilities(flows=[FLOW_REQUEST])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Validate Bearer token in Authorization header."""
        logger.info(f"Authenticating request: {request.method} {request.url}")

        # Check for Authorization header.
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            return self._unauthorized_response("Missing or invalid Authorization header")

        # Extract and validate token.
        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != self.expected_token:
            logger.warning("Invalid token")
            return self._unauthorized_response("Invalid token")

        # Token is valid, allow request to continue.
        logger.info("Authentication successful")
        return HTTPResponse(**{"continue": True})

    def _unauthorized_response(self, message: str) -> HTTPResponse:
        """Create a 401 Unauthorized response."""
        response = HTTPResponse(
            status_code=401,
            body=f'{{"error": "{message}"}}'.encode(),
            **{"continue": False},
        )
        response.headers["Content-Type"] = "application/json"
        response.headers["WWW-Authenticate"] = "Bearer"
        return response


if __name__ == "__main__":
    asyncio.run(serve(AuthPlugin()))
