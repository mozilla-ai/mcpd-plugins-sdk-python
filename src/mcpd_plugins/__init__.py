"""mcpd-plugins: Python SDK for building mcpd plugins.

This SDK provides a simple way to create plugins for the mcpd plugin system using gRPC.
Plugins extend the BasePlugin class and override only the methods they need.

Example:
    ```python
    import asyncio
    from mcpd_plugins import BasePlugin, serve
    from mcpd_plugins.v1.plugins.plugin_pb2 import Capabilities, Flow, Metadata

    class MyPlugin(BasePlugin):
        async def GetMetadata(self, request, context):
            return Metadata(
                name="my-plugin",
                version="1.0.0",
                description="A simple example plugin"
            )

        async def GetCapabilities(self, request, context):
            return Capabilities(flows=[Flow.FLOW_REQUEST])

        async def HandleRequest(self, request, context):
            # Add custom header
            response = HTTPResponse(**{"continue": True})
            response.headers["X-My-Plugin"] = "processed"
            return response

    if __name__ == "__main__":
        asyncio.run(serve(MyPlugin()))
    ```
"""

from mcpd_plugins.base_plugin import BasePlugin
from mcpd_plugins.exceptions import ConfigurationError, PluginError, ServerError
from mcpd_plugins.server import serve

try:
    from mcpd_plugins._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "BasePlugin",
    "serve",
    "PluginError",
    "ConfigurationError",
    "ServerError",
    "__version__",
]
