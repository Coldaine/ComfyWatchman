# ComfyFixerSmart Migration Testing Strategy

This document outlines comprehensive testing strategies for validating ComfyFixerSmart migrations, ensuring data integrity, functional correctness, and performance requirements.

## Testing Overview

### Test Categories
- **Migration Tests**: Validate data and configuration migration
- **Functional Tests**: Ensure features work after migration
- **Performance Tests**: Verify performance improvements/regressions
- **Compatibility Tests**: Test with different user setups
- **Rollback Tests**: Validate emergency recovery procedures

### Test Environments
- **Development**: Local testing during development
- **Staging**: Pre-production validation
- **Production**: Live system testing with backups

## Migration Test Scenarios

### Scenario 1: Fresh Installation
**Objective**: Test migration on a new system with no existing data.

**Setup**:
```bash
# Clean environment
rm -rf config/ state/ output/ log/
```

**Test Steps**:
1. Run configuration migration: `python scripts/migrate_config.py`
2. Run state migration: `python scripts/migrate_state.py`
3. Validate migration: `python scripts/validate_migration.py`
4. Test basic functionality: `python -m comfyfixersmart.cli --help`

**Expected Results**:
- Default configuration created
- Empty state initialized
- All validation checks pass
- CLI responds correctly

### Scenario 2: Legacy System with Data
**Objective**: Test migration from existing 1.x system with download history.

**Setup**:
```bash
# Simulate legacy state
mkdir -p state
echo '{"downloads": {"model1.safetensors": {"success": true, "timestamp": "2024-01-01T00:00:00Z"}}, "history": []}' > state/download_state.json
```

**Test Steps**:
1. Backup verification: `ls -la state/`
2. Run migration with backup: `python scripts/migrate_state.py --backup`
3. Verify backup created: `ls -la state_backup_*`
4. Validate migration: `python scripts/validate_migration.py`
5. Check data integrity: Compare old vs new state statistics

**Expected Results**:
- Backup created successfully
- Data migrated without loss
- New state format valid
- Statistics accurate

### Scenario 3: Complex Configuration
**Objective**: Test migration with custom environment variables and complex setup.

**Setup**:
```bash
# Set legacy environment
export COMFYUI_ROOT="/custom/comfyui/path"
export OUTPUT_DIR="custom_output"
export LOG_DIR="custom_log"
export STATE_DIR="custom_state"
mkdir -p workflows/
echo '{"nodes": []}' > workflows/complex_workflow.json
```

**Test Steps**:
1. Run config migration: `python scripts/migrate_config.py --dry-run`
2. Verify environment detection
3. Run actual migration: `python scripts/migrate_config.py`
4. Check TOML config: `cat config/default.toml`
5. Test with workflow: `python -m comfyfixersmart.cli workflows/complex_workflow.json --dry-run`

**Expected Results**:
- Environment variables detected
- Configuration migrated correctly
- Custom paths preserved
- Workflow processing works

### Scenario 4: Error Conditions
**Objective**: Test migration resilience to errors and edge cases.

**Test Cases**:
- Corrupted state file
- Missing permissions
- Insufficient disk space
- Network connectivity issues
- Invalid configuration values

**Test Steps**:
```bash
# Test corrupted state
echo "invalid json" > state/download_state.json
python scripts/migrate_state.py  # Should handle gracefully

# Test permission issues
chmod 444 state/
python scripts/migrate_state.py  # Should report error clearly
chmod 755 state/

# Test missing dependencies
pip uninstall tomli tomli-w  # Temporarily
python scripts/migrate_config.py  # Should provide clear error
pip install tomli tomli-w  # Restore
```

**Expected Results**:
- Clear error messages
- Graceful failure handling
- Recovery suggestions provided
- No data corruption

## Functional Testing Strategy

### Core Functionality Tests

#### CLI Interface Testing
```bash
# Test all CLI options
python -m comfyfixersmart.cli --help
python -m comfyfixersmart.cli --version
python -m comfyfixersmart.cli --v1 --dry-run
python -m comfyfixersmart.cli --v2 --dry-run
python -m comfyfixersmart.cli --search civitai --dry-run
```

#### Workflow Processing Tests
```bash
# Test with various workflow types
python -m comfyfixersmart.cli workflows/simple.json --dry-run
python -m comfyfixersmart.cli workflows/complex.json --dry-run
python -m comfyfixersmart.cli workflows/missing_models.json --dry-run
```

#### Download Simulation Tests
```bash
# Test download logic without actual downloads
python -m comfyfixersmart.cli --no-script --dry-run workflow.json
# Verify model detection and URL generation
```

### Compatibility Layer Testing

#### Wrapper Script Tests
```bash
# Test Python wrapper
python comfy_fixer_compat.py --help
python comfy_fixer_compat.py --show-migration-info

# Test shell wrapper
./comfy_fixer.sh --help
COMFYFIXER_COMPATIBILITY_MODE=legacy ./comfy_fixer.sh --help
```

#### Argument Translation Tests
```bash
# Test old arguments work with new system
python comfy_fixer_compat.py --verify-urls --dry-run workflow.json
./comfy_fixer.sh --verify-urls --dry-run workflow.json
```

## Performance Testing Strategy

### Benchmarking Setup
```bash
# Create test workflows of different sizes
# Small: 5 models
# Medium: 20 models
# Large: 100+ models

# Run performance tests
time python -m comfyfixersmart.cli small_workflow.json --dry-run
time python -m comfyfixersmart.cli medium_workflow.json --dry-run
time python -m comfyfixersmart.cli large_workflow.json --dry-run
```

### Performance Metrics
- **Startup Time**: Time to load configuration and initialize
- **Processing Speed**: Models analyzed per second
- **Memory Usage**: Peak memory consumption
- **Disk I/O**: State file read/write performance
- **Network Requests**: API call efficiency

### Performance Regression Tests
```bash
# Compare old vs new system performance
time python comfy_fixer.py benchmark_workflow.json  # Old system
time python -m comfyfixersmart.cli benchmark_workflow.json  # New system

# Ensure new system is faster
# Target: 2-3x improvement for large workflows
```

## Data Integrity Testing

### State Migration Validation
```python
# Python script to validate state integrity
import json
from pathlib import Path

def validate_state_migration(old_file, new_file):
    old_state = json.loads(Path(old_file).read_text())
    new_state = json.loads(Path(new_file).read_text())

    # Check download count preservation
    old_count = len(old_state.get('downloads', {}))
    new_count = len(new_state.get('downloads', {}))

    assert old_count == new_count, f"Download count mismatch: {old_count} vs {new_count}"

    # Check data preservation
    for filename, old_data in old_state.get('downloads', {}).items():
        new_data = new_state.get('downloads', {}).get(filename)
        assert new_data, f"Missing download data for {filename}"

        # Check critical fields
        assert old_data.get('success') == (new_data.get('status') == 'success')
        assert old_data.get('timestamp') == new_data.get('timestamp')

    print("✅ State migration validation passed")
```

### Configuration Migration Validation
```python
def validate_config_migration():
    # Test environment variable migration
    import os
    os.environ['COMFYUI_ROOT'] = '/test/path'

    # Run migration
    # Verify TOML contains correct values
    # Check environment override still works
```

## Rollback Testing Strategy

### Rollback Scenarios
1. **Successful Migration Rollback**: Test returning to old system after successful migration
2. **Failed Migration Recovery**: Test rollback after partial migration failure
3. **Data Recovery**: Ensure no data loss during rollback

### Rollback Test Script
```bash
#!/bin/bash
# Rollback testing script

echo "=== Rollback Testing ==="

# Setup test state
mkdir -p test_state_backup
cp -r state/* test_state_backup/

# Run migration
python scripts/migrate_state.py --backup

# Simulate working with new system
echo "Working with new system..."
# ... some operations ...

# Test rollback
python scripts/rollback.py --backup-dir state_backup_* --dry-run
python scripts/rollback.py --backup-dir state_backup_* --force

# Validate rollback
if diff -r test_state_backup/ state/; then
    echo "✅ Rollback successful - state restored"
else
    echo "❌ Rollback failed - state mismatch"
    exit 1
fi
```

## Automated Testing Framework

### Test Structure
```
tests/
├── migration/
│   ├── test_config_migration.py
│   ├── test_state_migration.py
│   ├── test_validation.py
│   └── test_rollback.py
├── functional/
│   ├── test_cli.py
│   ├── test_workflow_processing.py
│   └── test_compatibility.py
├── performance/
│   ├── benchmark.py
│   └── regression_test.py
└── integration/
    ├── test_full_migration.py
    └── test_user_scenarios.py
```

### Continuous Integration
```yaml
# .github/workflows/migration-tests.yml
name: Migration Tests
on: [push, pull_request]

jobs:
  migration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Run migration tests
        run: pytest tests/migration/ -v
      - name: Run functional tests
        run: pytest tests/functional/ -v
```

## User Scenario Testing

### Scenario-Based Test Cases

#### Power User Migration
- Large download history (1000+ models)
- Custom configuration
- Multiple workflow directories
- Performance-critical setup

#### Minimal User Migration
- First-time user
- Default settings
- Single workflow
- Basic functionality

#### Enterprise User Migration
- Multi-user environment
- Network restrictions
- Custom model directories
- Integration with existing tools

### User Acceptance Testing
```bash
# Setup different user environments
# Test migration in each environment
# Gather feedback on ease of use
# Measure time to complete migration
```

## Monitoring and Reporting

### Test Results Dashboard
- Migration success rate
- Performance benchmarks
- Error frequency by type
- User feedback scores

### Automated Reporting
```python
def generate_test_report(results):
    """Generate comprehensive test report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "migration_tests": results["migration"],
        "functional_tests": results["functional"],
        "performance_tests": results["performance"],
        "rollback_tests": results["rollback"],
        "recommendations": generate_recommendations(results)
    }

    with open("migration_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report
```

## Risk Mitigation

### High-Risk Areas
- **State Data Corruption**: Comprehensive backup and validation
- **Configuration Loss**: Environment variable preservation
- **Performance Regression**: Benchmarking against baselines
- **User Downtime**: Compatibility layer and rollback procedures

### Contingency Plans
- **Migration Failure**: Clear rollback procedures
- **Data Loss**: Multiple backup strategies
- **Performance Issues**: Compatibility mode fallback
- **User Confusion**: Comprehensive documentation and support

---

## Test Execution Checklist

### Pre-Migration Testing
- [ ] Unit tests for migration scripts
- [ ] Integration tests for full migration
- [ ] Performance benchmarks established
- [ ] Rollback procedures tested

### Migration Testing
- [ ] Dry-run migrations tested
- [ ] Full migrations with backups tested
- [ ] Error conditions handled
- [ ] Data integrity verified

### Post-Migration Testing
- [ ] Functional tests pass
- [ ] Performance meets targets
- [ ] User scenarios validated
- [ ] Documentation accurate

### Ongoing Monitoring
- [ ] Automated regression tests
- [ ] Performance monitoring
- [ ] User feedback collection
- [ ] Issue tracking and resolution

---

*This testing strategy ensures migration reliability and user confidence in the upgrade process.*