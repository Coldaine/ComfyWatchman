"""
Copilot Validator Adapter for ComfyFixerSmart

Integrates the powerful workflow validation and repair capabilities from the
forked ComfyUI-Copilot backend.
"""

import json
from typing import Dict, Any, Optional

from ..logging import get_logger
from . import COPILOT_AVAILABLE

# Conditionally import from the forked submodule
if COPILOT_AVAILABLE:
    try:
        from backend.service.debug_agent import debug_workflow_errors
        from backend.utils.request_context import set_session_id, set_config
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

    async def validate(self, workflow_path: str, session_id: str = "comfyfixer-session") -> Optional[Dict[str, Any]]:
        """
        Validates a workflow file using the Copilot debug agent.

        This simulates the environment needed for the agent to run headlessly.

        Args:
            workflow_path: The absolute path to the workflow.json file.
            session_id: A unique ID for the validation session.

        Returns:
            A dictionary containing the final validation report, or None on failure.
        """
        if not self.is_available():
            self.logger.error("Validation called but Copilot backend is not available.")
            return None

        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to read or parse workflow file {workflow_path}: {e}")
            return None

        self.logger.info(f"Starting Copilot validation for: {workflow_path}")

        # --- Context Simulation ---
        # The Copilot backend uses a request context to get session_id and config.
        # We must simulate this context for the agent to work headlessly.
        set_session_id(session_id)
        # We can pass a mock config. For now, an empty one is sufficient.
        # This might need to be expanded if the agents require specific config values.
        set_config({})
        # --- End Context Simulation ---

        final_report = None
        try:
            # The debug_workflow_errors is an async generator. We need to iterate
            # through it to get the final result.
            async for text_update, ext_data in debug_workflow_errors(workflow_data):
                if ext_data and ext_data.get("finished"):
                    self.logger.info("Copilot validation stream finished.")
                    final_report = {
                        "full_text_log": text_update,
                        "structured_summary": ext_data.get("data")
                    }
                    break
            
            if final_report:
                self.logger.info(f"Successfully received validation report for {workflow_path}.")
            else:
                self.logger.warning(f"Copilot validation for {workflow_path} finished without a final report.")

            return final_report

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during Copilot validation for {workflow_path}: {e}")
            # In a real scenario, you might want to see the traceback
            # import traceback
            # self.logger.error(traceback.format_exc())
            return None
