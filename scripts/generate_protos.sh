#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Script to download proto files from mcpd-proto and generate Python code.
# Generated files are committed to the repository for ease of use.

# Configuration
PROTO_VERSION="${PROTO_VERSION:-v0.0.3}"
PROTO_BASE_URL="https://raw.githubusercontent.com/mozilla-ai/mcpd-proto/${PROTO_VERSION}"
PROTO_FILE="plugins/v1/plugin.proto"
TMP_DIR="tmp"
PROTO_TMP_DIR="${TMP_DIR}/plugins"
OUTPUT_DIR="src/mcpd_plugins/v1/plugins"

echo "🔄 Generating protocol buffer files from mcpd-proto ${PROTO_VERSION}..."

# Create temp directory
mkdir -p "$PROTO_TMP_DIR"

# Download proto file
echo "📥 Downloading ${PROTO_FILE}..."
PROTO_URL="${PROTO_BASE_URL}/${PROTO_FILE}"
if ! curl -fsSL "$PROTO_URL" -o "${PROTO_TMP_DIR}/plugin.proto"; then
  echo "❌ Failed to download proto file from: ${PROTO_URL}"
  echo "   Please check the PROTO_VERSION (${PROTO_VERSION}) is valid."
  exit 1
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Generate Python code
echo "🔨 Generating Python code..."
uv run python -m grpc_tools.protoc \
    --proto_path="$TMP_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "${PROTO_TMP_DIR}/plugin.proto"

# Fix imports in generated files (grpc_tools generates incorrect relative imports)
echo "🔧 Fixing imports in generated files..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's/import plugin_pb2/from . import plugin_pb2/' "$OUTPUT_DIR/plugin_pb2_grpc.py"
else
    # Linux
    sed -i 's/import plugin_pb2/from . import plugin_pb2/' "$OUTPUT_DIR/plugin_pb2_grpc.py"
fi

# Create __init__.py files if they don't exist
touch "$OUTPUT_DIR/__init__.py"
touch "src/mcpd_plugins/v1/__init__.py"

echo "✅ Protocol buffer generation complete!"
echo "   Proto version: ${PROTO_VERSION}"
echo "   Generated files in: ${OUTPUT_DIR}"
echo "   - plugin_pb2.py"
echo "   - plugin_pb2_grpc.py"
echo ""
echo "To use a different proto version, set PROTO_VERSION environment variable:"
echo "  PROTO_VERSION=v0.0.4 ./scripts/generate_protos.sh"
