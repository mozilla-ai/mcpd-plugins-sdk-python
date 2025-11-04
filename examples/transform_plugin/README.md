# Transform Plugin Example

A plugin that transforms JSON request bodies by adding metadata fields.

## What it does

- Intercepts POST/PUT/PATCH requests with JSON content
- Parses the JSON body
- Adds a `_metadata` field with plugin information and client IP
- Returns the modified request with updated Content-Length header
- Returns 400 Bad Request if JSON is invalid
- Passes through non-JSON requests unchanged

## Running the example

```bash
# From the repository root
cd examples/transform_plugin
uv run python main.py
```

## Example transformation

**Original request body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Transformed request body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "_metadata": {
    "processed_by": "transform-plugin",
    "version": "1.0.0",
    "client_ip": "192.168.1.100"
  }
}
```

## Key concepts demonstrated

- Request body modification
- JSON parsing and serialization
- Conditional processing based on HTTP method and Content-Type
- Error handling (returning 400 for invalid JSON)
- Updating Content-Length header after transformation
- Copying and modifying request fields

## Building

See [BUILD.md](../../BUILD.md) for complete instructions on building standalone executables.

Quick build:

```bash
# Development build with PyInstaller (fast)
make build-plugin PLUGIN=examples/transform_plugin

# Production build with Nuitka (optimized)
make build-plugin-prod PLUGIN=examples/transform_plugin

# Run the executable
./dist/transform_plugin
```
