"""Integration tests for example plugins."""

import sys
from pathlib import Path

import pytest
from google.protobuf.empty_pb2 import Empty

# Add examples to path.
examples_dir = Path(__file__).parent.parent.parent / "examples"
sys.path.insert(0, str(examples_dir))


class TestSimplePlugin:
    """Integration tests for simple_plugin example."""

    @pytest.mark.asyncio
    async def test_simple_plugin_metadata(self, mock_context):
        """Simple plugin should return correct metadata."""
        from simple_plugin.main import SimplePlugin

        plugin = SimplePlugin()
        metadata = await plugin.GetMetadata(Empty(), mock_context)

        assert metadata.name == "simple-plugin"
        assert metadata.version == "1.0.0"
        assert "custom header" in metadata.description.lower()

    @pytest.mark.asyncio
    async def test_simple_plugin_capabilities(self, mock_context):
        """Simple plugin should declare REQUEST flow."""
        from simple_plugin.main import SimplePlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import FLOW_REQUEST

        plugin = SimplePlugin()
        capabilities = await plugin.GetCapabilities(Empty(), mock_context)

        assert len(capabilities.flows) == 1
        assert capabilities.flows[0] == FLOW_REQUEST

    @pytest.mark.asyncio
    async def test_simple_plugin_adds_header(self, mock_context):
        """Simple plugin should add X-Simple-Plugin header."""
        from simple_plugin.main import SimplePlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import HTTPRequest

        plugin = SimplePlugin()
        request = HTTPRequest(
            method="GET",
            url="https://example.com/test",
            path="/test",
        )
        request.headers["User-Agent"] = "test"

        response = await plugin.HandleRequest(request, mock_context)

        assert getattr(response, "continue") is True
        assert "X-Simple-Plugin" in response.modified_request.headers
        assert response.modified_request.headers["X-Simple-Plugin"] == "processed"


class TestAuthPlugin:
    """Integration tests for auth_plugin example."""

    @pytest.mark.asyncio
    async def test_auth_plugin_rejects_missing_token(self, mock_context):
        """Auth plugin should reject requests without Authorization header."""
        from auth_plugin.main import AuthPlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import HTTPRequest

        plugin = AuthPlugin()
        request = HTTPRequest(
            method="GET",
            url="https://example.com/test",
            path="/test",
        )

        response = await plugin.HandleRequest(request, mock_context)

        assert getattr(response, "continue") is False
        assert response.status_code == 401
        assert response.headers.get("Content-Type") == "application/json"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"].startswith("Bearer")
        assert b"error" in response.body

    @pytest.mark.asyncio
    async def test_auth_plugin_rejects_invalid_token(self, mock_context):
        """Auth plugin should reject requests with invalid token."""
        from auth_plugin.main import AuthPlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import HTTPRequest

        plugin = AuthPlugin()
        request = HTTPRequest(
            method="GET",
            url="https://example.com/test",
            path="/test",
        )
        request.headers["Authorization"] = "Bearer wrong-token"

        response = await plugin.HandleRequest(request, mock_context)

        assert getattr(response, "continue") is False
        assert response.status_code == 401
        assert response.headers.get("Content-Type") == "application/json"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"].startswith("Bearer")
        assert b"error" in response.body

    @pytest.mark.asyncio
    async def test_auth_plugin_accepts_valid_token(self, mock_context):
        """Auth plugin should accept requests with valid token."""
        from auth_plugin.main import AuthPlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import HTTPRequest

        plugin = AuthPlugin()
        request = HTTPRequest(
            method="GET",
            url="https://example.com/test",
            path="/test",
        )
        request.headers["Authorization"] = "Bearer secret-token-123"

        response = await plugin.HandleRequest(request, mock_context)

        assert getattr(response, "continue") is True


class TestLoggingPlugin:
    """Integration tests for logging_plugin example."""

    @pytest.mark.asyncio
    async def test_logging_plugin_supports_both_flows(self, mock_context):
        """Logging plugin should support both REQUEST and RESPONSE flows."""
        from logging_plugin.main import LoggingPlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import FLOW_REQUEST, FLOW_RESPONSE

        plugin = LoggingPlugin()
        capabilities = await plugin.GetCapabilities(Empty(), mock_context)

        assert len(capabilities.flows) == 2
        assert FLOW_REQUEST in capabilities.flows
        assert FLOW_RESPONSE in capabilities.flows

    @pytest.mark.asyncio
    async def test_logging_plugin_logs_request(self, mock_context, caplog):
        """Logging plugin should log request details."""
        from logging_plugin.main import LoggingPlugin

        from mcpd_plugins.v1.plugins.plugin_pb2 import HTTPRequest

        plugin = LoggingPlugin()
        request = HTTPRequest(
            method="GET",
            url="https://example.com/test",
            path="/test",
        )

        response = await plugin.HandleRequest(request, mock_context)

        assert getattr(response, "continue") is True
        # Check that logging occurred (test output capture).
        assert "INCOMING REQUEST" in caplog.text
