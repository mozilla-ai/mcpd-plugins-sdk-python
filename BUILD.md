# Building Plugin Executables

This guide explains how to build Python plugins into standalone single-file executables that can be used with [mcpd](https://github.com/mozilla-ai/mcpd).

## Why Build Executables?

`mcpd` requires plugins to be standalone executables that it can spawn as separate processes. Python plugins need to be packaged with their dependencies and the Python runtime into a single executable file.

## Prerequisites

Install build dependencies:

```bash
uv sync --group build
```

This installs both PyInstaller (for development) and Nuitka (for production builds).

## Quick Start

Build any plugin executable:

```bash
make build-plugin PLUGIN=examples/simple_plugin
```

The executable will be created in `dist/simple_plugin` (or `dist/simple_plugin.exe` on Windows).

Run the built plugin:

```bash
./dist/simple_plugin
```

## Build Tools

We support two build tools with different trade-offs:

### PyInstaller (Recommended for Development)

**Pros:**
- Fast builds (~5-10 seconds)
- Mature and well-documented
- Good compatibility with most packages
- Single-file executables for easy distribution

**Cons:**
- Slightly slower startup time (~100-200ms overhead)
- Runtime performance same as standard Python

**When to use:** During development and testing when fast iteration is important.

### Nuitka (Recommended for Production)

**Pros:**
- 2-3x faster startup time
- Compiled to native C code
- Better performance for CPU-bound operations
- More secure (harder to decompile)

**Cons:**
- Much longer build times (5-30 minutes)
- Larger executable sizes (~2x PyInstaller)
- Requires C compiler toolchain

**When to use:** For production releases where performance and security matter.

## Building with PyInstaller

### Basic Build

```bash
# Using Makefile
make build-plugin PLUGIN=examples/simple_plugin

# Or directly
./scripts/build_plugin.sh examples/simple_plugin
```

### Advanced Options

```bash
# Build with custom name
./scripts/build_plugin.sh examples/simple_plugin --name my-plugin

# Build in debug mode (shows console output)
./scripts/build_plugin.sh examples/simple_plugin --debug
```

## Building with Nuitka

### Basic Build

```bash
# Using Makefile
make build-plugin-prod PLUGIN=examples/simple_plugin

# Or directly
./scripts/build_plugin.sh examples/simple_plugin --nuitka
```

### Advanced Options

```bash
# Optimize for size
./scripts/build_plugin.sh examples/simple_plugin --nuitka --optimize-size

# Optimize for speed
./scripts/build_plugin.sh examples/simple_plugin --nuitka --optimize-speed

# Enable all optimizations (slow build)
./scripts/build_plugin.sh examples/simple_plugin --nuitka --full-compat
```

## Platform-Specific Notes

### macOS

**Requirements:**
- Xcode Command Line Tools: `xcode-select --install`
- For Nuitka: Full Xcode (for compiling to native code)

**Code Signing:**
If you need to distribute your plugin, you may need to sign it:

```bash
codesign --force --sign - dist/simple_plugin
```

### Linux

**Requirements:**
- GCC/G++ compiler: `sudo apt-get install build-essential` (Ubuntu/Debian)
- For Nuitka: Additional dev packages may be needed

**Permissions:**
Make executable:

```bash
chmod +x dist/simple_plugin
```

### Windows

**Requirements:**
- For Nuitka: Visual Studio Build Tools or MinGW-w64

**Note:** Executables will have `.exe` extension automatically.

## Troubleshooting

### ImportError: No module named 'grpc'

The gRPC library has native C extensions. PyInstaller should detect these automatically, but if you encounter issues:

```bash
# Add hidden imports explicitly
./scripts/build_plugin.sh examples/simple_plugin --hidden-import=grpc._cython.cygrpc
```

### AsyncIO Runtime Errors

If you see `RuntimeError: This event loop is already running`:

```bash
# Rebuild with asyncio hooks
./scripts/build_plugin.sh examples/simple_plugin --collect-all=asyncio
```

### Missing Protobuf Files

If protobuf definitions aren't found:

```bash
# Ensure proto files are included as data files
./scripts/build_plugin.sh examples/simple_plugin --add-data "src/mcpd_plugins/v1/plugins:mcpd_plugins/v1/plugins"
```

### Large Executable Size

To reduce size:

1. Use `--exclude-module` to remove unused dependencies
2. Use `--strip` to remove debug symbols (Linux/macOS)
3. Use Nuitka with `--optimize-size`

### Slow Nuitka Builds

Nuitka builds can take 5-30 minutes. To speed up:

1. Use `--show-progress` to see what's happening
2. Use `--jobs=N` to parallelize (N = CPU cores)
3. Cache compiled modules with `--module-cache-dir=.nuitka_cache`

## How the Build Process Works

### PyInstaller Process

1. **Analysis:** PyInstaller analyzes your code to find all dependencies
2. **Collection:** Collects Python modules, native libraries, and data files
3. **Bundling:** Packages everything with a bootloader
4. **Output:** Creates executable that extracts and runs at startup

### Nuitka Process

1. **Transpilation:** Converts Python code to C code
2. **Compilation:** Compiles C code to native machine code
3. **Linking:** Links with Python runtime and dependencies
4. **Output:** Creates native executable

## Testing Built Plugins

After building, test your plugin:

```bash
# Start the plugin server
./dist/simple_plugin

# In another terminal, verify it's listening
lsof -i :50051  # macOS/Linux
netstat -an | grep 50051  # Windows

# Test with grpcurl (if installed)
grpcurl -plaintext localhost:50051 list
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Install build dependencies
  run: uv sync --group build

- name: Build plugin with PyInstaller
  run: make build-plugin PLUGIN=examples/simple_plugin

- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: simple-plugin-${{ runner.os }}
    path: dist/simple_plugin*
```

## Best Practices

1. **Development:** Use PyInstaller for fast iteration
2. **Testing:** Test both source and built versions
3. **Production:** Use Nuitka for final releases
4. **Versioning:** Include version in executable name
5. **Documentation:** Update plugin README with build instructions
6. **Size:** Monitor executable size and optimize if needed
7. **Performance:** Benchmark critical paths in built executables

## Further Reading

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Nuitka Documentation](https://nuitka.net/doc/user-manual.html)
- [gRPC Python Performance Best Practices](https://grpc.io/docs/guides/performance/)
