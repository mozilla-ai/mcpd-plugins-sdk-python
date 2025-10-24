"""Server helper functions for launching gRPC plugin servers."""

import asyncio
import logging
import os
import signal

from grpc import aio

from mcpd_plugins.base_plugin import BasePlugin
from mcpd_plugins.exceptions import ServerError
from mcpd_plugins.v1.plugins.plugin_pb2_grpc import add_PluginServicer_to_server

logger = logging.getLogger(__name__)


async def serve(
    plugin: BasePlugin,
    port: int | None = None,
    max_workers: int = 10,
    grace_period: float = 5.0,
) -> None:
    """Launch a gRPC server for the plugin.

    This is a convenience function that handles server setup, signal handling,
    and graceful shutdown. It runs until interrupted by SIGTERM or SIGINT.

    Args:
        plugin: The plugin instance to serve (should extend BasePlugin).
        port: Port to listen on. If None, uses PLUGIN_PORT env var or defaults to 50051.
        max_workers: Maximum number of concurrent workers (default: 10).
        grace_period: Seconds to wait for graceful shutdown (default: 5.0).

    Raises:
        ServerError: If the server fails to start or encounters an error.

    Example:
        ```python
        import asyncio
        from mcpd_plugins import BasePlugin, serve

        class MyPlugin(BasePlugin):
            async def GetMetadata(self, request, context):
                return Metadata(name="my-plugin", version="1.0.0")

        if __name__ == "__main__":
            asyncio.run(serve(MyPlugin()))
        ```
    """
    if port is None:
        port = int(os.getenv("PLUGIN_PORT", "50051"))

    server = aio.server()
    add_PluginServicer_to_server(plugin, server)

    listen_addr = f"[::]:{port}"
    try:
        server.add_insecure_port(listen_addr)
    except Exception as e:
        raise ServerError(f"Failed to bind to {listen_addr}: {e}") from e

    # Setup signal handling for graceful shutdown.
    stop_event = asyncio.Event()

    def signal_handler(signum: int, frame) -> None:  # noqa: ARG001
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        stop_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start the server.
    try:
        await server.start()
        logger.info(f"Plugin server started on {listen_addr}")

        # Wait for shutdown signal.
        await stop_event.wait()

        # Graceful shutdown.
        logger.info(f"Shutting down server (grace period: {grace_period}s)...")
        await server.stop(grace_period)
        logger.info("Server stopped gracefully")

    except Exception as e:
        logger.error(f"Server error: {e}")
        await server.stop(0)
        raise ServerError(f"Server encountered an error: {e}") from e
