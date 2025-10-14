"""
Copilot Validator Adapter for ComfyFixerSmart

Integrates the powerful workflow validation and repair capabilities from the
forked ComfyUI-Copilot backend.
"""

import json
from typing import Dict, Any, Optional, Tuple

from ..logging import get_logger
from ..config import config
from . import COPILOT_AVAILABLE

# Conditionally import from the forked submodule
if COPILOT_AVAILABLE:
    try:
        from ...backend.service.debug_agent import debug_workflow_errors
        from ...backend.utils.request_context import set_session_id, set_config
    except (ImportError, ModuleNotFoundError) as e:
        debug_workflow_errors = None
        set_session_id, set_config = None, None
        _import_error = e
else:
    debug_workflow_errors = None
    set_session_id, set_config = None, None
    _import_error = "ComfyUI-Copilot backend not found or 'agents' package not installed."


class CopilotValidator:
    """
    An adapter to run the ComfyUI-Copilot validation engine on a workflow file.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger("CopilotValidator")
        if not COPILOT_AVAILABLE or not debug_workflow_errors:
            self.enabled = False
            self.logger.warning(f"Copilot validation is disabled. Reason: {_import_error}")
        else:
            self.enabled = True
            self.logger.info("CopilotValidator initialized successfully.")

    def is_available(self) -> bool:
        """Check if the validator is properly initialized and ready."""
        return self.enabled

    async def validate_and_repair(self, workflow_path: str, session_id: str = "comfyfixer-repair-session") -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Validates and optionally repairs a workflow file.

        If auto-repair is enabled, this method will overwrite the original
        workflow file with the repaired version.

        Args:
            workflow_path: The absolute path to the workflow.json file.
            session_id: A unique ID for the session.

        Returns:
            A tuple containing:
            - The final validation report.
            - The repaired workflow data if changes were made, otherwise None.
        """
        report = await self.validate(workflow_path, session_id)

        if not report or not config.copilot.auto_repair:
            return report, None

        # Check the report for evidence of a successful repair
        repaired_workflow = None
        summary = report.get("structured_summary", [])
        if not isinstance(summary, list):
            return report, None

        for item in summary:
            if isinstance(item, dict) and item.get("type") in ("param_update", "workflow_update"):
                workflow_data = item.get("data", {}).get("workflow_data")
                if workflow_data:
                    self.logger.info(f"Found repaired workflow data in validation report for {workflow_path}.")
                    repaired_workflow = workflow_data
                    break
        
        if repaired_workflow:
            try:
                # Overwrite the original file with the repaired workflow
                with open(workflow_path, 'w', encoding='utf-8') as f:
                    json.dump(repaired_workflow, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Successfully saved repaired workflow to {workflow_path}")
                return report, repaired_workflow
            except IOError as e:
                self.logger.error(f"Failed to save repaired workflow to {workflow_path}: {e}")

        return report, None
