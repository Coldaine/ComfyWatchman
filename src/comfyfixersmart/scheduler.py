"""Guardrailed scheduler for automated readiness cycles."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .cache_manager import CacheManager
from .config import config
from .core import ComfyFixerCore, WorkflowRun
from .logging import get_logger
from .reporting.status_report import StatusReportGenerator, StatusArtifacts
from .state_manager import JsonStateManager, StateManager
from .utils import get_available_vram_gb, is_machine_recently_awake, load_json_file


class Scheduler:
    """Run readiness cycles on an interval with safety guardrails."""

    def __init__(self, state_manager: Optional[StateManager] = None, logger=None) -> None:
        self.logger = logger or get_logger("Scheduler")
        self.state_manager = state_manager or JsonStateManager(config.state_dir, logger=self.logger)
        self.cache_manager = CacheManager(state_manager=self.state_manager, logger=self.logger)
        self.status_generator = StatusReportGenerator(state_manager=self.state_manager, logger=self.logger)
        self.core = ComfyFixerCore(logger=self.logger, state_manager=self.state_manager)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_cycle(self, force: bool = False) -> Optional[Any]:
        """Execute a single guarded cycle."""

        if not force and not config.schedule.enabled:
            self.logger.info("Scheduler disabled via configuration; skipping cycle")
            self._record_skip("disabled")
            return None

        if not config.models_dir or not config.models_dir.exists():
            raise ValueError("Models directory is not configured; aborting cycle")

        if not force and not is_machine_recently_awake():
            self.logger.info("Machine recently resumed; deferring cycle")
            self._record_skip("recent_resume")
            return None

        if not force:
            vram_gb = get_available_vram_gb()
            if vram_gb is not None and vram_gb < config.schedule.min_vram_gb:
                self.logger.info(
                    "Insufficient VRAM detected (%.2f GB < %.2f GB); skipping cycle",
                    vram_gb,
                    config.schedule.min_vram_gb,
                )
                self._record_skip("insufficient_vram", {'available_vram_gb': vram_gb})
                return None

        self.logger.info("Starting automated readiness cycle")
        start_time = datetime.now()

        workflow_paths = self.core.scanner.scan_workflows()
        intake_summary = self.state_manager.process_workflow_intake(workflow_paths)

        cache_paths = self.cache_manager.refresh_all()

        run = self.core.run_workflow_analysis(
            specific_workflows=None,
            workflow_dirs=None,
            search_backends=config.search.backend_order,
            generate_script=True,
            verify_urls=False,
        )

        artifacts = self.status_generator.generate(run, intake_summary, cache_paths)

        cycle_result = {
            'run_id': run.run_id,
            'status': run.status,
            'started_at': start_time.isoformat(),
            'finished_at': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - start_time).total_seconds(),
            'workflows_scanned': run.workflows_scanned,
            'models_missing': run.models_missing,
            'models_resolved': run.models_resolved,
            'uncertain_models': getattr(run, 'uncertain_models', 0),
            'artifacts': {
                'status_json': str(artifacts.json_path),
                'status_markdown': str(artifacts.markdown_path) if artifacts.markdown_path else None,
                'download_script': run.download_script,
            },
        }

        self.state_manager.record_cycle_result(cycle_result)
        self._append_structured_log(cycle_result)

        self.logger.info("Cycle complete: run_id=%s status=%s", run.run_id, run.status)
        return run

    def run_forever(self, interval_minutes: Optional[int] = None) -> None:
        """Run cycles indefinitely respecting the configured interval."""

        interval = interval_minutes or config.schedule.interval_minutes
        self.logger.info("Scheduler loop started (interval=%s minutes)", interval)

        try:
            while True:
                try:
                    self.run_cycle()
                except Exception as exc:  # pragma: no cover
                    self.logger.error(f"Scheduler cycle failed: {exc}")
                    self._record_skip('error', {'error': str(exc)})
                time.sleep(max(60, interval * 60))
        except KeyboardInterrupt:  # pragma: no cover
            self.logger.info("Scheduler loop interrupted by user")

    def list_recent_intake(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.state_manager.list_intake_events(limit)

    def regenerate_status_report(self) -> Optional[StatusArtifacts]:
        """Regenerate the master status report using the most recent cycle."""

        last_cycle = self.state_manager.state.metadata.get('last_cycle', {})
        run_id = last_cycle.get('run_id')
        if not run_id or run_id == 'skipped':
            self.logger.warning("No completed cycle available for status regeneration")
            return None

        run = WorkflowRun(run_id=run_id, start_time=datetime.now())
        run.status = last_cycle.get('status', 'unknown')
        run.workflows_scanned = last_cycle.get('workflows_scanned', 0)
        run.models_missing = last_cycle.get('models_missing', 0)
        run.models_resolved = last_cycle.get('models_resolved', 0)
        run.uncertain_models = last_cycle.get('uncertain_models', 0)
        artifacts = last_cycle.get('artifacts', {}) or {}
        run.download_script = artifacts.get('download_script')
        run.missing_file = self._resolve_output_file(f"missing_models_{run_id}.json")
        run.resolutions_file = self._resolve_output_file(f"resolutions_{run_id}.json")
        run.search_results = load_json_file(run.resolutions_file, default=[]) if run.resolutions_file else []

        cache_paths = {
            'model_cache': self._state_file('model_cache.json'),
            'custom_nodes_cache': self._state_file('custom_nodes_cache.json'),
        }

        return self.status_generator.generate(run, {'new': [], 'updated': [], 'removed': []}, cache_paths)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _append_structured_log(self, payload: Dict[str, Any]) -> None:
        log_path = Path(config.log_dir) / 'structured.log'
        with log_path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + '\n')

    def _record_skip(self, reason: str, extra: Optional[Dict[str, Any]] = None) -> None:
        payload = {
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
        }
        if extra:
            payload.update(extra)
        self.state_manager.record_cycle_result({
            'run_id': 'skipped',
            'status': reason,
            'started_at': datetime.now().isoformat(),
            'finished_at': datetime.now().isoformat(),
            'duration_seconds': 0.0,
            'workflows_scanned': 0,
            'models_missing': 0,
            'models_resolved': 0,
            'uncertain_models': 0,
            'artifacts': {},
            'skip': payload,
        })
        self._append_structured_log({'skip': payload})

    def _state_file(self, name: str) -> Optional[Path]:
        path = config.state_dir / name
        return path if path.exists() else None

    def _resolve_output_file(self, name: str) -> Optional[str]:
        path = config.output_dir / name
        return str(path) if path.exists() else None
