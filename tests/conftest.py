"""Pytest configuration and shared fixtures."""

import pytest
from google.protobuf.empty_pb2 import Empty
from grpc.aio import Metadata

from mcpd_plugins.v1.plugins.plugin_pb2 import HTTPRequest, PluginConfig


class AbortedError(Exception):
    """Exception raised when gRPC context abort is called."""

    def __init__(self, code, details: str) -> None:
        """Initialize with gRPC status code and details.

        Args:
            code: gRPC status code.
            details: Error details message.
        """
        self.code = code
        self.details = details
        super().__init__(f"Aborted with code {code}: {details}")


class MockContext:
    """Mock gRPC ServicerContext for testing."""

    def __init__(self) -> None:
        """Initialize mock context."""
        self.invocation_metadata = Metadata()
        self.peer_identity = None
        self.code = None
        self.details = None

    def set_code(self, code) -> None:
        """Set the gRPC status code.

        Args:
            code: gRPC status code.
        """
        self.code = code

    def set_details(self, details: str) -> None:
        """Set the error details.

        Args:
            details: Error details message.
        """
        self.details = details

    def abort(self, code, details: str):
        """Mock abort method.

        Args:
            code: gRPC status code.
            details: Error details message.

        Raises:
            AbortedError: Always raised to simulate gRPC abort.
        """
        self.code = code
        self.details = details
        raise AbortedError(code, details)


@pytest.fixture
def mock_context():
    """Provide a mock gRPC context for testing."""
    return MockContext()


@pytest.fixture
def empty_request():
    """Provide an Empty request message."""
    return Empty()


@pytest.fixture
def sample_plugin_config():
    """Provide a sample plugin configuration."""
    config = PluginConfig()
    config.custom_config["key1"] = "value1"
    config.custom_config["key2"] = "value2"
    return config


@pytest.fixture
def sample_http_request():
    """Provide a sample HTTP request."""
    request = HTTPRequest(
        method="GET",
        url="https://example.com/api/test",
        path="/api/test",
        remote_addr="192.168.1.100",
        request_uri="/api/test?foo=bar",
    )
    request.headers["User-Agent"] = "test-client/1.0"
    request.headers["Content-Type"] = "application/json"
    return request


@pytest.fixture
def sample_http_request_with_body():
    """Provide a sample HTTP request with body."""
    request = HTTPRequest(
        method="POST",
        url="https://example.com/api/test",
        path="/api/test",
        body=b'{"test": "data"}',
        remote_addr="192.168.1.100",
    )
    request.headers["Content-Type"] = "application/json"
    request.headers["Content-Length"] = "16"
    return request
