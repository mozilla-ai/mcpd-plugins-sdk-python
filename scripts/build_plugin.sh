#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Script to build Python plugins into standalone executables
# Supports both PyInstaller (fast, for development) and Nuitka (optimized, for production)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
USE_NUITKA=false
DEBUG=false
ONEFILE=true  # Always build as single-file executable.
PLUGIN_DIR=""
PLUGIN_NAME=""
EXTRA_ARGS=()

# Print usage
usage() {
    cat << EOF
Usage: $(basename "$0") PLUGIN_DIR [OPTIONS]

Build a Python plugin into a standalone single-file executable.

Arguments:
    PLUGIN_DIR          Path to plugin directory (e.g., examples/simple_plugin)

Options:
    --pyinstaller       Use PyInstaller (default, fast builds)
    --nuitka            Use Nuitka (slower builds, better performance)
    --name NAME         Custom name for executable (default: directory name)
    --debug             Enable debug mode (console output)
    --optimize-size     Optimize for smaller size (Nuitka only)
    --optimize-speed    Optimize for speed (Nuitka only)
    --help              Show this help message

Examples:
    # Quick development build
    $(basename "$0") examples/simple_plugin

    # Production build with Nuitka
    $(basename "$0") examples/simple_plugin --nuitka

    # Custom name
    $(basename "$0") examples/auth_plugin --name auth-plugin-v1

EOF
    exit 1
}

# Parse arguments
if [[ $# -lt 1 ]]; then
    usage
fi

PLUGIN_DIR="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --pyinstaller)
            USE_NUITKA=false
            shift
            ;;
        --nuitka)
            USE_NUITKA=true
            shift
            ;;
        --name)
            PLUGIN_NAME="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --optimize-size|--optimize-speed)
            EXTRA_ARGS+=("$1")
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            ;;
    esac
done

# Validate plugin directory
if [[ ! -d "$PLUGIN_DIR" ]]; then
    echo -e "${RED}Error: Plugin directory not found: $PLUGIN_DIR${NC}"
    exit 1
fi

if [[ ! -f "$PLUGIN_DIR/main.py" ]]; then
    echo -e "${RED}Error: main.py not found in $PLUGIN_DIR${NC}"
    exit 1
fi

# Determine plugin name
if [[ -z "$PLUGIN_NAME" ]]; then
    PLUGIN_NAME=$(basename "$PLUGIN_DIR")
fi

echo -e "${GREEN}🔨 Building plugin: $PLUGIN_NAME${NC}"
echo -e "   Plugin directory: $PLUGIN_DIR"
echo -e "   Build tool: $([ "$USE_NUITKA" = true ] && echo "Nuitka" || echo "PyInstaller")"
echo ""

# Create dist directory
mkdir -p dist

if [[ "$USE_NUITKA" = true ]]; then
    # Build with Nuitka
    echo -e "${YELLOW}Building with Nuitka (this may take 5-30 minutes)...${NC}"

    NUITKA_ARGS=(
        --standalone
        --onefile
        --follow-imports
        --python-flag=no_site
        --output-dir=dist
        --output-filename="$PLUGIN_NAME"
    )

    # Add debug flag if requested
    if [[ "$DEBUG" = true ]]; then
        NUITKA_ARGS+=(--debug)
    fi

    # Add optimization flags
    for arg in "${EXTRA_ARGS[@]}"; do
        case $arg in
            --optimize-size)
                NUITKA_ARGS+=(--lto=yes)
                ;;
            --optimize-speed)
                NUITKA_ARGS+=(--lto=no)
                NUITKA_ARGS+=(--remove-output)
                ;;
        esac
    done

    # Include grpcio and protobuf data files
    NUITKA_ARGS+=(
        --include-package=grpc
        --include-package=google.protobuf
        --include-package-data=mcpd_plugins
    )

    uv run python -m nuitka "${NUITKA_ARGS[@]}" "$PLUGIN_DIR/main.py"

else
    # Build with PyInstaller
    echo -e "${YELLOW}Building with PyInstaller...${NC}"

    PYINSTALLER_ARGS=(
        --name="$PLUGIN_NAME"
        --distpath=dist
        --workpath=build
        --specpath=build
    )

    # Add debug/console flag
    if [[ "$DEBUG" = true ]]; then
        PYINSTALLER_ARGS+=(--console)
    else
        PYINSTALLER_ARGS+=(--console) # Plugins need console for gRPC
    fi

    # Onefile vs onedir
    if [[ "$ONEFILE" = true ]]; then
        PYINSTALLER_ARGS+=(--onefile)
    fi

    # Hidden imports for grpc and asyncio
    PYINSTALLER_ARGS+=(
        --hidden-import=grpc
        --hidden-import=grpc._cython.cygrpc
        --hidden-import=google.protobuf
        --hidden-import=asyncio
        --collect-all=grpc
        --copy-metadata=grpcio
        --copy-metadata=protobuf
    )

    uv run pyinstaller "${PYINSTALLER_ARGS[@]}" "$PLUGIN_DIR/main.py"
fi

echo ""
echo -e "${GREEN}✅ Build complete!${NC}"
echo -e "   Executable: dist/$PLUGIN_NAME"
echo ""
echo -e "To run your plugin:"
echo -e "   ${YELLOW}./dist/$PLUGIN_NAME${NC}"
echo ""
echo -e "To test with mcpd, see: https://github.com/mozilla-ai/mcpd"
