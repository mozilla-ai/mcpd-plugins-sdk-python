# Simple Plugin Example

A minimal plugin that demonstrates basic functionality by adding a custom header to HTTP requests.

## What it does

- Implements the `HandleRequest` method to intercept incoming HTTP requests
- Adds a custom header `X-Simple-Plugin: processed` to all requests
- Passes the request through with `continue_=True`

## Running the example

```bash
# From the repository root
cd examples/simple_plugin
uv run python main.py
```

The plugin will start on port 50051 (or the port specified in `PLUGIN_PORT` environment variable).

## Key concepts demonstrated

- Extending `BasePlugin` class
- Implementing `GetMetadata()` to provide plugin information
- Implementing `GetCapabilities()` to declare supported flows
- Implementing `HandleRequest()` to process HTTP requests
- Using the `serve()` helper to launch the gRPC server
