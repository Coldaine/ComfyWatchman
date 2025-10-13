# ComfyFixerSmart Documentation Build System
#
# This Makefile provides targets for building, validating, and maintaining
# the ComfyFixerSmart documentation.
#
# Usage:
#   make help          # Show available targets
#   make docs          # Build all documentation
#   make validate-docs # Validate documentation
#   make clean-docs    # Clean build artifacts

.PHONY: help docs validate-docs clean-docs check-links check-structure check-examples

# Default target
help:
	@echo "ComfyFixerSmart Documentation Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  docs          - Build all documentation"
	@echo "  validate-docs - Validate documentation structure and links"
	@echo "  clean-docs    - Clean documentation build artifacts"
	@echo "  check-links   - Check internal links"
	@echo "  check-structure - Validate documentation structure"
	@echo "  check-examples  - Validate code examples"
	@echo "  help          - Show this help message"

# Build documentation
docs: check-structure check-links check-examples
	@echo "✓ Documentation build complete"

# Validate documentation
validate-docs: check-structure check-links check-examples
	@echo "✓ Documentation validation complete"

# Clean build artifacts
clean-docs:
	@echo "Cleaning documentation build artifacts..."
	@find docs/ -name "*.tmp" -delete 2>/dev/null || true
	@find docs/ -name "*~" -delete 2>/dev/null || true
	@find docs/ -name "*.bak" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

# Check internal links
check-links:
	@echo "Checking internal documentation links..."
	@python scripts/validate_links.py
	@echo "✓ Link validation complete"

# Check documentation structure
check-structure:
	@echo "Validating documentation structure..."
	@python scripts/validate_structure.py
	@echo "✓ Structure validation complete"

# Check code examples
check-examples:
	@echo "Validating code examples..."
	@python scripts/validate_examples.py
	@echo "✓ Example validation complete"

# Development targets
dev-setup:
	@echo "Setting up documentation development environment..."
	@pip install -r docs/requirements.txt
	@echo "✓ Development environment ready"

dev-serve:
	@echo "Starting documentation development server..."
	@python scripts/serve_docs.py

# CI/CD targets
ci-validate:
	@echo "Running CI documentation validation..."
	@make validate-docs
	@echo "✓ CI validation complete"

ci-build:
	@echo "Running CI documentation build..."
	@make docs
	@echo "✓ CI build complete"