"""Unit tests for BasePlugin class."""

import pytest
from google.protobuf.empty_pb2 import Empty

from mcpd_plugins import BasePlugin
from mcpd_plugins.v1.plugins.plugin_pb2 import (
    Capabilities,
    HTTPResponse,
    Metadata,
)


class TestBasePlugin:
    """Tests for BasePlugin default implementations."""

    @pytest.fixture
    def plugin(self):
        """Create a BasePlugin instance for testing."""
        return BasePlugin()

    @pytest.mark.asyncio
    async def test_configure_returns_empty(self, plugin, sample_plugin_config, mock_context):
        """Configure should return Empty by default."""
        result = await plugin.Configure(sample_plugin_config, mock_context)
        assert isinstance(result, Empty)

    @pytest.mark.asyncio
    async def test_stop_returns_empty(self, plugin, empty_request, mock_context):
        """Stop should return Empty by default."""
        result = await plugin.Stop(empty_request, mock_context)
        assert isinstance(result, Empty)

    @pytest.mark.asyncio
    async def test_get_metadata_returns_metadata(self, plugin, empty_request, mock_context):
        """GetMetadata should return Metadata with default values."""
        result = await plugin.GetMetadata(empty_request, mock_context)
        assert isinstance(result, Metadata)
        assert result.name == "base-plugin"
        assert result.version == "0.0.0"
        assert result.description == "Base plugin implementation"

    @pytest.mark.asyncio
    async def test_get_capabilities_returns_empty_capabilities(self, plugin, empty_request, mock_context):
        """GetCapabilities should return empty Capabilities by default."""
        result = await plugin.GetCapabilities(empty_request, mock_context)
        assert isinstance(result, Capabilities)
        assert len(result.flows) == 0

    @pytest.mark.asyncio
    async def test_check_health_returns_empty(self, plugin, empty_request, mock_context):
        """CheckHealth should return Empty by default."""
        result = await plugin.CheckHealth(empty_request, mock_context)
        assert isinstance(result, Empty)

    @pytest.mark.asyncio
    async def test_check_ready_returns_empty(self, plugin, empty_request, mock_context):
        """CheckReady should return Empty by default."""
        result = await plugin.CheckReady(empty_request, mock_context)
        assert isinstance(result, Empty)

    @pytest.mark.asyncio
    async def test_handle_request_passes_through(self, plugin, sample_http_request, mock_context):
        """HandleRequest should return continue=True by default."""
        result = await plugin.HandleRequest(sample_http_request, mock_context)
        assert isinstance(result, HTTPResponse)
        assert getattr(result, "continue") is True

    @pytest.mark.asyncio
    async def test_handle_response_passes_through(self, plugin, mock_context):
        """HandleResponse should return continue=True by default."""
        http_response = HTTPResponse(status_code=200, **{"continue": True})
        result = await plugin.HandleResponse(http_response, mock_context)
        assert isinstance(result, HTTPResponse)
        assert getattr(result, "continue") is True


class TestCustomPlugin:
    """Tests for custom plugin that overrides methods."""

    class CustomPlugin(BasePlugin):
        """Custom plugin for testing overrides."""

        async def GetMetadata(self, request, context):
            """Override with custom metadata."""
            return Metadata(
                name="custom-plugin",
                version="1.2.3",
                description="Custom test plugin",
            )

        async def HandleRequest(self, request, context):
            """Override to add custom header."""
            response = HTTPResponse(**{"continue": True})
            response.headers["X-Custom"] = "test"
            return response

    @pytest.fixture
    def custom_plugin(self):
        """Create a custom plugin instance for testing."""
        return self.CustomPlugin()

    @pytest.mark.asyncio
    async def test_custom_get_metadata(self, custom_plugin, empty_request, mock_context):
        """Custom GetMetadata should return overridden values."""
        result = await custom_plugin.GetMetadata(empty_request, mock_context)
        assert result.name == "custom-plugin"
        assert result.version == "1.2.3"
        assert result.description == "Custom test plugin"

    @pytest.mark.asyncio
    async def test_custom_handle_request(self, custom_plugin, sample_http_request, mock_context):
        """Custom HandleRequest should add custom header."""
        result = await custom_plugin.HandleRequest(sample_http_request, mock_context)
        assert getattr(result, "continue") is True
        assert result.headers["X-Custom"] == "test"
