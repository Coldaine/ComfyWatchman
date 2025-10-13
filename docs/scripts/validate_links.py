#!/usr/bin/env python3
"""
Documentation Link Validator

Validates internal links in the ComfyFixerSmart documentation.
Checks for broken relative links and missing files.
"""

import os
import re
from pathlib import Path
from typing import List, Set, Dict
from urllib.parse import urlparse

class LinkValidator:
    """Validates documentation links."""

    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all_files(self) -> bool:
        """Validate links in all documentation files."""
        success = True

        # Find all markdown files
        md_files = list(self.docs_root.rglob("*.md"))

        for md_file in md_files:
            if not self.validate_file(md_file):
                success = False

        return success

    def validate_file(self, file_path: Path) -> bool:
        """Validate links in a single file."""
        success = True

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Cannot read {file_path}: {e}")
            return False

        # Find all markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)

        for link_text, link_url in links:
            if not self.validate_link(file_path, link_url):
                success = False

        return success

    def validate_link(self, source_file: Path, link_url: str) -> bool:
        """Validate a single link."""
        # Skip external URLs
        if link_url.startswith(('http://', 'https://', 'mailto:')):
            return True

        # Skip anchor links (for now)
        if link_url.startswith('#'):
            return True

        # Handle relative links
        if not link_url.startswith('/'):
            # Relative to current file's directory
            base_dir = source_file.parent
            target_path = (base_dir / link_url).resolve()

            # Try as .md file if no extension
            if not target_path.suffix and not target_path.exists():
                target_path = target_path.with_suffix('.md')

            if not target_path.exists():
                # Try relative to docs root
                target_path = (self.docs_root / link_url).resolve()
                if not target_path.suffix and not target_path.exists():
                    target_path = target_path.with_suffix('.md')

            if not target_path.exists():
                self.errors.append(f"Broken link in {source_file}: {link_url}")
                return False

        return True

    def report_results(self) -> None:
        """Report validation results."""
        if self.errors:
            print("❌ Link validation failed:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("✅ All links are valid")

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

def main():
    """Main validation function."""
    docs_root = Path(__file__).parent.parent

    validator = LinkValidator(docs_root)
    success = validator.validate_all_files()
    validator.report_results()

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())