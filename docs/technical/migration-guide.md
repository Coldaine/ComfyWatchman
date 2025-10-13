# Migration Guide

This guide helps you migrate between different versions of ComfyFixerSmart, including breaking changes and required updates.

## Latest Version: 2.0.0

ComfyFixerSmart 2.0.0 introduces significant improvements with the new incremental workflow system. This guide covers migration from v1.x versions.

## Migration from v1.x to v2.0

### Key Changes

#### 1. Incremental Workflow (Breaking Change)

**What Changed:**
- v1.x used batch processing (search all → download all)
- v2.0 uses incremental processing (search one → download immediately)

**Migration Required:**
- No code changes required for basic usage
- Scripts and automation continue to work
- Performance improvements are automatic

**Benefits:**
- Faster downloads (no waiting for all searches)
- Better reliability (failures don't block others)
- Real-time progress visibility

#### 2. Configuration System Overhaul

**What Changed:**
- New TOML-based configuration system
- Environment variables still supported
- More granular control options

**Migration:**

**Old (v1.x):**
```bash
# Environment variables only
export COMFYUI_ROOT="/path/to/comfyui"
export CIVITAI_API_KEY="your-key"
```

**New (v2.0):**
```toml
# config/default.toml
comfyui_root = "/path/to/comfyui"
civitai_api_key = "your-key"  # Or use env var

# Additional options
workflow_dirs = ["user/default/workflows"]
search_backends = ["civitai", "huggingface"]
download_concurrency = 3
```

**Migration Steps:**
1. Create `config/default.toml` with your settings
2. Move environment variables to config file if preferred
3. Test with `comfyfixer --validate-config`

#### 3. CLI Changes

**New Options:**
```bash
# Search backend selection
comfyfixer --search civitai,huggingface

# Incremental mode (now default)
comfyfixer --v2

# Legacy v1 mode (if needed)
comfyfixer --v1
```

**Deprecated Options:**
- `--batch-mode`: Use `--v1` instead
- `--single-threaded`: Use `--concurrency 1`

#### 4. Output Structure Changes

**New Output Structure (v2.0):**
```
output/
├── download_001_model.sh    # Individual scripts
├── download_002_model.sh
├── download_counter.txt     # Progress tracking
├── downloaded_models.json   # Success tracking
├── missing_models.json      # Original analysis
├── analysis_report.md       # Human-readable report
└── logs/                    # Organized logs
    ├── comfyfixer_20251012_143000.log
    └── search_history.log
```

**Migration:**
- Scripts now numbered individually
- JSON files for programmatic access
- Better log organization

### Breaking Changes

#### API Changes

**StateManager API:**
```python
# v1.x
state = StateManager()
state.add_downloaded_model("model.safetensors")

# v2.0
state = StateManager()
state.record_download("model.safetensors", "civitai", "12345")
```

**Configuration Access:**
```python
# v1.x
from comfyfixersmart.config import config
config.set_comfyui_root("/path")

# v2.0
from comfyfixersmart import config
config.comfyui_root = Path("/path")
```

#### File Paths

**Log Files:**
- v1.x: `qwen_search_history.log` (flat)
- v2.0: `logs/search_history.log` (organized)

**State Files:**
- v1.x: `download_state.json` (simple)
- v2.0: `state/download_state.json` (versioned)

### Migration Steps

#### Step 1: Backup Your Data

```bash
# Backup existing configuration
cp ~/.secrets ~/.secrets.backup
cp -r output/ output.backup/
cp -r log/ log.backup/
```

#### Step 2: Update Installation

```bash
# Update to v2.0
pip install --upgrade comfyfixersmart

# Verify version
comfyfixer --version  # Should show 2.0.0
```

#### Step 3: Create New Configuration

```bash
# Create config directory
mkdir -p config

# Create default configuration
cat > config/default.toml << 'EOF'
# ComfyUI Configuration
comfyui_root = "/path/to/your/comfyui"

# Workflow scanning
workflow_dirs = [
    "user/default/workflows"
]

# Search backends
search_backends = ["civitai"]

# Download settings
download_concurrency = 3
download_timeout = 300
verify_downloads = true

# Logging
log_level = "INFO"
EOF
```

#### Step 4: Update Environment Variables (Optional)

If you prefer environment variables:

```bash
# Keep existing variables
export COMFYUI_ROOT="/path/to/comfyui"
export CIVITAI_API_KEY="your-key"

# Add new variables if needed
export DOWNLOAD_CONCURRENCY="3"
```

#### Step 5: Test Configuration

```bash
# Validate configuration
comfyfixer --validate-config

# Test basic functionality
comfyfixer --help
```

#### Step 6: Run Test Analysis

```bash
# Test with a single workflow
comfyfixer path/to/test/workflow.json --output-dir test-output/

# Check results
ls -la test-output/
cat test-output/analysis_report.md
```

#### Step 7: Migrate Custom Scripts

**Old Script (v1.x):**
```bash
#!/bin/bash
cd /path/to/comfyfixer
python comfy_fixer.py
bash output/download_missing.sh
```

**New Script (v2.0):**
```bash
#!/bin/bash
cd /path/to/comfyfixer
comfyfixer  # CLI now handles everything
# Or specify workflows:
# comfyfixer workflow1.json workflow2.json
```

**Python API Migration:**
```python
# v1.x
from comfyfixersmart.core import run_comfy_fixer
result = run_comfy_fixer(workflows=["workflow.json"])

# v2.0 (same API, enhanced)
from comfyfixersmart import ComfyFixerCore
fixer = ComfyFixerCore()
result = fixer.run(workflow_paths=["workflow.json"])
```

### Troubleshooting Migration

#### "Configuration file not found"

**Solution:**
```bash
# Create minimal config
mkdir -p config
echo 'comfyui_root = "/path/to/comfyui"' > config/default.toml
```

#### "Module not found" errors

**Solution:**
```bash
# Reinstall with dependencies
pip uninstall comfyfixersmart
pip install comfyfixersmart

# Or reinstall in development mode
pip install -e .
```

#### "API key not found"

**Solution:**
```bash
# Check environment
echo $CIVITAI_API_KEY

# Or add to config
echo 'civitai_api_key = "your-key"' >> config/default.toml
```

#### Performance Issues

**Solution:**
```toml
# Optimize for your system
[download]
concurrency = 2  # Reduce if system is slow
timeout = 600    # Increase for slow connections

[cache]
enabled = true   # Enable caching
```

### Rollback Plan

If you need to rollback to v1.x:

```bash
# Install specific version
pip install comfyfixersmart==1.9.0

# Restore backup configuration
cp ~/.secrets.backup ~/.secrets
cp -r output.backup/* output/
cp -r log.backup/* log/
```

## Future Migrations

### Planned for v3.0

**Expected Changes:**
- Plugin system for custom search backends
- Async/await support for better concurrency
- Configuration validation with JSON schema
- Enhanced error reporting and recovery

**Migration Timeline:**
- v2.5: Deprecation warnings for changed APIs
- v3.0: Breaking changes with migration tools

### Preparing for v3.0

```python
# Use new APIs where available
from comfyfixersmart import ComfyFixerCore

# Avoid deprecated patterns
# Old: direct config manipulation
# New: use config object
```

## Version Compatibility

### Supported Versions

- **v2.0+**: Current version with incremental workflow
- **v1.8+**: Last v1.x version with bug fixes
- **v1.0+**: Minimum supported version

### End of Life

- **v1.x**: Supported until v3.0 release (estimated Q2 2026)
- **v0.x**: No longer supported

### Long-term Support

- **LTS Versions**: v2.0 (until v4.0)
- **Security Fixes**: 3 years from release
- **Bug Fixes**: 2 years from release

## Getting Help

### Migration Support

- **Documentation**: This migration guide
- **Issues**: GitHub issues for migration problems
- **Discussions**: Community discussions for questions

### Professional Services

For complex migrations or enterprise support:
- Contact maintainers
- Check for commercial support options
- Consider professional consulting

## Summary

Migrating from v1.x to v2.0 is straightforward:

1. **Backup** your existing setup
2. **Update** to v2.0
3. **Create** new configuration file
4. **Test** with small workflows
5. **Migrate** custom scripts if needed

The new incremental workflow provides significant performance and reliability improvements while maintaining backward compatibility for most use cases.