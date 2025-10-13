"""
Command Line Interface for ComfyFixerSmart

Provides CLI entry points for running ComfyFixerSmart from the command line.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import config
from .logging import get_logger
from .core import run_comfy_fixer, run_v1_compatibility_mode, run_v2_compatibility_mode


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="comfyfixer",
        description="ComfyFixerSmart - Incremental ComfyUI model downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  comfyfixer                          # Analyze all workflows in default directories
  comfyfixer workflow.json            # Analyze specific workflow file
  comfyfixer --dir /path/to/workflows  # Analyze workflows in specific directory
  comfyfixer --search civitai,huggingface  # Use specific search backends
  comfyfixer --v1                      # Use v1 compatibility mode
  comfyfixer --v2                      # Use v2 compatibility mode (default)
        """
    )

    # Input options
    parser.add_argument(
        'workflows',
        nargs='*',
        help='Specific workflow files to analyze'
    )

    parser.add_argument(
        '--dir', '--workflow-dir',
        action='append',
        dest='workflow_dirs',
        help='Directory to scan for workflow files (can be used multiple times)'
    )

    # Search options
    parser.add_argument(
        '--search', '--backends',
        default='civitai',
        help='Comma-separated list of search backends (default: civitai)'
    )

    # Mode options
    parser.add_argument(
        '--v1',
        action='store_true',
        help='Use v1 compatibility mode (incremental processing)'
    )

    parser.add_argument(
        '--v2',
        action='store_true',
        help='Use v2 compatibility mode (batch processing, default)'
    )

    # Output options
    parser.add_argument(
        '--output-dir',
        type=Path,
        help=f'Output directory for results (default: {config.output_dir})'
    )

    parser.add_argument(
        '--no-script',
        action='store_true',
        help='Skip generating download script'
    )

    parser.add_argument(
        '--verify-urls',
        action='store_true',
        help='Enable URL verification during downloads'
    )

    # Configuration
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file'
    )

    parser.add_argument(
        '--comfyui-root',
        type=Path,
        help='Path to ComfyUI installation (required if not configured)'
    )

    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress non-error output'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s 2.0.0'
    )

    return parser


def setup_logging(log_level: str, quiet: bool) -> None:
    """Setup logging configuration."""
    import logging

    if quiet:
        log_level = 'ERROR'

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def update_config_from_args(args: argparse.Namespace) -> None:
    """Update global config from command line arguments."""
    global config

    if args.config and args.config.exists():
        # Load config from file if specified
        config.load_from_file(args.config)

    # Override with command line arguments
    if args.output_dir:
        config.output_dir = args.output_dir
    if args.comfyui_root:
        config.comfyui_root = args.comfyui_root


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.quiet)

    logger = get_logger("ComfyFixerCLI")

    try:
        # Update configuration
        update_config_from_args(args)

        # Parse search backends
        search_backends = [b.strip() for b in args.search.split(',')] if args.search else ['civitai']

        # Determine workflow directories
        workflow_dirs = args.workflow_dirs
        if not workflow_dirs:
            workflow_dirs = [str(d) for d in config.workflow_dirs]

        logger.info("=" * 70)
        logger.info("ComfyFixerSmart v2.0.0 - Starting Analysis")
        logger.info("=" * 70)
        logger.info(f"Workflow directories: {workflow_dirs}")
        logger.info(f"Search backends: {search_backends}")
        logger.info(f"Output directory: {config.output_dir}")

        # Determine which mode to run
        if args.v1:
            # V1 compatibility mode
            logger.info("Running in V1 compatibility mode (incremental)")
            result = run_v1_compatibility_mode(
                specific_workflows=args.workflows if args.workflows else None,
                verify_urls=args.verify_urls
            )
        elif args.v2 or (not args.v1 and not args.v2):
            # V2 mode (default)
            logger.info("Running in V2 mode (batch processing)")
            result = run_v2_compatibility_mode(
                specific_workflows=args.workflows if args.workflows else None,
                retry_failed=False  # Could add --retry flag later
            )
        else:
            # Unified mode using ComfyFixerCore
            logger.info("Running unified analysis")
            from .core import ComfyFixerCore

            core = ComfyFixerCore(logger=logger)
            result = core.run_workflow_analysis(
                specific_workflows=args.workflows,
                workflow_dirs=workflow_dirs,
                search_backends=search_backends,
                generate_script=not args.no_script,
                verify_urls=args.verify_urls
            )

        # Report results
        if result:
            logger.info("=" * 70)
            logger.info("Analysis Complete!")
            logger.info("=" * 70)
            logger.info(f"Status: {result.status}")
            logger.info(f"Workflows scanned: {result.workflows_scanned}")
            logger.info(f"Models found: {result.models_found}")
            logger.info(f"Models missing: {result.models_missing}")
            logger.info(f"Models resolved: {result.models_resolved}")

            if result.download_script:
                logger.info(f"Download script: {result.download_script}")

            if result.errors:
                logger.warning("Errors encountered:")
                for error in result.errors:
                    logger.warning(f"  - {error}")
                return 1
        else:
            logger.error("Analysis failed - no results returned")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.log_level == 'DEBUG':
            import traceback
            logger.debug(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())