# Rate Limit Plugin Example

A plugin that implements rate limiting using a token bucket algorithm to prevent clients from overwhelming the server.

## What it does

- Tracks requests per client IP address
- Limits each client to a configurable number of requests per minute (default: 60)
- Returns 429 Too Many Requests when limit is exceeded
- Adds rate limit headers to responses (`X-RateLimit-Limit`, `X-RateLimit-Remaining`)
- Includes `Retry-After` header when rate limit is exceeded

## Running the example

```bash
# From the repository root
cd examples/rate_limit_plugin
uv run python main.py
```

## Configuration

You can customize the rate limit by modifying the `requests_per_minute` parameter when creating the plugin:

```python
asyncio.run(serve(RateLimitPlugin(requests_per_minute=100)))
```

## Key concepts demonstrated

- Stateful plugin implementation (tracking client buckets)
- Token bucket algorithm for rate limiting
- Custom response headers
- Calculating and returning `Retry-After` header
- Per-client tracking using remote IP address
- Request rejection with appropriate HTTP status codes

## Building

See [BUILD.md](../../BUILD.md) for complete instructions on building standalone executables.

Quick build:

```bash
# Development build with PyInstaller (fast)
make build-plugin PLUGIN=examples/rate_limit_plugin

# Production build with Nuitka (optimized)
make build-plugin-prod PLUGIN=examples/rate_limit_plugin

# Run the executable
./dist/rate_limit_plugin
```
