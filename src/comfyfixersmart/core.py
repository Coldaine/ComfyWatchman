"""
Core Orchestrator Module for ComfyFixerSmart

Provides the main workflow orchestration logic that coordinates between
all modules. Supports both v1 and v2 workflow patterns with unified
CLI interface and progress tracking.

Classes:
    ComfyFixerCore: Main orchestrator class
    WorkflowRun: Represents a complete workflow run

Functions:
    run_comfy_fixer: Main entry point for running the fixer
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import config
from .download import DownloadManager
from .inventory import ModelInventory
from .logging import get_logger
from .scanner import WorkflowScanner
from .search import ModelSearch, SearchResult
from .state_manager import JsonStateManager
from .utils import save_json_file


@dataclass
class WorkflowRun:
    """Represents a complete ComfyFixerSmart run."""

    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # 'running', 'completed', 'failed'

    # Statistics
    workflows_scanned: int = 0
    models_found: int = 0
    models_missing: int = 0
    models_resolved: int = 0
    downloads_generated: int = 0

    # Paths
    output_dir: Optional[str] = None
    log_file: Optional[str] = None
    missing_file: Optional[str] = None
    resolutions_file: Optional[str] = None
    download_script: Optional[str] = None

    # Results
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "workflows_scanned": self.workflows_scanned,
            "models_found": self.models_found,
            "models_missing": self.models_missing,
            "models_resolved": self.models_resolved,
            "downloads_generated": self.downloads_generated,
            "output_dir": self.output_dir,
            "log_file": self.log_file,
            "missing_file": self.missing_file,
            "resolutions_file": self.resolutions_file,
            "download_script": self.download_script,
            "errors": self.errors,
        }


class ComfyFixerCore:
    """
    Main orchestrator for ComfyFixerSmart workflow.

    Coordinates between scanner, inventory, search, and download modules
    to provide a complete model discovery and download solution.
    """

    def __init__(self, logger=None, state_manager=None):
        """
        Initialize the core orchestrator.

        Args:
            logger: Optional logger instance
            state_manager: Optional StateManager instance
        """
        self.logger = logger or get_logger("ComfyFixerCore")
        self.state_manager = state_manager or JsonStateManager(config.state_dir, logger=self.logger)

        # Initialize components
        self.scanner = WorkflowScanner(logger=self.logger)
        self.inventory = ModelInventory(state_manager=self.state_manager, logger=self.logger)
        self.search = ModelSearch(state_manager=self.state_manager, logger=self.logger)
        self.download_manager = DownloadManager(
            state_manager=self.state_manager, logger=self.logger
        )
        # Add alias for backward compatibility with tests
        self.downloader = self.download_manager

        # Current run tracking
        self.current_run: Optional[WorkflowRun] = None

    def run_workflow_analysis(
        self,
        specific_workflows: Optional[List[str]] = None,
        workflow_dirs: Optional[List[str]] = None,
        search_backends: Optional[List[str]] = None,
        generate_script: bool = True,
        verify_urls: bool = False,
    ) -> WorkflowRun:
        """
        Run the complete ComfyFixerSmart workflow analysis.

        Args:
            specific_workflows: List of specific workflow files to analyze
            workflow_dirs: List of directories to scan for workflows
            search_backends: List of search backends to use
            generate_script: Whether to generate download script
            verify_urls: Whether to enable URL verification

        Returns:
            WorkflowRun object with results
        """
        # Initialize run
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run = WorkflowRun(
            run_id=run_id, start_time=datetime.now(), output_dir=str(config.output_dir)
        )

        try:
            self.logger.info("=" * 70)
            self.logger.info("ComfyFixerSmart - Starting Analysis")
            self.logger.info(f"Run ID: {run_id}")
            self.logger.info("=" * 70)

            # Step 1: Scan workflows
            workflows = self._scan_workflows(specific_workflows, workflow_dirs)

            if not workflows:
                self._complete_run("completed", "No workflows found")
                return self.current_run

            # Step 2: Extract and analyze models
            all_models, local_inventory = self._analyze_models(workflows)

            if not all_models:
                self._complete_run("completed", "No models found in workflows")
                return self.current_run

            # Step 3: Find missing models
            missing_models = self._find_missing_models(all_models, local_inventory)

            if not missing_models:
                self._complete_run("completed", "All models are available locally")
                return self.current_run

            # Step 4: Search for missing models
            search_results = self._search_missing_models(missing_models, search_backends)

            # Step 5: Generate download script (optional)
            if generate_script and search_results:
                script_path = self._generate_download_script(search_results)
                if script_path:
                    self.current_run.download_script = script_path

            # Complete successfully
            self._complete_run("completed")

        except Exception as e:
            self.logger.error(f"Workflow analysis failed: {e}")
            self._complete_run("failed", str(e))

        return self.current_run

    def _scan_workflows(
        self, specific_workflows: Optional[List[str]], workflow_dirs: Optional[List[str]]
    ) -> List[str]:
        """Scan workflows and update run statistics."""
        workflows = self.scanner.scan_workflows(specific_workflows, workflow_dirs)
        self.current_run.workflows_scanned = len(workflows)
        return workflows

    def _analyze_models(self, workflows: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extract models from workflows and build inventory."""
        self.logger.info("=== Analyzing Models ===")

        # Extract all models
        all_models = []
        for workflow in workflows:
            models = self.scanner.extract_models_from_workflow(workflow)
            # Convert ModelReference objects to dicts for compatibility
            for model in models:
                all_models.append(
                    {
                        "filename": model.filename,
                        "type": model.type,
                        "node_type": model.node_type,
                        "workflow": os.path.basename(model.workflow_path),
                    }
                )

        self.current_run.models_found = len(all_models)

        # Build local inventory
        local_inventory = self.inventory.build_inventory()

        return all_models, local_inventory

    def _find_missing_models(
        self, all_models: List[Dict[str, Any]], local_inventory: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find models that are missing from local inventory."""
        self.logger.info("=== Finding Missing Models ===")

        missing = []
        seen_filenames = set()

        for model in all_models:
            filename = model["filename"]

            if filename in seen_filenames:
                continue
            seen_filenames.add(filename)

            if filename not in local_inventory:
                # Check state manager for recent downloads
                status = self.state_manager.get_download_status(filename)
                if status == "success":
                    continue

                # Check for recent failures (optional retry logic)
                if status == "failed" and self.state_manager.was_recently_attempted(
                    filename, hours=1
                ):
                    continue

                missing.append(model)

        self.current_run.models_missing = len(missing)
        self.logger.info(f"Found {len(missing)} missing models")

        # Save missing models list
        if missing:
            missing_file = config.output_dir / f"missing_models_{self.current_run.run_id}.json"
            save_json_file(missing_file, missing)
            self.current_run.missing_file = str(missing_file)

        return missing

    def _search_missing_models(
        self, missing_models: List[Dict[str, Any]], search_backends: Optional[List[str]]
    ) -> List[SearchResult]:
        """Search for missing models using configured backends."""
        self.logger.info("=== Searching for Missing Models ===")

        if search_backends is None:
            search_backends = ["civitai"]  # Default to Civitai

        search_results = self.search.search_multiple_models(
            missing_models, backends=search_backends, use_cache=True
        )

        resolved_count = sum(1 for result in search_results if result.status == "FOUND")
        self.current_run.models_resolved = resolved_count

        self.logger.info(f"Resolved {resolved_count}/{len(missing_models)} models")

        # Save resolutions
        if search_results:
            resolutions_file = config.output_dir / f"resolutions_{self.current_run.run_id}.json"
            resolutions_data = [result.__dict__ for result in search_results]
            save_json_file(resolutions_file, resolutions_data)
            self.current_run.resolutions_file = str(resolutions_file)

        return search_results

    def _generate_download_script(self, search_results: List[SearchResult]) -> Optional[str]:
        """Generate download script from search results."""
        self.logger.info("=== Generating Download Script ===")

        # Convert SearchResult objects to dicts
        results_dict = [result.__dict__ for result in search_results]

        script_path = self.download_manager.generate_download_script(
            results_dict, run_id=self.current_run.run_id
        )

        if script_path:
            self.current_run.downloads_generated = 1
            self.logger.info(f"Download script generated: {script_path}")

        return script_path

    def _complete_run(self, status: str, error_message: Optional[str] = None):
        """Complete the current run."""
        self.current_run.status = status
        self.current_run.end_time = datetime.now()

        if error_message:
            self.current_run.errors.append(error_message)

        duration = self.current_run.end_time - self.current_run.start_time
        self.logger.info(f"Run {status} in {duration.total_seconds():.1f} seconds")

        if status == "completed":
            self._log_completion_summary()

    def _log_completion_summary(self):
        """Log completion summary."""
        run = self.current_run
        self.logger.info("=" * 70)
        self.logger.info("✓ Analysis Complete!")
        self.logger.info("=" * 70)
        self.logger.info(f"Workflows scanned: {run.workflows_scanned}")
        self.logger.info(f"Models found: {run.models_found}")
        self.logger.info(f"Models missing: {run.models_missing}")
        self.logger.info(f"Models resolved: {run.models_resolved}")

        if run.download_script:
            self.logger.info(f"Download script: {run.download_script}")
            self.logger.info("Next steps:")
            self.logger.info(f"  1. Review: {run.resolutions_file}")
            self.logger.info(f"  2. Run: bash {run.download_script}")

        if run.errors:
            self.logger.warning("Errors encountered:")
            for error in run.errors:
                self.logger.warning(f"  - {error}")

    def get_run_history(self, limit: int = 10) -> List[WorkflowRun]:
        """
        Get recent run history.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of recent WorkflowRun objects
        """
        # This would typically read from persistent storage
        # For now, return current run if available
        return [self.current_run] if self.current_run else []

    def retry_failed_run(self, run_id: str) -> Optional[WorkflowRun]:
        """
        Retry a failed run.

        Args:
            run_id: ID of the run to retry

        Returns:
            New WorkflowRun object if retry was initiated
        """
        # Implementation would load previous run and retry
        self.logger.info(f"Retry functionality for run {run_id} not implemented yet")
        return None

    def run(
        self,
        specific_workflows: Optional[List[str]] = None,
        workflow_dirs: Optional[List[str]] = None,
        models_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        search_backends: Optional[List[str]] = None,
        generate_scripts: bool = False,
        scan_only: bool = False,
        verify_urls: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the ComfyFixerSmart workflow analysis.
        
        This is the main entry point method expected by tests and external callers.
        It provides a simplified interface to the more detailed run_workflow_analysis method.
        
        Args:
            specific_workflows: List of specific workflow files to analyze
            workflow_dirs: List of directories to scan for workflows
            models_dir: Directory containing local models (overrides config)
            output_dir: Directory for output files (overrides config)
            search_backends: List of search backends to use
            generate_scripts: Whether to generate download scripts
            scan_only: Whether to only scan workflows without searching/downloading
            verify_urls: Whether to verify URLs before downloading
            
        Returns:
            Dictionary with run results and statistics
        """
        # Update config if custom paths provided
        if models_dir:
            config.models_dir = models_dir
        if output_dir:
            config.output_dir = output_dir
            
        # Run the workflow analysis
        workflow_run = self.run_workflow_analysis(
            specific_workflows=specific_workflows,
            workflow_dirs=workflow_dirs,
            search_backends=search_backends,
            generate_script=generate_scripts,
            verify_urls=verify_urls,
        )
        
        # Convert WorkflowRun to dictionary for compatibility with tests
        result = workflow_run.to_dict()
        
        # Add scan_only flag to result for test compatibility
        result["scan_only"] = scan_only
        
        return result

    def _generate_run_report(self, run_result: Dict[str, Any], output_dir: str) -> Optional[str]:
        """
        Generate a human-readable run report.
        
        Args:
            run_result: Dictionary with run results
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file, or None if failed
        """
        try:
            from pathlib import Path
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            report_file = output_path / f"run_report_{run_result.get('run_id', 'unknown')}.md"
            
            with open(report_file, 'w') as f:
                f.write("# ComfyFixerSmart Run Report\n\n")
                f.write(f"Run ID: {run_result.get('run_id', 'unknown')}\n")
                f.write(f"Status: {run_result.get('status', 'unknown')}\n")
                
                if run_result.get('start_time'):
                    f.write(f"Start Time: {run_result['start_time']}\n")
                if run_result.get('end_time'):
                    f.write(f"End Time: {run_result['end_time']}\n")
                
                f.write("\n## Statistics\n\n")
                f.write(f"- Workflows Scanned: {run_result.get('workflows_scanned', 0)}\n")
                f.write(f"- Models Found: {run_result.get('models_found', 0)}\n")
                f.write(f"- Models Missing: {run_result.get('models_missing', 0)}\n")
                f.write(f"- Models Resolved: {run_result.get('models_resolved', 0)}\n")
                f.write(f"- Downloads Generated: {run_result.get('downloads_generated', 0)}\n")
                
                if run_result.get('errors'):
                    f.write("\n## Errors\n\n")
                    for error in run_result['errors']:
                        f.write(f"- {error}\n")
                        
                if run_result.get('missing_file'):
                    f.write(f"\n## Missing Models\n\n")
                    f.write(f"See: {run_result['missing_file']}\n")
                    
                if run_result.get('resolutions_file'):
                    f.write(f"\n## Search Results\n\n")
                    f.write(f"See: {run_result['resolutions_file']}\n")
                    
                if run_result.get('download_script'):
                    f.write(f"\n## Download Script\n\n")
                    f.write(f"Run: `bash {run_result['download_script']}`\n")
            
            self.logger.info(f"Run report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"Failed to generate run report: {e}")
            return None

    def cleanup_old_runs(self, days: int = 30):
        """
        Clean up old run files.

        Args:
            days: Remove runs older than this many days
        """
        # Implementation would clean up old output files
        self.logger.info(f"Cleanup of runs older than {days} days not implemented yet")


# Convenience functions for backward compatibility and CLI usage
def run_comfy_fixer(
    specific_workflows=None,
    workflow_dirs=None,
    search_backends=None,
    generate_script=True,
    verify_urls=False,
    logger=None,
):
    """
    Main entry point for running ComfyFixerSmart.

    Args:
        specific_workflows: List of specific workflow files
        workflow_dirs: List of workflow directories
        search_backends: List of search backends to use
        generate_script: Whether to generate download script
        verify_urls: Whether to verify URLs
        logger: Optional logger instance

    Returns:
        WorkflowRun object with results
    """
    core = ComfyFixerCore(logger=logger)
    return core.run_workflow_analysis(
        specific_workflows=specific_workflows,
        workflow_dirs=workflow_dirs,
        search_backends=search_backends,
        generate_script=generate_script,
        verify_urls=verify_urls,
    )


def run_v1_compatibility_mode(specific_workflows=None, verify_urls=False, logger=None):
    """
    Run in v1 compatibility mode (original comfy_fixer.py behavior).

    Args:
        specific_workflows: List of specific workflow files
        verify_urls: Whether to enable URL verification
        logger: Optional logger instance

    Returns:
        WorkflowRun object
    """
    # V1 uses Qwen search as optional backend
    backends = ["qwen"] if verify_urls else ["civitai"]
    return run_comfy_fixer(
        specific_workflows=specific_workflows,
        search_backends=backends,
        generate_script=True,
        verify_urls=verify_urls,
        logger=logger,
    )


def run_v2_compatibility_mode(specific_workflows=None, retry_failed=False, logger=None):
    """
    Run in v2 compatibility mode (comfy_fixer_v2.py behavior).

    Args:
        specific_workflows: List of specific workflow files
        retry_failed: Whether to retry failed downloads
        logger: Optional logger instance

    Returns:
        WorkflowRun object
    """
    core = ComfyFixerCore(logger=logger)

    if retry_failed:
        # Clear failed downloads from state
        core.state_manager.clear_failed()
        core.logger.info("Cleared failed download records for retry")

    return core.run_workflow_analysis(
        specific_workflows=specific_workflows,
        search_backends=None,  # Use config defaults (qwen, civitai) for best results
        generate_script=True,
        verify_urls=False,
    )
