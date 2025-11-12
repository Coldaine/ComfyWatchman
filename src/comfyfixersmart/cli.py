"""Command Line Interface for ComfyFixerSmart."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .config import config
from .logging import get_logger
from .core import run_comfy_fixer, run_v1_compatibility_mode, run_v2_compatibility_mode
from .scheduler import Scheduler


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

    parser.add_argument(
        "--run-cycle",
        action="store_true",
        help="Run a single guarded scheduler cycle",
    )

    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start the automated scheduler loop",
    )

    parser.add_argument(
        "--status-report",
        action="store_true",
        help="Regenerate the master status report from the last cycle",
    )

    parser.add_argument(
        "--list-intake",
        action="store_true",
        help="List recent external workflow intake acknowledgments",
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


def _add_bool_toggle(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    help_enable: str,
    help_disable: str,
    default: bool,
) -> None:
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(f"--{name}", dest=name, action="store_true", help=help_enable)
    group.add_argument(f"--no-{name}", dest=name, action="store_false", help=help_disable)
    parser.set_defaults(**{name: default})


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
    _add_bool_toggle(
        parser,
        name="summary",
        help_enable="Show condensed text output (default)",
        help_disable="Show expanded metadata section in text output",
        default=True,
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
    _add_bool_toggle(
        parser,
        name="components",
        help_enable="Include per-component listings for Diffusers directories (default)",
        help_disable="Exclude per-component listings for Diffusers directories",
        default=True,
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
        json_results = results
    else:
        json_results = inspect_paths(
            args.paths,
            recursive=args.recursive,
            fmt="json",
            summary=args.summary,
            do_hash=args.hash,
            unsafe=args.unsafe,
            include_components=include_components,
        )

    items = json_results if isinstance(json_results, list) else [json_results]
    exit_code = 1 if any((item.get("warnings") for item in items if isinstance(item, dict) and item.get("warnings"))) else 0

    if args.format == "json":
        payload: object
        if isinstance(json_results, list) and len(json_results) == 1:
            payload = json_results[0]
        else:
            payload = json_results
        print(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            flush=True,
        )
    else:
        print(results, flush=True)
    return exit_code


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

        scheduler_actions = any(
            [
                getattr(args, 'scheduler', False),
                getattr(args, 'run_cycle', False),
                getattr(args, 'status_report', False),
                getattr(args, 'list_intake', False),
            ]
        )

        if scheduler_actions:
            scheduler = Scheduler(logger=logger)
            executed_action = False

            if getattr(args, 'list_intake', False):
                events = scheduler.list_recent_intake()
                print(json.dumps(events, indent=2, ensure_ascii=False))
                executed_action = True

            if getattr(args, 'status_report', False):
                artifacts = scheduler.regenerate_status_report()
                executed_action = True
                if not artifacts:
                    logger.error("Unable to regenerate status report; no previous cycle found")
                    return 1
                logger.info(f"Status report refreshed: {artifacts.json_path}")

            if getattr(args, 'run_cycle', False):
                result = scheduler.run_cycle(force=True)
                return 0 if result else 1

            if getattr(args, 'scheduler', False):
                scheduler.run_forever()
                return 0

            if executed_action:
                return 0

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
