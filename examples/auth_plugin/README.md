# Auth Plugin Example

A plugin that validates Bearer token authentication for incoming HTTP requests.

## What it does

- Checks for the `Authorization` header in requests
- Validates that it contains a Bearer token
- Rejects requests with invalid or missing tokens (returns 401 Unauthorized)
- Allows valid requests to continue

## Running the example

```bash
# Set the expected token (optional, defaults to "secret-token-123")
export AUTH_TOKEN="my-secret-token"

# From the repository root
cd examples/auth_plugin
uv run python main.py
```

## Configuration

The plugin uses the `AUTH_TOKEN` environment variable to set the expected token (default: `secret-token-123`).

## Key concepts demonstrated

- Request validation and rejection
- Environment variable configuration
- Returning error responses with `continue_=False`
- Setting HTTP status codes and response bodies
- Using class initialization for plugin state
