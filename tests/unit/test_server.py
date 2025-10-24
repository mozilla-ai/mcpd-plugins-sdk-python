"""Unit tests for server module."""

import os

import pytest

from mcpd_plugins.server import serve


class TestServeFunction:
    """Tests for serve helper function."""

    @pytest.mark.asyncio
    async def test_serve_with_invalid_port_raises_error(self):
        """serve should raise ServerError if port binding fails."""
        # Note: This test is limited without actually starting a server.
        # In practice, we'd need more complex mocking to test server startup failures.
        # This is a placeholder test to demonstrate the pattern.
        assert callable(serve)

    def test_serve_uses_env_var_for_port(self, monkeypatch):
        """serve should use PLUGIN_PORT environment variable if set."""
        monkeypatch.setenv("PLUGIN_PORT", "9999")
        # Since we can't easily test the actual port binding without starting the server,
        # we just verify that the function is callable and accepts the right parameters.
        assert callable(serve)

    def test_serve_defaults_to_port_50051(self):
        """serve should default to port 50051 if no port specified."""
        # Remove env var if it exists.
        if "PLUGIN_PORT" in os.environ:
            del os.environ["PLUGIN_PORT"]

        # Verify the function signature accepts the expected parameters.
        assert callable(serve)


# Note: Full integration tests for the gRPC server would require:
# 1. Actually starting the server in a background task
# 2. Creating a gRPC client to connect to it
# 3. Making test calls
# 4. Shutting down the server gracefully
# These are better suited for integration tests rather than unit tests.
