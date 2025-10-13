# ComfyFixerSmart Migration Cheat Sheet

## Quick Migration Commands

### One-Command Migration
```bash
# Migrate everything with backups and validation
python scripts/migrate_config.py && python scripts/migrate_state.py --backup && python scripts/validate_migration.py
```

### Individual Steps
```bash
# 1. Migrate configuration
python scripts/migrate_config.py

# 2. Migrate state (with backup)
python scripts/migrate_state.py --backup

# 3. Validate migration
python scripts/validate_migration.py
```

## Command Translation

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `python comfy_fixer.py` | `python -m comfyfixersmart.cli` | Basic usage |
| `python comfy_fixer.py workflow.json` | `python -m comfyfixersmart.cli workflow.json` | Specific workflow |
| `python comfy_fixer.py --verify-urls` | `python -m comfyfixersmart.cli --verify-urls` | URL verification |

## Configuration Changes

### Old Environment Variables
```bash
# These still work but are deprecated
export COMFYUI_ROOT="/path/to/comfyui"
export OUTPUT_DIR="output"
export LOG_DIR="log"
export STATE_DIR="state"
```

### New Configuration File
```toml
# config/default.toml
comfyui_root = "/path/to/comfyui"
output_dir = "output"
log_dir = "log"
state_dir = "state"
# ... more options
```

## File Structure Changes

### Old Structure
```
comfy_fixer.py
state_manager.py
state/
├── download_state.json
output/
log/
```

### New Structure
```
src/comfyfixersmart/
├── cli.py
├── config.py
├── state_manager.py
├── core.py
└── ...
config/
├── default.toml
state/
├── download_state_v2.json
scripts/
├── migrate_*.py
├── validate_migration.py
├── rollback.py
docs/
├── migration-guide.md
├── migration-checklist.md
```

## Common Issues & Fixes

### Import Errors
```bash
# Fix: Add src to Python path
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

### Config Not Found
```bash
# Fix: Run migration or create manually
python scripts/migrate_config.py --force
```

### State Migration Fails
```bash
# Fix: Check state file format
python -c "import json; json.load(open('state/download_state.json'))"
# Then retry migration
python scripts/migrate_state.py --force
```

### Validation Errors
```bash
# Fix: Run verbose validation
python scripts/validate_migration.py --verbose
```

## Emergency Rollback

### Quick Rollback
```bash
# Rollback with latest backup
python scripts/rollback.py --force

# Rollback specific backup
python scripts/rollback.py --backup-dir state_backup_20231201_120000 --force
```

### Manual Rollback
```bash
# Restore from backup
cp -r migration_backup_20231201_120000/* .
rm -rf config/  # If config migration caused issues
```

## Testing Commands

### Basic Tests
```bash
# Test CLI
python -m comfyfixersmart.cli --help

# Test import
python -c "from comfyfixersmart.config import config; print('OK')"

# Test with sample workflow
find workflows -name "*.json" | head -1 | xargs python -m comfyfixersmart.cli --dry-run
```

### Compatibility Tests
```bash
# Test v1 mode
python -m comfyfixersmart.cli --v1 --dry-run

# Test v2 mode
python -m comfyfixersmart.cli --v2 --dry-run

# Test search backends
python -m comfyfixersmart.cli --search civitai --dry-run
```

## Performance Comparison

### Old System
```bash
time python comfy_fixer.py --dry-run
```

### New System
```bash
time python -m comfyfixersmart.cli --dry-run
```

## Monitoring & Logs

### Check Logs
```bash
# New system logs
ls -la log/
tail log/comfyfixer_*.log

# Old system logs (if still present)
tail debug_run.log
```

### Monitor State
```bash
# Check download statistics
python -c "import json; data=json.load(open('state/download_state_v2.json')); print(data['statistics'])"

# Compare with old state
python -c "import json; old=json.load(open('state/download_state.json')); print(f'Old downloads: {len(old[\"downloads\"])}')"
```

## Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:
```bash
# ComfyFixer aliases
alias comfyfixer='python -m comfyfixersmart.cli'
alias comfyfixer-old='python comfy_fixer.py'
alias migrate-comfy='python scripts/migrate_config.py && python scripts/migrate_state.py --backup && python scripts/validate_migration.py'
alias rollback-comfy='python scripts/rollback.py --force'
```

## Version Information

```bash
# Check new system version
python -c "from comfyfixersmart import __version__; print(__version__)"

# Check migration status
python scripts/validate_migration.py | grep -E "(version|downloads)"
```

## Support Resources

- **Migration Guide**: `docs/migration-guide.md`
- **Checklist**: `docs/migration-checklist.md`
- **Scripts Help**: `python scripts/*.py --help`
- **Validation**: `python scripts/validate_migration.py --verbose`

---

## Quick Status Check

Run after migration:
```bash
echo "=== Migration Status ===" && \
python scripts/validate_migration.py && \
echo -e "\n=== CLI Test ===" && \
python -m comfyfixersmart.cli --help | head -5 && \
echo -e "\n=== State Check ===" && \
ls -la state/ && \
echo -e "\n=== Config Check ===" && \
ls -la config/