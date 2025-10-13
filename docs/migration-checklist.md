# ComfyFixerSmart Migration Checklist

This checklist ensures a smooth migration from the old ComfyFixerSmart system to the new refactored version.

## Pre-Migration Preparation

### System Backup
- [ ] Create timestamped full project backup
  ```bash
  cp -r . migration_backup_$(date +%Y%m%d_%H%M%S)
  ```
- [ ] Backup state directory separately
  ```bash
  cp -r state state_backup_pre_migration
  ```
- [ ] Backup configuration files and environment variables
  ```bash
  env | grep -E "(COMFYUI|CIVITAI|OUTPUT|LOG|STATE)" > env_backup.txt
  ```
- [ ] Verify backup integrity
  ```bash
  ls -la migration_backup_*/ && du -sh migration_backup_*/
  ```

### Environment Assessment
- [ ] Document current ComfyUI installation path
- [ ] List all workflow directories in use
- [ ] Record custom environment variables
- [ ] Note any custom scripts or integrations
- [ ] Check current Python version and dependencies
  ```bash
  python --version && pip list | grep -E "(requests|toml)"
  ```

### Dependency Check
- [ ] Verify Python 3.8+ is available
- [ ] Install new required packages
  ```bash
  pip install tomli tomli-w
  ```
- [ ] Test new package imports
  ```bash
  python -c "import tomllib, tomli_w; print('Dependencies OK')"
  ```

## Migration Execution

### Phase 1: Configuration Migration
- [ ] Run configuration migration script
  ```bash
  python scripts/migrate_config.py --dry-run
  python scripts/migrate_config.py
  ```
- [ ] Verify config file creation
  ```bash
  ls -la config/default.toml && head config/default.toml
  ```
- [ ] Validate configuration syntax
  ```bash
  python -c "import tomllib; print('Config syntax OK')"
  ```
- [ ] Test configuration loading
  ```bash
  python -c "from comfyfixersmart.config import config; print(f'Config loaded: {config.comfyui_root}')"
  ```

### Phase 2: State Migration
- [ ] Run state migration with backup
  ```bash
  python scripts/migrate_state.py --backup --dry-run
  python scripts/migrate_state.py --backup
  ```
- [ ] Verify backup creation
  ```bash
  ls -la state_backup_*/
  ```
- [ ] Check new state file creation
  ```bash
  ls -la state/download_state_v2.json
  ```
- [ ] Validate state file format
  ```bash
  python -c "import json; data=json.load(open('state/download_state_v2.json')); print(f'State version: {data.get(\"version\")}')"
  ```

### Phase 3: System Validation
- [ ] Run comprehensive validation
  ```bash
  python scripts/validate_migration.py --verbose
  ```
- [ ] Verify directory structure
  ```bash
  ls -la output/ log/ state/
  ```
- [ ] Test new module imports
  ```bash
  python -c "from comfyfixersmart.cli import create_parser; from comfyfixersmart.state_manager import StateManager; print('Imports OK')"
  ```
- [ ] Validate ComfyUI integration
  ```bash
  python scripts/validate_migration.py --comfyui-root /path/to/comfyui
  ```

### Phase 4: Functional Testing
- [ ] Test CLI help system
  ```bash
  python -m comfyfixersmart.cli --help
  ```
- [ ] Test basic workflow scanning (dry run)
  ```bash
  find workflows -name "*.json" | head -1 | xargs python -m comfyfixersmart.cli --dry-run
  ```
- [ ] Test different compatibility modes
  ```bash
  python -m comfyfixersmart.cli --v1 --dry-run
  python -m comfyfixersmart.cli --v2 --dry-run
  ```
- [ ] Verify search backend options
  ```bash
  python -m comfyfixersmart.cli --search civitai --dry-run
  ```

## Post-Migration Tasks

### System Integration
- [ ] Update PYTHONPATH if needed
  ```bash
  export PYTHONPATH="$PWD/src:$PYTHONPATH"
  ```
- [ ] Update shell aliases and scripts
  ```bash
  # Update scripts to use new CLI
  sed -i 's/python comfy_fixer.py/python -m comfyfixersmart.cli/g' *.sh
  ```
- [ ] Update any cron jobs or scheduled tasks
- [ ] Update documentation and README files

### User Training
- [ ] Document new CLI commands and options
- [ ] Create command reference cheat sheet
- [ ] Update team workflows and procedures
- [ ] Schedule training session if needed

### Cleanup and Optimization
- [ ] Remove old backup files after successful testing
  ```bash
  rm -rf migration_backup_*  # Only after thorough testing
  ```
- [ ] Archive old state files
  ```bash
  mkdir -p archives/old_state && mv state/download_state.json archives/old_state/
  ```
- [ ] Update .gitignore for new file structure
- [ ] Optimize configuration for production use

## Verification Points

### Data Integrity
- [ ] All download history preserved
- [ ] File paths and sizes maintained
- [ ] Timestamps and metadata intact
- [ ] No duplicate or missing entries

### Functional Integrity
- [ ] All CLI commands work as expected
- [ ] Workflow scanning produces same results
- [ ] Download functionality operational
- [ ] Error handling and logging functional

### Performance Integrity
- [ ] Migration doesn't impact performance negatively
- [ ] Memory usage within acceptable limits
- [ ] Startup time reasonable
- [ ] Batch processing working correctly

## Rollback Readiness

### Emergency Procedures
- [ ] Verify rollback script functionality
  ```bash
  python scripts/rollback.py --dry-run
  ```
- [ ] Document rollback steps clearly
- [ ] Test rollback on development system
- [ ] Have backup restoration plan ready

### Support Plan
- [ ] Identify support contacts for migration issues
- [ ] Prepare troubleshooting guides
- [ ] Set up monitoring for post-migration issues
- [ ] Plan communication for any downtime

## Sign-off Requirements

### Technical Sign-off
- [ ] All validation checks pass
- [ ] Functional testing complete
- [ ] Performance benchmarks met
- [ ] Security review completed

### User Acceptance
- [ ] Key users test their workflows
- [ ] Training completed
- [ ] Documentation reviewed
- [ ] Go-live approval obtained

## Post-Migration Monitoring

### Week 1 Monitoring
- [ ] Monitor error logs daily
- [ ] Check download success rates
- [ ] Verify user feedback
- [ ] Performance monitoring

### Month 1 Review
- [ ] Comprehensive system review
- [ ] User satisfaction survey
- [ ] Performance optimization
- [ ] Documentation updates

---

## Quick Reference Commands

```bash
# Full migration in one command
python scripts/migrate_config.py && python scripts/migrate_state.py --backup && python scripts/validate_migration.py

# Quick validation
python scripts/validate_migration.py --verbose

# Emergency rollback
python scripts/rollback.py --force

# Test new system
python -m comfyfixersmart.cli --help
```

## Emergency Contacts

- Technical Lead: [Name/Contact]
- System Admin: [Name/Contact]
- User Support: [Name/Contact]

---

*Complete all checklist items before considering migration successful. Keep backups until system is stable in production.*