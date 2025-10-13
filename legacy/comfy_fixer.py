#!/usr/bin/env python3
"""
ComfyFixerSmart v1 - Refactored with shared modules
Analyzes workflows, finds missing models, downloads from Civitai

Usage:
   python comfy_fixer.py                    # Standard workflow (Civitai search)
   python comfy_fixer.py --verify-urls      # Enable Qwen-based search
   python comfy_fixer.py workflow.json      # Scan specific workflow

Options:
   --verify-urls    Enable Qwen-based search (adds processing time)
   --help           Show this help message

Requirements:
- CIVITAI_API_KEY in ~/.secrets
- requests library: pip install requests
- Qwen CLI (optional, only needed for --verify-urls)
"""

import argparse
import sys
from datetime import datetime

from src.comfyfixersmart.config import config
from src.comfyfixersmart.logging import get_logger
from src.comfyfixersmart.core import run_v1_compatibility_mode

# Initialize logger
logger = get_logger("ComfyFixerSmart")


def main():
    """Main entry point for ComfyFixerSmart v1."""
    parser = argparse.ArgumentParser(description='ComfyFixerSmart v1 - Model discovery and download')
    parser.add_argument('workflows', nargs='*', help='Specific workflow files to scan (optional)')
    parser.add_argument('--verify-urls', action='store_true',
                       help='Enable Qwen-based search for better accuracy')

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("ComfyFixerSmart v1 - Starting")
    logger.info("=" * 70)

    try:
        # Run workflow analysis using shared modules
        run_result = run_v1_compatibility_mode(
            specific_workflows=args.workflows if args.workflows else None,
            verify_urls=args.verify_urls,
            logger=logger
        )

        # Log results
        if run_result.status == 'completed':
            logger.info("✓ Analysis completed successfully!")
            if run_result.download_script:
                logger.info(f"Download script ready: {run_result.download_script}")
        else:
            logger.error(f"Analysis failed: {run_result.errors}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()