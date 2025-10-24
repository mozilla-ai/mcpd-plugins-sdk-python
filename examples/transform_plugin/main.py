"""Content transformation plugin that modifies request bodies.

This example demonstrates how to transform request content, such as
modifying JSON payloads or adding default fields.
"""

import asyncio
import json
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


class TransformPlugin(BasePlugin):
    """Plugin that transforms JSON request bodies."""

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Return plugin metadata."""
        return Metadata(
            name="transform-plugin",
            version="1.0.0",
            description="Transforms JSON request bodies by adding metadata fields",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Declare support for request flow."""
        return Capabilities(flows=[FLOW_REQUEST])

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Transform JSON request bodies by adding metadata."""
        logger.info(f"Processing request: {request.method} {request.url}")

        # Only transform POST/PUT/PATCH requests with JSON content.
        content_type = request.headers.get("Content-Type", "")
        if request.method not in ("POST", "PUT", "PATCH") or "application/json" not in content_type:
            logger.info("Skipping non-JSON or non-mutating request")
            return HTTPResponse(**{"continue": True})

        # Try to parse and transform the JSON body.
        try:
            if not request.body:
                logger.info("Empty body, skipping transformation")
                return HTTPResponse(**{"continue": True})

            # Parse JSON.
            data = json.loads(request.body.decode("utf-8"))
            logger.info(f"Original payload: {data}")

            # Add metadata fields.
            if isinstance(data, dict):
                data["_metadata"] = {
                    "processed_by": "transform-plugin",
                    "version": "1.0.0",
                    "client_ip": request.remote_addr,
                }
                logger.info(f"Transformed payload: {data}")

                # Create modified request.
                modified_body = json.dumps(data).encode("utf-8")
                response = HTTPResponse(**{"continue": True})
                response.modified_request.CopyFrom(request)
                response.modified_request.body = modified_body

                # Update Content-Length header.
                response.modified_request.headers["Content-Length"] = str(len(modified_body))

                logger.info("Request body transformed successfully")
                return response
            else:
                logger.warning("JSON body is not a dict, skipping transformation")
                return HTTPResponse(**{"continue": True})

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON body: {e}")
            # Return 400 Bad Request for invalid JSON.
            return HTTPResponse(
                **{"continue": False},
                status_code=400,
                body=b'{"error": "Invalid JSON"}',
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            logger.error(f"Unexpected error during transformation: {e}")
            # Allow request to continue on unexpected errors.
            return HTTPResponse(**{"continue": True})


if __name__ == "__main__":
    asyncio.run(serve(TransformPlugin()))
