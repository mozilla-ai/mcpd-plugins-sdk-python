"""Server helper functions for launching gRPC plugin servers."""

import argparse
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
    args: list[str] | None = None,
    max_workers: int = 10,
    grace_period: float = 5.0,
) -> None:
    """Launch a gRPC server for the plugin.

    This is a convenience function that handles server setup, signal handling,
    and graceful shutdown. It runs until interrupted by SIGTERM or SIGINT.

    When running under mcpd, the --address and --network flags are required and
    passed by mcpd. For standalone testing, omit these flags and the server will
    default to TCP on port 50051.

    Args:
        plugin: The plugin instance to serve (should extend BasePlugin).
        args: Command-line arguments (typically sys.argv). If None, runs in standalone
            mode on TCP port 50051. When provided by mcpd, expects --address and --network.
        max_workers: Maximum number of concurrent workers (default: 10).
        grace_period: Seconds to wait for graceful shutdown (default: 5.0).

    Raises:
        ServerError: If the server fails to start or encounters an error.

    Example:
        ```python
        import asyncio
        import sys
        from mcpd_plugins import BasePlugin, serve

        class MyPlugin(BasePlugin):
            async def GetMetadata(self, request, context):
                return Metadata(name="my-plugin", version="1.0.0")

        if __name__ == "__main__":
            # For mcpd: pass sys.argv to handle --address and --network
            asyncio.run(serve(MyPlugin(), sys.argv))

            # For standalone testing: omit args to use TCP :50051
            # asyncio.run(serve(MyPlugin()))
        ```
    """
    # Parse command-line arguments if provided.
    if args is not None:
        parser = argparse.ArgumentParser(description="Plugin server for mcpd")
        parser.add_argument(
            "--address",
            type=str,
            required=False,
            help="gRPC address (socket path for unix, host:port for tcp)",
        )
        parser.add_argument(
            "--network",
            type=str,
            default="unix",
            choices=["unix", "tcp"],
            help="Network type (unix or tcp)",
        )
        parsed_args = parser.parse_args(args[1:])  # Skip program name.

        # Require --address when args are provided (mcpd mode).
        if parsed_args.address is None:
            raise ServerError(
                "--address is required when running with command-line arguments. "
                "For standalone testing, call serve() without args."
            )

        address = parsed_args.address
        network = parsed_args.network
    else:
        # Standalone mode: use TCP with default port.
        network = "tcp"
        port = int(os.getenv("PLUGIN_PORT", "50051"))
        address = f"[::]:{port}"

    # Format the listen address based on network type.
    listen_addr = (
        f"unix:///{address}"  # Three slashes for Unix sockets.
        if network == "unix"
        else address
        if ":" in address
        else f"[::]:{address}"
    )

    server = aio.server()
    add_PluginServicer_to_server(plugin, server)

    try:
        result = server.add_insecure_port(listen_addr)
        if result == 0:
            raise ServerError(f"Failed to bind to {listen_addr}")
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
