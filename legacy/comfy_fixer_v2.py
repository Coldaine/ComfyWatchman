#!/usr/bin/env python3
"""
ComfyFixerSmart v2 - Refactored with shared modules
Improved with state tracking, better validation, per-run isolation

Usage:
   python comfy_fixer_v2.py                    # Scan all workflows
   python comfy_fixer_v2.py workflow.json      # Scan specific workflow
   python comfy_fixer_v2.py --retry-failed     # Retry failed downloads
   python comfy_fixer_v2.py --stats            # Show download statistics

Requirements:
- CIVITAI_API_KEY in ~/.secrets
- requests library: pip install requests
"""

import argparse
import sys
from datetime import datetime

from src.comfyfixersmart.config import config
from src.comfyfixersmart.logging import get_logger
from src.comfyfixersmart.state_manager import StateManager
from src.comfyfixersmart.core import run_v2_compatibility_mode

# Initialize logger
logger = get_logger("ComfyFixerSmart_v2")


def main():
    """Main entry point for ComfyFixerSmart v2."""
    parser = argparse.ArgumentParser(description='ComfyFixerSmart v2 with state tracking')
    parser.add_argument('workflows', nargs='*', help='Specific workflow files to scan (optional)')
    parser.add_argument('--retry-failed', action='store_true', help='Clear failed downloads and retry')
    parser.add_argument('--stats', action='store_true', help='Show download statistics')

    args = parser.parse_args()

    # Handle stats request
    if args.stats:
        state_manager = StateManager()
        stats = state_manager.get_stats()
        print("\n=== Download Statistics ===")
        print(f"Unique models tracked: {stats['total_unique_models']}")
        print(f"Total attempts: {stats['total_attempts']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Pending: {stats['pending']}")
        return

    logger.info("=" * 70)
    logger.info("ComfyFixerSmart v2 - Starting")
    logger.info("=" * 70)

    try:
        # Run workflow analysis using shared modules
        run_result = run_v2_compatibility_mode(
            specific_workflows=args.workflows if args.workflows else None,
            retry_failed=args.retry_failed,
            logger=logger
        )

        # Log results
        if run_result.status == 'completed':
            logger.info("✓ Analysis completed successfully!")
            if run_result.download_script:
                logger.info(f"Download script ready: {run_result.download_script}")

            # Show current state stats
            state_manager = StateManager()
            stats = state_manager.get_stats()
            logger.info(f"\nCurrent download state:")
            logger.info(f"  Successfully downloaded: {stats['successful']}")
            logger.info(f"  Failed: {stats['failed']}")

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