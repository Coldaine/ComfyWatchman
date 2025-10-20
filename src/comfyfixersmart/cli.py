"""Command Line Interface for ComfyFixerSmart."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .config import config
from .logging import get_logger
from .core import run_comfy_fixer, run_v1_compatibility_mode, run_v2_compatibility_mode


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="comfywatchman",
        description="ComfyFixerSmart - Incremental ComfyUI model downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  comfywatchman                          # Analyze all workflows in default directories
  comfywatchman workflow.json            # Analyze specific workflow file
  comfywatchman --dir /path/to/workflows  # Analyze workflows in specific directory
  comfywatchman --search civitai,huggingface  # Use specific search backends
  comfywatchman inspect model.safetensors  # Inspect a single model file
        """,
    )

    # Input options
    parser.add_argument(
        "workflows",
        nargs="*",
        help="Specific workflow files to analyze",
    )

    parser.add_argument(
        "--dir",
        "--workflow-dir",
        action="append",
        dest="workflow_dirs",
        help="Directory to scan for workflow files (can be used multiple times)",
    )

    # Search options
    parser.add_argument(
        "--search",
        "--backends",
        default="civitai",
        help="Comma-separated list of search backends (default: civitai)",
    )

    # Mode options
    parser.add_argument(
        "--v1",
        action="store_true",
        help="Use v1 compatibility mode (incremental processing)",
    )

    parser.add_argument(
        "--v2",
        action="store_true",
        help="Use v2 compatibility mode (batch processing, default)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=f"Output directory for results (default: {config.output_dir})",
    )

    parser.add_argument(
        "--no-script",
        action="store_true",
        help="Skip generating download script",
    )

    parser.add_argument(
        "--verify-urls",
        action="store_true",
        help="Enable URL verification during downloads",
    )

    # Configuration
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    parser.add_argument(
        "--comfyui-root",
        type=Path,
        help="Path to ComfyUI installation (required if not configured)",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0",
    )

    return parser


def create_inspect_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="comfywatchman inspect",
        description="Inspect model metadata without loading tensors.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Paths to files or directories to inspect",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively inspect directories",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--summary",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Toggle condensed text output (default: enabled)",
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Compute SHA256 hashes (can be slow)",
    )
    parser.add_argument(
        "--unsafe",
        action="store_true",
        help="Allow unsafe torch.load for pickle checkpoints",
    )
    parser.add_argument(
        "--components",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include per-component listings for Diffusers directories",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error output",
    )
    return parser


def setup_logging(log_level: str, quiet: bool) -> None:
    """Setup logging configuration."""
    import logging

    if quiet:
        log_level = "ERROR"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def update_config_from_args(args: argparse.Namespace) -> None:
    """Update global config from command line arguments."""
    global config

    if getattr(args, "config", None) and args.config.exists():
        config.load_from_file(args.config)

    if getattr(args, "output_dir", None):
        config.output_dir = args.output_dir
    if getattr(args, "comfyui_root", None):
        config.comfyui_root = args.comfyui_root


def _run_inspect_command(args: argparse.Namespace) -> int:
    from .inspector import inspect_paths

    include_components = getattr(args, "components", True)
    results = inspect_paths(
        args.paths,
        recursive=args.recursive,
        fmt=args.format,
        summary=args.summary,
        do_hash=args.hash,
        unsafe=args.unsafe,
        include_components=include_components,
    )

    if args.format == "json":
        payload: object
        if isinstance(results, list) and len(results) == 1:
            payload = results[0]
        else:
            payload = results
        print(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            flush=True,
        )
    else:
        print(results, flush=True)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    raw_args = list(sys.argv[1:] if argv is None else argv)

    if raw_args and raw_args[0] == "inspect":
        inspect_parser = create_inspect_parser()
        inspect_args = inspect_parser.parse_args(raw_args[1:])
        setup_logging(inspect_args.log_level, inspect_args.quiet)
        return _run_inspect_command(inspect_args)

    parser = create_parser()
    args = parser.parse_args(raw_args)

    setup_logging(getattr(args, "log_level", "INFO"), getattr(args, "quiet", False))

    logger = get_logger("ComfyFixerCLI")

    try:
        update_config_from_args(args)

        search_backends = [b.strip() for b in args.search.split(",")] if args.search else ["civitai"]

        workflow_dirs = args.workflow_dirs or [str(d) for d in config.workflow_dirs]

        logger.info("=" * 70)
        logger.info("ComfyFixerSmart v2.0.0 - Starting Analysis")
        logger.info("=" * 70)
        logger.info(f"Workflow directories: {workflow_dirs}")
        logger.info(f"Search backends: {search_backends}")
        logger.info(f"Output directory: {config.output_dir}")

        if args.v1:
            logger.info("Running in V1 compatibility mode (incremental)")
            result = run_v1_compatibility_mode(
                specific_workflows=args.workflows if args.workflows else None,
                verify_urls=args.verify_urls,
            )
        elif args.v2 or (not args.v1 and not args.v2):
            logger.info("Running in V2 mode (batch processing)")
            result = run_v2_compatibility_mode(
                specific_workflows=args.workflows if args.workflows else None,
                retry_failed=False,
            )
        else:
            logger.info("Running unified analysis")
            from .core import ComfyFixerCore

            core = ComfyFixerCore(logger=logger)
            result = core.run_workflow_analysis(
                specific_workflows=args.workflows,
                workflow_dirs=workflow_dirs,
                search_backends=search_backends,
                generate_script=not args.no_script,
                verify_urls=args.verify_urls,
            )

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
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"Unexpected error: {exc}")
        if getattr(args, "log_level", "INFO") == "DEBUG":
            import traceback

            logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())

