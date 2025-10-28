"""Server helper functions for launching gRPC plugin servers."""

import argparse
import asyncio
import logging
import os
import signal
import types
from pathlib import Path

from grpc import aio

from mcpd_plugins.base_plugin import BasePlugin
from mcpd_plugins.exceptions import ServerError
from mcpd_plugins.v1.plugins.plugin_pb2_grpc import add_PluginServicer_to_server

logger = logging.getLogger(__name__)

# Network type constants.
NETWORK_UNIX = "unix"
NETWORK_TCP = "tcp"


def _cleanup_unix_socket(network: str, address: str, *, raise_on_error: bool = False) -> None:
    """Clean up Unix socket file if it exists.

    Args:
        network: Network type (unix or tcp).
        address: Socket file path.
        raise_on_error: If True, raise ServerError on cleanup failure. If False, log warning.
    """
    if network != NETWORK_UNIX:
        return

    try:
        socket_path = Path(address)
        if socket_path.exists():
            socket_path.unlink()
    except OSError as e:
        if raise_on_error:
            raise ServerError(f"Failed to prepare unix socket {address}: {e}") from e
        logger.warning("Failed to unlink unix socket: %s", address)


async def serve(
    plugin: BasePlugin,
    args: list[str] | None = None,
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
    # Parse command-line arguments if provided (and there are actual arguments beyond program name).
    if args is not None and len(args) > 1:
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
            default=NETWORK_UNIX,
            choices=[NETWORK_UNIX, NETWORK_TCP],
            help="Network type (unix or tcp)",
        )
        # Be tolerant of extra flags passed by hosts (e.g. mcpd).
        parsed_args, _unknown = parser.parse_known_args(args[1:])  # Skip program name.
        if _unknown:
            logger.debug("Ignoring unknown args: %s", _unknown)

        # Require --address when args are provided (mcpd mode).
        if parsed_args.address is None:
            raise ServerError(
                "--address is required when running with command-line arguments. "
                "For standalone testing, run without arguments."
            )

        address = parsed_args.address
        network = parsed_args.network
    else:
        # Standalone mode: use TCP with default port.
        network = NETWORK_TCP
        port = int(os.getenv("PLUGIN_PORT", "50051"))
        address = f"[::]:{port}"

    # Format the listen address based on network type.
    listen_addr = (
        f"unix:///{address}"  # Three slashes for Unix sockets.
        if network == NETWORK_UNIX
        else address
        if ":" in address
        else f"[::]:{address}"
    )

    # If using a Unix socket, remove any stale socket file before binding.
    _cleanup_unix_socket(network, address, raise_on_error=True)

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

    def signal_handler(signum: int, frame: types.FrameType | None) -> None:  # noqa: ARG001
        """Handle shutdown signals."""
        logger.info("Received signal %s, initiating graceful shutdown...", signum)
        stop_event.set()

    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGTERM, signal_handler, signal.SIGTERM, None)
        loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT, None)
    except (NotImplementedError, RuntimeError):
        # Fallback (e.g., on Windows or non-main thread).
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    # Start the server.
    try:
        await server.start()
        logger.info("Plugin server started on %s", listen_addr)

        # Wait for shutdown signal.
        await stop_event.wait()

        # Graceful shutdown.
        logger.info("Shutting down server (grace period: %ss)...", grace_period)
        await server.stop(grace_period)
        logger.info("Server stopped gracefully")
        _cleanup_unix_socket(network, address)

    except Exception as e:
        logger.exception("Server error")
        await server.stop(0)
        _cleanup_unix_socket(network, address)
        raise ServerError(f"Server encountered an error: {e}") from e
