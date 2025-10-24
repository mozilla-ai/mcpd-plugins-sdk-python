"""Custom exception classes for mcpd-plugins SDK."""


class PluginError(Exception):
    """Base exception class for all plugin-related errors."""

    pass


class ConfigurationError(PluginError):
    """Exception raised for configuration-related errors."""

    pass


class ServerError(PluginError):
    """Exception raised for server startup or shutdown errors."""

    pass
