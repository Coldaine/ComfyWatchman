#!/usr/bin/env python3
"""
Documentation Structure Validator

Validates the ComfyFixerSmart documentation structure and organization.
Ensures all required files exist and follow naming conventions.
"""

import os
from pathlib import Path
from typing import List, Dict, Set

class StructureValidator:
    """Validates documentation structure."""

    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_structure(self) -> bool:
        """Validate overall documentation structure."""
        success = True

        # Check required directories
        required_dirs = [
            "user",
            "developer",
            "technical",
            "scripts"
        ]

        for dir_name in required_dirs:
            dir_path = self.docs_root / dir_name
            if not dir_path.exists():
                self.errors.append(f"Missing required directory: {dir_name}/")
                success = False
            elif not dir_path.is_dir():
                self.errors.append(f"{dir_name} is not a directory")
                success = False

        # Check required files
        required_files = [
            "README.md",
            "user/user-guide.md",
            "user/configuration.md",
            "user/cli-reference.md",
            "user/troubleshooting.md",
            "user/examples.md",
            "developer/developer-guide.md",
            "developer/architecture.md",
            "developer/api-reference.md",
            "developer/testing.md",
            "developer/release-process.md",
            "technical/migration-guide.md",
            "technical/performance.md",
            "technical/integrations.md",
            "technical/faq.md",
            "scripts/validate_links.py",
            "scripts/validate_structure.py",
            "scripts/validate_examples.py",
            "Makefile"
        ]

        for file_name in required_files:
            file_path = self.docs_root / file_name
            if not file_path.exists():
                self.errors.append(f"Missing required file: {file_name}")
                success = False
            elif not file_path.is_file():
                self.errors.append(f"{file_name} is not a regular file")
                success = False

        # Check file naming conventions
        if not self.validate_naming_conventions():
            success = False

        # Check for orphaned files
        if not self.check_for_orphaned_files():
            success = False

        return success

    def validate_naming_conventions(self) -> bool:
        """Validate file and directory naming conventions."""
        success = True

        # Check all .md files use kebab-case
        for md_file in self.docs_root.rglob("*.md"):
            if md_file.name == "README.md":
                continue  # README.md is allowed

            expected_name = md_file.name.replace('_', '-').lower()
            if md_file.name != expected_name:
                self.warnings.append(
                    f"File should use kebab-case: {md_file.name} → {expected_name}"
                )

        # Check script files have .py extension and are executable concepts
        scripts_dir = self.docs_root / "scripts"
        if scripts_dir.exists():
            for script_file in scripts_dir.glob("*"):
                if script_file.is_file() and not script_file.name.endswith('.py'):
                    self.warnings.append(
                        f"Script file should have .py extension: {script_file.name}"
                    )

        return success

    def check_for_orphaned_files(self) -> bool:
        """Check for files that might be orphaned or misplaced."""
        success = True

        # Define expected file patterns
        expected_patterns = {
            "docs/README.md",
            "docs/user/*.md",
            "docs/developer/*.md",
            "docs/technical/*.md",
            "docs/scripts/*.py",
            "docs/Makefile"
        }

        # This is a basic check - could be enhanced
        all_md_files = set(str(f.relative_to(self.docs_root))
                          for f in self.docs_root.rglob("*.md"))

        # Check for files outside expected locations
        for md_file in all_md_files:
            if not any(md_file.startswith(pattern.rstrip('*'))
                      for pattern in expected_patterns):
                self.warnings.append(f"File outside expected location: {md_file}")

        return success

    def report_results(self) -> None:
        """Report validation results."""
        if self.errors:
            print("❌ Structure validation failed:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("✅ Documentation structure is valid")

        if self.warnings:
            print("⚠️  Structure warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

def main():
    """Main validation function."""
    docs_root = Path(__file__).parent.parent

    validator = StructureValidator(docs_root)
    success = validator.validate_structure()
    validator.report_results()

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())