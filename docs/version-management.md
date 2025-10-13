# ComfyFixerSmart Version Management Strategy

This document outlines the version management strategy for ComfyFixerSmart, including version numbering, backward compatibility policies, and migration timelines.

## Version Numbering Scheme

ComfyFixerSmart follows [Semantic Versioning](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

### Version Components
- **MAJOR**: Breaking changes that require migration
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Pre-release Identifiers
- **alpha**: Early testing, may have breaking changes
- **beta**: Feature complete, API stable
- **rc**: Release candidate, ready for production

### Examples
- `2.0.0`: Major release with new architecture
- `2.1.0`: New features added
- `2.1.1`: Bug fixes
- `3.0.0-alpha.1`: Next major version in development

## Current Version Status

### Version 2.0.0 (Current)
- **Release Date**: [Current Date]
- **Status**: Stable
- **Previous Version**: 1.x (Legacy)

### Migration Timeline
- **Version 1.x End of Life**: 6 months after 2.0.0 release
- **Version 1.x Support**: 12 months after 2.0.0 release
- **Compatibility Layer Removal**: 18 months after 2.0.0 release

## Backward Compatibility Policy

### API Compatibility
- **MAJOR versions**: May break backward compatibility
- **MINOR versions**: Must maintain backward compatibility
- **PATCH versions**: Must maintain backward compatibility

### Configuration Compatibility
- Configuration files are automatically migrated
- Old environment variables still supported but deprecated
- TOML format is preferred for new configurations

### Data Compatibility
- State files are migrated with data preservation
- Download history maintained across versions
- File paths and metadata preserved

## Deprecation Timeline

### Version 1.x Features (Deprecated in 2.0.0)

| Feature | Deprecated In | Removed In | Replacement |
|---------|---------------|------------|-------------|
| `comfy_fixer.py` script | 2.0.0 | 3.0.0 | `python -m comfyfixersmart.cli` |
| Environment variable config | 2.0.0 | 3.0.0 | TOML configuration files |
| Simple JSON state format | 2.0.0 | 3.0.0 | Enhanced state management |
| Legacy CLI arguments | 2.0.0 | 3.0.0 | New CLI with compatibility layer |

### Compatibility Layer Features

| Feature | Status | Removal Timeline |
|---------|--------|------------------|
| `comfy_fixer_compat.py` | Active | 3.0.0 |
| `comfy_fixer.sh` wrapper | Active | 3.0.0 |
| `scripts/compat_wrapper.py` | Active | 3.0.0 |
| Migration prompt | Active | 2.5.0 |

## Release Schedule

### Regular Releases
- **PATCH releases**: As needed for critical fixes
- **MINOR releases**: Monthly for new features
- **MAJOR releases**: Quarterly for major changes

### Support Windows
- **Current Version**: 12 months from release
- **N-1 Version**: 6 months from release
- **N-2 Version**: 3 months from release
- **Older Versions**: Community support only

## Migration Strategy by Version

### Migrating from 1.x to 2.0.0

#### Automatic Migration
```bash
# One-command migration
python scripts/migrate_config.py && \
python scripts/migrate_state.py --backup && \
python scripts/validate_migration.py
```

#### Manual Migration
1. **Configuration**: Run `scripts/migrate_config.py`
2. **State**: Run `scripts/migrate_state.py --backup`
3. **Validation**: Run `scripts/validate_migration.py`
4. **Testing**: Test with sample workflows
5. **Cleanup**: Remove old backups after verification

#### Rollback Plan
```bash
# Emergency rollback
python scripts/rollback.py --force
```

### Future Version Migrations

#### 2.x to 3.0.0 (Planned)
- **Breaking Changes**: Removal of compatibility layer
- **Migration Required**: Update scripts and workflows
- **Timeline**: Q2 2025

#### Migration Commands for 3.0.0
```bash
# Update to new CLI permanently
sed -i 's/python comfy_fixer.py/python -m comfyfixersmart.cli/g' *.sh
sed -i 's/comfy_fixer_compat.py/comfyfixersmart.cli/g' *.sh

# Remove compatibility wrappers
rm comfy_fixer_compat.py comfy_fixer.sh
rm scripts/compat_wrapper.py
```

## Feature Flags and Experimental Features

### Current Feature Flags

| Flag | Description | Status | Version |
|------|-------------|--------|---------|
| `enable_claude_verification` | Claude AI verification | Deprecated | 2.0.0 |
| `verify_urls` | URL verification during download | Active | 2.0.0 |
| `batch_processing` | Process multiple workflows together | Active | 2.0.0 |

### Experimental Features

| Feature | Flag | Expected Version |
|---------|------|------------------|
| Multi-threading | `experimental_threading` | 2.2.0 |
| GPU acceleration | `experimental_gpu` | 2.3.0 |
| Cloud storage | `experimental_cloud` | 3.0.0 |

## Version Detection and Compatibility

### Runtime Version Detection
```python
from comfyfixersmart import __version__
print(f"ComfyFixerSmart version: {__version__}")
```

### Compatibility Checking
```python
import pkg_resources

def check_compatibility():
    try:
        version = pkg_resources.get_distribution('comfyfixersmart').version
        major, minor, patch = map(int, version.split('.'))
        return major >= 2
    except:
        return False
```

### Version Requirements
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.8"
comfyfixersmart = "^2.0.0"
```

## Communication Plan

### Version Announcements
- **Release Notes**: Published with each release
- **Migration Guides**: Updated for major versions
- **Deprecation Warnings**: Runtime warnings for deprecated features
- **Community Updates**: Forum and Discord announcements

### Support Channels
- **Documentation**: `docs/` directory
- **Issues**: GitHub issues for bugs
- **Discussions**: GitHub discussions for questions
- **Migration Support**: Dedicated migration issues

## Quality Assurance

### Release Checklist
- [ ] All tests pass
- [ ] Migration scripts tested
- [ ] Backward compatibility verified
- [ ] Documentation updated
- [ ] Release notes written
- [ ] Security review completed

### Testing Strategy
- **Unit Tests**: All modules
- **Integration Tests**: Full workflow processing
- **Migration Tests**: Upgrade from N-1 version
- **Performance Tests**: Benchmark against previous version
- **Compatibility Tests**: Multiple Python versions

## Emergency Releases

### Hotfix Process
1. **Critical Bug**: Identified and confirmed
2. **Patch Created**: Minimal fix applied
3. **Testing**: Regression tests pass
4. **Release**: PATCH version increment
5. **Communication**: Users notified of critical update

### Security Releases
1. **Vulnerability**: Identified and assessed
2. **Fix Developed**: Security patch created
3. **Review**: Security team review
4. **Release**: PATCH version with security notes
5. **Communication**: Security advisory published

---

## Version History

### Version 2.0.0
- **Date**: [Release Date]
- **Changes**:
  - Modular architecture refactor
  - TOML configuration system
  - Enhanced state management
  - New CLI with more options
  - Compatibility layer for migration
  - Comprehensive validation tools

### Version 1.x (Legacy)
- **Status**: Deprecated
- **Support**: Until [Date]
- **Features**: Monolithic script, environment config, simple state

---

*This version management strategy ensures smooth transitions while maintaining stability and backward compatibility.*