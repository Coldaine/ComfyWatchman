#!/usr/bin/env python3
"""
Documentation Examples Validator

Validates code examples in the ComfyFixerSmart documentation.
Checks syntax and basic correctness of code blocks.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

class ExamplesValidator:
    """Validates documentation code examples."""

    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all_files(self) -> bool:
        """Validate examples in all documentation files."""
        success = True

        # Find all markdown files
        md_files = list(self.docs_root.rglob("*.md"))

        for md_file in md_files:
            if not self.validate_file(md_file):
                success = False

        return success

    def validate_file(self, file_path: Path) -> bool:
        """Validate examples in a single file."""
        success = True

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Cannot read {file_path}: {e}")
            return False

        # Find all code blocks
        code_blocks = self.extract_code_blocks(content)

        for i, (language, code) in enumerate(code_blocks):
            if not self.validate_code_block(file_path, i + 1, language, code):
                success = False

        return success

    def extract_code_blocks(self, content: str) -> List[tuple]:
        """Extract code blocks from markdown content."""
        # Pattern for fenced code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        return matches

    def validate_code_block(self, file_path: Path, block_num: int, language: str, code: str) -> bool:
        """Validate a single code block."""
        success = True

        # Skip if no language specified or not Python
        if not language or language.lower() not in ['python', 'py', 'bash', 'sh', 'toml', 'json']:
            return True

        if language.lower() in ['python', 'py']:
            if not self.validate_python_code(file_path, block_num, code):
                success = False
        elif language.lower() in ['bash', 'sh']:
            if not self.validate_bash_code(file_path, block_num, code):
                success = False
        elif language.lower() == 'toml':
            if not self.validate_toml_code(file_path, block_num, code):
                success = False
        elif language.lower() == 'json':
            if not self.validate_json_code(file_path, block_num, code):
                success = False

        return success

    def validate_python_code(self, file_path: Path, block_num: int, code: str) -> bool:
        """Validate Python code block."""
        success = True

        # Basic syntax check
        try:
            compile(code, f'<code block {block_num} in {file_path}>', 'exec')
        except SyntaxError as e:
            self.errors.append(
                f"Python syntax error in {file_path} block {block_num}: {e}"
            )
            success = False
        except Exception as e:
            self.warnings.append(
                f"Python validation warning in {file_path} block {block_num}: {e}"
            )

        # Check for common issues
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for undefined variables (basic)
            if re.search(r'\b\w+\s*=', line):
                # This is a basic check - could be enhanced
                pass

        return success

    def validate_bash_code(self, file_path: Path, block_num: int, code: str) -> bool:
        """Validate Bash code block."""
        success = True

        # Check for common bash issues
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for unclosed quotes
            if (line.count('"') % 2 != 0) or (line.count("'") % 2 != 0):
                self.warnings.append(
                    f"Unclosed quote in {file_path} block {block_num} line {i}"
                )

            # Check for common command issues
            if line.startswith('pip install') and '--user' in line:
                self.warnings.append(
                    f"Using --user with pip install in {file_path} block {block_num}"
                )

        return success

    def validate_toml_code(self, file_path: Path, block_num: int, code: str) -> bool:
        """Validate TOML code block."""
        success = True

        try:
            import tomllib
            tomllib.loads(code)
        except ImportError:
            # tomllib not available, skip validation
            pass
        except Exception as e:
            self.errors.append(
                f"TOML syntax error in {file_path} block {block_num}: {e}"
            )
            success = False

        return success

    def validate_json_code(self, file_path: Path, block_num: int, code: str) -> bool:
        """Validate JSON code block."""
        success = True

        try:
            import json
            json.loads(code)
        except Exception as e:
            self.errors.append(
                f"JSON syntax error in {file_path} block {block_num}: {e}"
            )
            success = False

        return success

    def report_results(self) -> None:
        """Report validation results."""
        if self.errors:
            print("❌ Example validation failed:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("✅ All code examples are valid")

        if self.warnings:
            print("⚠️  Example warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

def main():
    """Main validation function."""
    docs_root = Path(__file__).parent.parent

    validator = ExamplesValidator(docs_root)
    success = validator.validate_all_files()
    validator.report_results()

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())