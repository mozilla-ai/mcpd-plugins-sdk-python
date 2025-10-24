# mcpd-plugins: Python SDK for Building mcpd Plugins

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)

A Python SDK for building plugins for the [mcpd](https://github.com/mozilla-ai/mcpd) plugin system. This SDK provides a simple, async-first API for creating gRPC-based plugins that can intercept and transform HTTP requests and responses.

## Features

- **Simple API**: Extend `BasePlugin` and override only the methods you need
- **Async/Await**: Full async support using Python's asyncio
- **Type Hints**: Complete type annotations for better IDE support
- **gRPC-based**: Built on grpcio with protocol buffers
- **Minimal Dependencies**: Only requires `grpcio` and `protobuf`
- **Comprehensive Examples**: Five example plugins demonstrating common patterns

## Installation

```bash
# Using uv (recommended)
uv add mcpd-plugins

# Using pip
pip install mcpd-plugins
```

## Quick Start

Here's a minimal plugin that adds a custom header to HTTP requests:

```python
import asyncio
import sys
from mcpd_plugins import BasePlugin, serve
from mcpd_plugins.v1.plugins.plugin_pb2 import (
    FLOW_REQUEST,
    Capabilities,
    HTTPRequest,
    HTTPResponse,
    Metadata,
)
from google.protobuf.empty_pb2 import Empty


class MyPlugin(BasePlugin):
    async def GetMetadata(self, request: Empty, context) -> Metadata:
        return Metadata(
            name="my-plugin",
            version="1.0.0",
            description="Adds a custom header to requests"
        )

    async def GetCapabilities(self, request: Empty, context) -> Capabilities:
        return Capabilities(flows=[FLOW_REQUEST])

    async def HandleRequest(self, request: HTTPRequest, context) -> HTTPResponse:
        response = HTTPResponse(**{"continue": True})
        response.modified_request.CopyFrom(request)
        response.modified_request.headers["X-My-Plugin"] = "processed"
        return response


if __name__ == "__main__":
    # Pass sys.argv for mcpd compatibility (handles --address and --network flags)
    asyncio.run(serve(MyPlugin(), sys.argv))
```

Run your plugin:

```bash
# For mcpd (with --address and --network arguments)
python my_plugin.py --address /tmp/my-plugin.sock --network unix

# For standalone testing (defaults to TCP port 50051)
python my_plugin.py
```

When running under mcpd, the `--address` and `--network` flags are required and automatically passed by mcpd. For standalone testing without arguments, the plugin defaults to TCP on port 50051.

## Core Concepts

### BasePlugin

The `BasePlugin` class provides default implementations for all plugin methods:

- `Configure()` - Initialize plugin with configuration
- `Stop()` - Clean up resources on shutdown
- `GetMetadata()` - Return plugin name, version, and description
- `GetCapabilities()` - Declare which flows the plugin supports
- `CheckHealth()` - Health check endpoint
- `CheckReady()` - Readiness check endpoint
- `HandleRequest()` - Process incoming HTTP requests
- `HandleResponse()` - Process outgoing HTTP responses

Override only the methods your plugin needs.

### Flows

Plugins can process two types of flows:

- **FLOW_REQUEST**: Intercept and modify incoming HTTP requests
- **FLOW_RESPONSE**: Intercept and modify outgoing HTTP responses

Declare your supported flows in `GetCapabilities()`.

### Request/Response Handling

When handling requests or responses, you can:

1. **Pass through unchanged**: Return `HTTPResponse(**{"continue": True})`
2. **Modify and continue**: Set `**{"continue": True}` and modify fields
3. **Reject**: Set `**{"continue": False}` with a status code and body

## Examples

The SDK includes five example plugins demonstrating common patterns:

### 1. Simple Plugin
Adds a custom header to all requests.

```bash
cd examples/simple_plugin
uv run python main.py
```

### 2. Auth Plugin
Validates Bearer token authentication and rejects unauthorized requests.

```bash
export AUTH_TOKEN="your-secret-token"
cd examples/auth_plugin
uv run python main.py
```

### 3. Logging Plugin
Logs HTTP request and response details for observability.

```bash
cd examples/logging_plugin
uv run python main.py
```

### 4. Rate Limit Plugin
Implements token bucket rate limiting per client IP.

```bash
cd examples/rate_limit_plugin
uv run python main.py
```

### 5. Transform Plugin
Transforms JSON request bodies by adding metadata fields.

```bash
cd examples/transform_plugin
uv run python main.py
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mozilla-ai/mcpd-plugins-sdk-python.git
cd mcpd-plugins-sdk-python

# Setup development environment
make setup
```

### Running Tests

```bash
# Run all tests
make test

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_base_plugin.py
```

### Linting

```bash
# Run all pre-commit hooks
make lint

# Run ruff directly
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Generating Protocol Buffers

The proto files are automatically generated from the [mcpd-proto](https://github.com/mozilla-ai/mcpd-proto) repository and committed to this repo. To regenerate:

```bash
make generate-protos
```

## API Reference

### BasePlugin

```python
class BasePlugin(PluginServicer):
    async def Configure(self, request: PluginConfig, context) -> Empty
    async def Stop(self, request: Empty, context) -> Empty
    async def GetMetadata(self, request: Empty, context) -> Metadata
    async def GetCapabilities(self, request: Empty, context) -> Capabilities
    async def CheckHealth(self, request: Empty, context) -> Empty
    async def CheckReady(self, request: Empty, context) -> Empty
    async def HandleRequest(self, request: HTTPRequest, context) -> HTTPResponse
    async def HandleResponse(self, request: HTTPResponse, context) -> HTTPResponse
```

### serve()

```python
async def serve(
    plugin: BasePlugin,
    args: Optional[list[str]] = None,  # Command-line arguments (typically sys.argv)
    max_workers: int = 10,
    grace_period: float = 5.0,
) -> None
```

**Parameters:**
- `plugin`: The plugin instance to serve
- `args`: Command-line arguments. When provided (e.g., `sys.argv`), enables mcpd compatibility by parsing `--address` and `--network` flags. When `None`, runs in standalone mode on TCP port 50051.
- `max_workers`: Maximum number of concurrent gRPC workers
- `grace_period`: Seconds to wait during graceful shutdown

**Command-line flags** (when `args` is provided):
- `--address`: gRPC address (socket path for unix, host:port for tcp) - **required**
- `--network`: Network type (`unix` or `tcp`) - defaults to `unix`

### Exceptions

- `PluginError` - Base exception for all plugin errors
- `ConfigurationError` - Configuration-related errors
- `ServerError` - Server startup/shutdown errors

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

For security issues, please see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [mcpd](https://github.com/mozilla-ai/mcpd) - The mcpd daemon
- [mcpd-proto](https://github.com/mozilla-ai/mcpd-proto) - Protocol buffer definitions
- [mcpd-plugins-sdk-go](https://github.com/mozilla-ai/mcpd-plugins-sdk-go) - Go SDK for plugins
- [mcpd-plugins-sdk-dotnet](https://github.com/mozilla-ai/mcpd-plugins-sdk-dotnet) - .NET SDK for plugins
- [mcpd-sdk-python](https://github.com/mozilla-ai/mcpd-sdk-python) - Python SDK for mcpd clients
