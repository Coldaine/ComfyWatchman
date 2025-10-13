# Release Process

This document outlines the process for releasing new versions of ComfyFixerSmart.

## Version Numbering

ComfyFixerSmart follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 2.1.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Release Types

### Major Release (X.0.0)

- Breaking API changes
- Major feature additions
- Significant architectural changes
- Requires migration guide

### Minor Release (x.Y.0)

- New features
- Enhancements
- Backward compatible
- May include deprecation warnings

### Patch Release (x.y.Z)

- Bug fixes
- Security updates
- Documentation improvements
- Performance optimizations

## Pre-Release Checklist

### Code Quality

- [ ] All tests pass (`pytest`)
- [ ] Code formatted (`black .`)
- [ ] Linting passes (`flake8 src/`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Test coverage ≥ 85% (`pytest --cov=comfyfixersmart`)
- [ ] No security vulnerabilities (`safety check`)

### Documentation

- [ ] API documentation updated
- [ ] User guide updated for new features
- [ ] Configuration documentation updated
- [ ] Examples updated
- [ ] Changelog updated
- [ ] Migration guide created (for breaking changes)

### Testing

- [ ] Unit tests cover new code
- [ ] Integration tests pass
- [ ] End-to-end tests pass
- [ ] Cross-platform testing (Linux, macOS, Windows)
- [ ] Performance regression testing

### Compatibility

- [ ] Python version compatibility verified (3.7+)
- [ ] Dependencies updated and tested
- [ ] Breaking changes documented
- [ ] Deprecation warnings added for removed features

## Release Process

### 1. Prepare Release Branch

```bash
# Create release branch
git checkout -b release/v2.1.0

# Update version in source
echo "2.1.0" > VERSION
# Update __version__ in src/comfyfixersmart/__init__.py
```

### 2. Update Changelog

Update `CHANGELOG.md` with new version:

```markdown
## [2.1.0] - 2025-10-12

### Added
- New feature description
- Another new feature

### Changed
- Modified behavior description

### Fixed
- Bug fix description

### Removed
- Deprecated feature removal
```

### 3. Final Testing

```bash
# Run full test suite
pytest --cov=comfyfixersmart --cov-report=html

# Build package
python -m build

# Test installation
pip install dist/comfyfixersmart-2.1.0.tar.gz --force-reinstall

# Test basic functionality
comfyfixer --version
comfyfixer --validate-config
```

### 4. Create Git Tag

```bash
# Commit changes
git add .
git commit -m "Release v2.1.0"

# Create annotated tag
git tag -a v2.1.0 -m "Release version 2.1.0

## Changes
- New feature description
- Bug fixes
- Documentation updates

## Breaking Changes
- None

## Migration
- No migration required"

# Push tag
git push origin v2.1.0
```

### 5. Build and Publish

#### PyPI Release

```bash
# Build distributions
python -m build

# Upload to PyPI (requires API token)
twine upload dist/*

# Or upload to TestPyPI first
twine upload --repository testpypi dist/*
```

#### GitHub Release

1. Go to GitHub Releases
2. Create new release from tag `v2.1.0`
3. Title: "ComfyFixerSmart v2.1.0"
4. Description: Copy from changelog
5. Upload built distributions
6. Publish release

### 6. Post-Release Tasks

```bash
# Merge release branch
git checkout main
git merge release/v2.1.0

# Delete release branch
git branch -d release/v2.1.0

# Push main branch
git push origin main

# Update develop branch if exists
git checkout develop
git merge main
git push origin develop
```

### 7. Announce Release

- Update project website/README badges
- Post in community forums
- Send release notes to mailing list
- Update social media

## Hotfix Releases

For critical bug fixes:

1. Create hotfix branch from last release tag
2. Make minimal changes
3. Test thoroughly
4. Release as patch version
5. Merge back to main and develop

## Automated Releases

### GitHub Actions CI/CD

Example workflow for automated releases:

```yaml
name: Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install build twine
    - name: Build
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### Release Automation Tools

Consider using:
- `semantic-release` for automated versioning
- `release-please` for GitHub-managed releases
- `cibuildwheel` for cross-platform wheels

## Rollback Process

If a release has issues:

1. **Immediate rollback**: Delete GitHub release, re-upload fixed version
2. **Patch release**: If minor issues, release patch version
3. **Hotfix**: For critical issues, create hotfix release
4. **Major rollback**: If severe issues, yank from PyPI and release new version

## Distribution Channels

### Primary

- **PyPI**: `pip install comfyfixersmart`
- **GitHub Releases**: Pre-built binaries and source
- **Docker Hub**: Container images (future)

### Secondary

- **Conda Forge**: Community package
- **Homebrew**: macOS/Linux package
- **Snap/Flatpak**: Desktop packages

## Security Releases

For security fixes:

1. **Private coordination**: Fix developed privately
2. **Simultaneous release**: Release fix and security advisory together
3. **CVE assignment**: If applicable, assign CVE number
4. **User notification**: Clear communication of risk and mitigation

## Maintenance Releases

### Long-term Support (LTS)

- **LTS versions**: Selected major versions get extended support
- **Bug fixes**: 2 years of support
- **Security fixes**: 3 years of support
- **Current LTS**: v2.x (until v4.0 release)

### End-of-Life Process

1. **Deprecation warning**: 6 months advance notice
2. **Final release**: Last patch release
3. **Archive**: Move to archive repository
4. **Security only**: Critical security fixes only

## Release Cadence

### Regular Releases

- **Major**: As needed (breaking changes)
- **Minor**: Monthly (feature releases)
- **Patch**: As needed (bug fixes)

### Time-based Releases

- **Feature freeze**: Last week of month
- **Release**: First week of following month
- **Hotfixes**: As needed

## Communication

### Internal Communication

- **Release planning**: Weekly sync meetings
- **Status updates**: Daily standups during release week
- **Blocker resolution**: Immediate escalation

### External Communication

- **Release notes**: Detailed changelog
- **Migration guides**: For breaking changes
- **Deprecation notices**: 2 releases advance notice
- **Security advisories**: Immediate notification

## Quality Gates

### Code Review Requirements

- **Minimum reviewers**: 2 maintainers
- **Automated checks**: Must pass CI
- **Security review**: For sensitive changes
- **Performance review**: For performance-impacting changes

### Testing Requirements

- **Unit test coverage**: ≥ 85%
- **Integration tests**: All pass
- **Manual testing**: Key user workflows
- **Compatibility testing**: Multiple Python versions

### Documentation Requirements

- **API documentation**: Complete and accurate
- **User guides**: Updated for new features
- **Examples**: Working code examples
- **Changelog**: Detailed change descriptions

This release process ensures high-quality, well-tested releases that maintain backward compatibility and provide clear communication to users.