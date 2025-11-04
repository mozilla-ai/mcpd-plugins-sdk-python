"""Unit tests for server module."""

import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpd_plugins.base_plugin import BasePlugin
from mcpd_plugins.exceptions import ServerError
from mcpd_plugins.server import serve


@pytest.fixture
def mock_plugin():
    """Provide a mock plugin instance."""
    return MagicMock(spec=BasePlugin)


@pytest.fixture
def mock_server():
    """Provide a mock gRPC server."""
    server = MagicMock()
    server.add_insecure_port = MagicMock(return_value=50051)
    server.start = AsyncMock()
    server.stop = AsyncMock()
    return server


@pytest.fixture
def mock_stop_event():
    """Provide a mock asyncio Event that immediately sets."""
    event = MagicMock(spec=asyncio.Event)
    event.wait = AsyncMock()
    event.set = MagicMock()
    return event


class TestServeStandaloneMode:
    """Tests for serve function in standalone mode (no args)."""

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_standalone_uses_default_port_50051(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Standalone mode should default to port 50051 on TCP."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin)

        # Verify server was created and bound to correct address
        mock_aio_server.assert_called_once()
        mock_add_servicer.assert_called_once_with(mock_plugin, mock_server)
        mock_server.add_insecure_port.assert_called_once_with("[::]:50051")

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_standalone_respects_plugin_port_env(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
        monkeypatch,
    ):
        """Standalone mode should use PLUGIN_PORT environment variable when set."""
        monkeypatch.setenv("PLUGIN_PORT", "9999")
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin)

        mock_server.add_insecure_port.assert_called_once_with("[::]:9999")

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_standalone_formats_address_correctly(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Standalone mode should format address as [::]:port."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin, args=None)

        # Verify IPv6 wildcard format
        call_args = mock_server.add_insecure_port.call_args[0][0]
        assert call_args.startswith("[::]:")


class TestServeMcpdMode:
    """Tests for serve function in mcpd mode (with args)."""

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_mcpd_mode_parses_address_and_network(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
        tmp_path,
    ):
        """mcpd mode should parse --address and --network flags."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        socket_path = str(tmp_path / "plugin.sock")
        await serve(mock_plugin, args=["program", "--address", socket_path, "--network", "unix"])

        # Note: unix:/// + socket_path = unix:///<socket_path> (4 slashes for absolute paths)
        mock_server.add_insecure_port.assert_called_once_with(f"unix:///{socket_path}")

    @pytest.mark.asyncio
    async def test_mcpd_mode_requires_address(self, mock_plugin):
        """mcpd mode should raise ServerError if --address not provided."""
        with pytest.raises(ServerError, match="--address is required"):
            await serve(mock_plugin, args=["program", "--network", "tcp"])

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_mcpd_mode_defaults_network_to_unix(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
        tmp_path,
    ):
        """mcpd mode should default network to unix when not specified."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        socket_path = str(tmp_path / "plugin.sock")
        await serve(mock_plugin, args=["program", "--address", socket_path])

        # Should use unix:// prefix (default network)
        call_args = mock_server.add_insecure_port.call_args[0][0]
        assert call_args.startswith("unix:///")

    @pytest.mark.asyncio
    async def test_mcpd_mode_validates_network_choices(self, mock_plugin):
        """mcpd mode should only accept unix or tcp for --network."""
        with pytest.raises(SystemExit):  # argparse raises SystemExit for invalid choice
            await serve(mock_plugin, args=["program", "--address", "addr", "--network", "invalid"])


class TestAddressFormatting:
    """Tests for address formatting logic."""

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_unix_socket_address_format(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
        tmp_path,
    ):
        """Unix socket should format as unix:///{path} - results in 4 slashes for absolute paths."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        socket_path = str(tmp_path / "plugin.sock")
        await serve(mock_plugin, args=["program", "--address", socket_path, "--network", "unix"])

        # unix:/// prefix + socket_path = unix:///<socket_path> (4 slashes for absolute paths)
        mock_server.add_insecure_port.assert_called_once_with(f"unix:///{socket_path}")

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_tcp_address_with_colon_passthrough(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """TCP address with colon should be used as-is."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin, args=["program", "--address", "localhost:8080", "--network", "tcp"])

        mock_server.add_insecure_port.assert_called_once_with("localhost:8080")

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_tcp_address_without_colon_wraps(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """TCP port-only address should be wrapped as [::]:port."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin, args=["program", "--address", "8080", "--network", "tcp"])

        mock_server.add_insecure_port.assert_called_once_with("[::]:8080")


class TestServerBinding:
    """Tests for server creation and binding."""

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_server_creation_and_binding(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Server should be created and servicer added."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin)

        # Verify proper call sequence
        mock_aio_server.assert_called_once()
        mock_add_servicer.assert_called_once_with(mock_plugin, mock_server)
        mock_server.add_insecure_port.assert_called_once()

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    async def test_bind_failure_returns_zero(self, mock_add_servicer, mock_aio_server, mock_plugin, mock_server):
        """Should raise ServerError when add_insecure_port returns 0."""
        mock_server.add_insecure_port.return_value = 0
        mock_aio_server.return_value = mock_server

        with pytest.raises(ServerError, match=r"Failed to bind"):
            await serve(mock_plugin)

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    async def test_bind_failure_raises_exception(self, mock_add_servicer, mock_aio_server, mock_plugin, mock_server):
        """Should raise ServerError when add_insecure_port raises exception."""
        mock_server.add_insecure_port.side_effect = OSError("Address already in use")
        mock_aio_server.return_value = mock_server

        with pytest.raises(ServerError, match=r"Failed to bind.*Address already in use"):
            await serve(mock_plugin)


class TestSignalHandlers:
    """Tests for signal handler registration."""

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.asyncio.Event")
    @patch("mcpd_plugins.server.asyncio.get_running_loop")
    async def test_registers_signal_handlers_via_loop(
        self,
        mock_get_loop,
        mock_event_class,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Should register SIGTERM and SIGINT handlers via loop.add_signal_handler (primary path)."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        # Mock the event loop.
        mock_loop = MagicMock()
        mock_loop.add_signal_handler = MagicMock()
        mock_get_loop.return_value = mock_loop

        await serve(mock_plugin)

        # Verify both signal handlers were registered via loop.
        assert mock_loop.add_signal_handler.call_count == 2
        signal_calls = [call_args[0][0] for call_args in mock_loop.add_signal_handler.call_args_list]
        assert signal.SIGTERM in signal_calls
        assert signal.SIGINT in signal_calls

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    @patch("mcpd_plugins.server.asyncio.get_running_loop")
    async def test_registers_signal_handlers_fallback(
        self,
        mock_get_loop,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Should fall back to signal.signal when loop.add_signal_handler fails (e.g., Windows)."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        # Mock the event loop to raise NotImplementedError (simulates Windows or non-main thread).
        mock_loop = MagicMock()
        mock_loop.add_signal_handler = MagicMock(side_effect=NotImplementedError)
        mock_get_loop.return_value = mock_loop

        await serve(mock_plugin)

        # Verify both signal handlers were registered via signal.signal fallback.
        assert mock_signal.call_count == 2
        signal_calls = [call_args[0][0] for call_args in mock_signal.call_args_list]
        assert signal.SIGTERM in signal_calls
        assert signal.SIGINT in signal_calls


class TestServerLifecycle:
    """Tests for server startup, shutdown, and error handling."""

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_server_starts_and_stops_gracefully(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Server should start, wait for stop event, then stop with grace period."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_stop_event.wait = AsyncMock()

        await serve(mock_plugin, grace_period=10.0)

        # Verify lifecycle calls
        mock_server.start.assert_called_once()
        mock_stop_event.wait.assert_called_once()
        mock_server.stop.assert_called_once_with(10.0)

    @pytest.mark.asyncio
    @patch("mcpd_plugins.server.aio.server")
    @patch("mcpd_plugins.server.add_PluginServicer_to_server")
    @patch("mcpd_plugins.server.signal.signal")
    @patch("mcpd_plugins.server.asyncio.Event")
    async def test_server_error_handling(
        self,
        mock_event_class,
        mock_signal,
        mock_add_servicer,
        mock_aio_server,
        mock_plugin,
        mock_server,
        mock_stop_event,
    ):
        """Server should handle exceptions during startup and call stop(0)."""
        mock_aio_server.return_value = mock_server
        mock_event_class.return_value = mock_stop_event
        mock_server.start.side_effect = RuntimeError("Server startup failed")

        with pytest.raises(ServerError, match="Server encountered an error"):
            await serve(mock_plugin)

        # Verify stop(0) was called for immediate shutdown
        mock_server.stop.assert_called_once_with(0)
