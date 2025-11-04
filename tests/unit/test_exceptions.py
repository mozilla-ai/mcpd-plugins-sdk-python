"""Unit tests for exception classes."""

import pytest

from mcpd_plugins.exceptions import ConfigurationError, PluginError, ServerError


class TestPluginError:
    """Tests for PluginError base exception."""

    def test_plugin_error_inherits_from_exception(self):
        """PluginError should inherit from Exception."""
        assert issubclass(PluginError, Exception)

    def test_plugin_error_with_message(self):
        """PluginError should store error message."""
        error = PluginError("Test error message")
        assert str(error) == "Test error message"

    def test_plugin_error_can_be_raised(self):
        """PluginError should be raisable."""
        with pytest.raises(PluginError) as exc_info:
            raise PluginError("Test error")
        assert "Test error" in str(exc_info.value)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_inherits_from_plugin_error(self):
        """ConfigurationError should inherit from PluginError."""
        assert issubclass(ConfigurationError, PluginError)

    def test_configuration_error_with_message(self):
        """ConfigurationError should store error message."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"

    def test_configuration_error_can_be_caught_as_plugin_error(self):
        """ConfigurationError should be catchable as PluginError."""
        with pytest.raises(PluginError):
            raise ConfigurationError("Config error")


class TestServerError:
    """Tests for ServerError exception."""

    def test_server_error_inherits_from_plugin_error(self):
        """ServerError should inherit from PluginError."""
        assert issubclass(ServerError, PluginError)

    def test_server_error_with_message(self):
        """ServerError should store error message."""
        error = ServerError("Server startup failed")
        assert str(error) == "Server startup failed"

    def test_server_error_can_be_caught_as_plugin_error(self):
        """ServerError should be catchable as PluginError."""
        with pytest.raises(PluginError):
            raise ServerError("Server error")
