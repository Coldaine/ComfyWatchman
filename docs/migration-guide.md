# ComfyFixerSmart Migration Guide

This guide provides comprehensive instructions for migrating from the old ComfyFixerSmart system to the new refactored version.

## Overview

The new ComfyFixerSmart system features:
- **Modular Architecture**: Separated concerns into dedicated modules
- **Enhanced Configuration**: TOML-based configuration with validation
- **Improved State Management**: Better tracking with statistics and migration support
- **Compatibility Modes**: Support for both v1 (incremental) and v2 (batch) processing
- **Better CLI**: More options and clearer help
- **Robust Error Handling**: Comprehensive validation and rollback capabilities

## Migration Process

### Step 1: Pre-Migration Preparation

#### Backup Your Data
```bash
# Create a full backup of your current setup
cp -r . migration_backup_$(date +%Y%m%d_%H%M%S)

# Specifically backup state and configuration
cp -r state state_backup
cp comfy_fixer.py comfy_fixer_backup.py
```

#### Check Current Setup
```bash
# Verify your current environment
python comfy_fixer.py --help

# Check for existing state
ls -la state/

# Check environment variables
env | grep -E "(COMFYUI|CIVITAI)"
```

#### Install New Dependencies
```bash
# Install new required packages
pip install tomli tomli-w  # For TOML configuration support

# Verify installation
python -c "import tomllib, tomli_w; print('TOML support OK')"
```

### Step 2: Configuration Migration

#### Automatic Migration
```bash
# Run the configuration migration script
python scripts/migrate_config.py

# Or specify custom config location
python scripts/migrate_config.py --config-path config/my_config.toml

# Dry run to see what would be migrated
python scripts/migrate_config.py --dry-run
```

#### Manual Configuration
If automatic migration doesn't detect your setup, create `config/default.toml`:

```toml
# ComfyFixerSmart Configuration
comfyui_root = "/path/to/your/ComfyUI"
workflow_dirs = [
    "user/default/workflows",
    "/additional/workflow/directory"
]
output_dir = "output"
log_dir = "log"
state_dir = "state"

# API Settings
civitai_api_base = "https://civitai.com/api/v1"
civitai_download_base = "https://civitai.com/api/download/models"
civitai_api_timeout = 30

# Model settings and mappings...
```

### Step 3: State Migration

#### Migrate Download State
```bash
# Migrate state with backup
python scripts/migrate_state.py --backup

# Or migrate without backup (not recommended)
python scripts/migrate_state.py --force

# Dry run
python scripts/migrate_state.py --dry-run
```

#### Verify State Migration
```bash
# Check that new state file was created
ls -la state/download_state_v2.json

# Verify old state is backed up
ls -la state_backup_*/
```

### Step 4: Validation

#### Run Migration Validation
```bash
# Basic validation
python scripts/validate_migration.py

# With ComfyUI root validation
python scripts/validate_migration.py --comfyui-root /path/to/ComfyUI

# Verbose output
python scripts/validate_migration.py --verbose
```

#### Manual Verification
```bash
# Test new CLI
python -m comfyfixersmart.cli --help

# Test import of new modules
python -c "from comfyfixersmart.config import Config; print('Import OK')"

# Check configuration loading
python -c "from comfyfixersmart.config import config; print(f'ComfyUI root: {config.comfyui_root}')"
```

### Step 5: Testing Migration

#### Test with Sample Workflow
```bash
# Test new system with a single workflow
python -m comfyfixersmart.cli path/to/test/workflow.json --dry-run

# Compare with old system (if still available)
python comfy_fixer.py path/to/test/workflow.json --dry-run
```

#### Test Different Modes
```bash
# Test v1 compatibility mode
python -m comfyfixersmart.cli --v1

# Test v2 mode (default)
python -m comfyfixersmart.cli --v2

# Test with different search backends
python -m comfyfixersmart.cli --search civitai,huggingface
```

### Step 6: Full Migration

#### Update Your Workflow
```bash
# Replace old commands with new ones
# Old: python comfy_fixer.py
# New: python -m comfyfixersmart.cli

# Update any scripts or aliases
sed -i 's/comfy_fixer.py/-m comfyfixersmart.cli/g' your_scripts.sh
```

#### Update Environment
```bash
# Update PYTHONPATH if needed
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Update any shell aliases
echo "alias comfyfixer='python -m comfyfixersmart.cli'" >> ~/.bashrc
```

## Compatibility Layer

The new system includes compatibility features:

### CLI Compatibility
```bash
# Old style still works (with warnings)
python comfy_fixer.py workflow.json

# New recommended style
python -m comfyfixersmart.cli workflow.json
```

### Configuration Compatibility
- Environment variables still override config file settings
- Old hardcoded paths are auto-detected during migration
- Graceful fallback to defaults for missing configuration

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# If you get import errors
export PYTHONPATH="$PWD/src:$PYTHONPATH"
pip install -e .
```

#### Configuration Not Found
```bash
# Regenerate config
python scripts/migrate_config.py --force

# Check config syntax
python -c "import tomllib; tomllib.load(open('config/default.toml', 'rb'))"
```

#### State Migration Fails
```bash
# Check state file format
python -c "import json; json.load(open('state/download_state.json'))"

# Manual state migration
python scripts/migrate_state.py --force
```

#### Validation Errors
```bash
# Run with verbose output
python scripts/validate_migration.py --verbose

# Check specific components
python -c "from comfyfixersmart.config import config; print(config.__dict__)"
```

### Rollback Procedures

#### Emergency Rollback
```bash
# Rollback to old system
python scripts/rollback.py --backup-dir state_backup_20231201_120000

# Rollback with config restoration
python scripts/rollback.py --restore-config --force
```

#### Partial Rollback
```bash
# Only rollback state
python scripts/rollback.py --dry-run  # See what would be changed
python scripts/rollback.py --force    # Actually rollback
```

## Migration Checklist

### Pre-Migration
- [ ] Create full system backup
- [ ] Backup state directory
- [ ] Backup configuration files
- [ ] Install new dependencies
- [ ] Test old system functionality

### Migration Steps
- [ ] Run configuration migration
- [ ] Run state migration with backup
- [ ] Validate migration success
- [ ] Test new system with sample data
- [ ] Update scripts and aliases
- [ ] Update environment variables

### Post-Migration
- [ ] Verify all workflows still work
- [ ] Check download history integrity
- [ ] Test different CLI options
- [ ] Update documentation
- [ ] Train team on new system

## Version Compatibility

| Old Version | New Version | Compatibility |
|-------------|-------------|---------------|
| 1.0.x       | 2.0.x       | Full migration support |
| Custom mods | 2.0.x       | Manual migration required |

## Support

### Getting Help
1. Check this migration guide
2. Run validation scripts with `--verbose`
3. Check logs in `log/` directory
4. Review error messages carefully

### Reporting Issues
When reporting migration issues, include:
- Output of `python scripts/validate_migration.py --verbose`
- Your old configuration (anonymized)
- Error messages and stack traces
- Steps to reproduce the issue

## FAQ

**Q: Can I run both old and new systems simultaneously?**
A: Yes, but not recommended. Use different directories or virtual environments.

**Q: What happens to my download history?**
A: It's migrated to the new format with enhanced tracking and statistics.

**Q: Do I need to reinstall ComfyUI?**
A: No, the new system works with your existing ComfyUI installation.

**Q: Can I migrate back if needed?**
A: Yes, use the rollback script with backup directories.

**Q: Are there performance differences?**
A: The new system may be faster due to batch processing and better caching.

## Quick Migration Reference

```bash
# One-command migration (with backups)
python scripts/migrate_config.py && python scripts/migrate_state.py --backup && python scripts/validate_migration.py

# Quick test
python -m comfyfixersmart.cli --help

# Emergency rollback
python scripts/rollback.py --force
```

---

*This migration guide is comprehensive but may need updates as the system evolves. Always backup before migrating!*