"""BasePlugin class providing default implementations for all plugin methods."""

from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext

from mcpd_plugins.v1.plugins.plugin_pb2 import (
    Capabilities,
    HTTPRequest,
    HTTPResponse,
    Metadata,
    PluginConfig,
)
from mcpd_plugins.v1.plugins.plugin_pb2_grpc import PluginServicer


class BasePlugin(PluginServicer):
    """Base class for mcpd plugins with sensible default implementations.

    Developers should extend this class and override only the methods they need.
    All methods are async (using async/await pattern) to support asynchronous operations.

    Example:
        ```python
        class MyPlugin(BasePlugin):
            async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
                return Metadata(
                    name="my-plugin",
                    version="1.0.0",
                    description="My custom plugin"
                )

            async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
                # Process the request
                response = HTTPResponse(**{"continue": True})
                response.headers["X-My-Plugin"] = "processed"
                return response
        ```
    """

    async def Configure(self, request: PluginConfig, context: ServicerContext) -> Empty:
        """Configure the plugin with the provided settings.

        Default implementation does nothing. Override to handle configuration.

        Args:
            request: Configuration settings from the host.
            context: gRPC context for the request.

        Returns:
            Empty message indicating successful configuration.
        """
        _ = (request, context)  # Required by gRPC interface.
        return Empty()

    async def Stop(self, request: Empty, context: ServicerContext) -> Empty:
        """Stop the plugin and clean up resources.

        Default implementation does nothing. Override to handle cleanup.

        Args:
            request: Empty request message.
            context: gRPC context for the request.

        Returns:
            Empty message indicating successful shutdown.
        """
        _ = (request, context)  # Required by gRPC interface.
        return Empty()

    async def GetMetadata(self, request: Empty, context: ServicerContext) -> Metadata:
        """Get plugin metadata (name, version, description).

        Default implementation returns basic metadata. Override to provide actual values.

        Args:
            request: Empty request message.
            context: gRPC context for the request.

        Returns:
            Metadata containing plugin information.
        """
        _ = (request, context)  # Required by gRPC interface.
        return Metadata(
            name="base-plugin",
            version="0.0.0",
            description="Base plugin implementation",
        )

    async def GetCapabilities(self, request: Empty, context: ServicerContext) -> Capabilities:
        """Get plugin capabilities (supported flows).

        Default implementation returns no capabilities. Must override to declare supported flows.

        Args:
            request: Empty request message.
            context: gRPC context for the request.

        Returns:
            Capabilities message listing supported flows.
        """
        _ = (request, context)  # Required by gRPC interface.
        return Capabilities()

    async def CheckHealth(self, request: Empty, context: ServicerContext) -> Empty:
        """Health check endpoint.

        Default implementation returns healthy status. Override if custom health checks needed.

        Args:
            request: Empty request message.
            context: gRPC context for the request.

        Returns:
            Empty message indicating healthy status.
        """
        _ = (request, context)  # Required by gRPC interface.
        return Empty()

    async def CheckReady(self, request: Empty, context: ServicerContext) -> Empty:
        """Readiness check endpoint.

        Default implementation returns ready status. Override if custom readiness checks needed.

        Args:
            request: Empty request message.
            context: gRPC context for the request.

        Returns:
            Empty message indicating ready status.
        """
        _ = (request, context)  # Required by gRPC interface.
        return Empty()

    async def HandleRequest(self, request: HTTPRequest, context: ServicerContext) -> HTTPResponse:
        """Handle incoming HTTP request.

        Default implementation passes through unchanged (continue=True).

        Args:
            request: The incoming HTTP request to process.
            context: gRPC context for the request.

        Returns:
            HTTPResponse indicating how to proceed (continue, modify, or reject).
        """
        _ = context  # Required by gRPC interface.
        return HTTPResponse(**{"continue": True})

    async def HandleResponse(self, response: HTTPResponse, context: ServicerContext) -> HTTPResponse:
        """Handle outgoing HTTP response.

        Default implementation passes through unchanged (continue=True).

        Note:
            The parameter is named 'response' for clarity, even though the generated
            gRPC stub names it 'request' (gRPC convention). This semantic naming
            improves code readability.

        Args:
            response: The outgoing HTTP response to process.
            context: gRPC context for the request.

        Returns:
            HTTPResponse indicating how to proceed (continue or modify).
        """
        _ = context  # Required by gRPC interface.
        return HTTPResponse(**{"continue": True})
