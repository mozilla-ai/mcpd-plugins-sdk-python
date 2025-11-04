# Logging Plugin Example

A plugin that logs HTTP request and response details for observability and debugging.

## What it does

- Logs details of incoming HTTP requests (method, URL, headers, body size)
- Logs details of outgoing HTTP responses (status code, headers, body size)
- Redacts sensitive headers (Authorization, Cookie) for security
- Supports both REQUEST and RESPONSE flows

## Running the example

```bash
# From the repository root
cd examples/logging_plugin
uv run python main.py
```

## Key concepts demonstrated

- Implementing both `HandleRequest()` and `HandleResponse()` methods
- Declaring multiple flows in `GetCapabilities()`
- Structured logging for observability
- Handling sensitive data (header redaction)
- Pass-through behavior while gathering telemetry

## Building

See [BUILD.md](../../BUILD.md) for complete instructions on building standalone executables.

Quick build:

```bash
# Development build with PyInstaller (fast)
make build-plugin PLUGIN=examples/logging_plugin

# Production build with Nuitka (optimized)
make build-plugin-prod PLUGIN=examples/logging_plugin

# Run the executable
./dist/logging_plugin
```
