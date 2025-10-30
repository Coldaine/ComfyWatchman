"""Master status report generation for scheduler cycles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config import config
from ..logging import get_logger
from ..state_manager import JsonStateManager, StateManager
from ..utils import ensure_directory, load_json_file


@dataclass
class StatusArtifacts:
    json_path: Path
    markdown_path: Optional[Path]


class StatusReportGenerator:
    """Generate the master status report consumed by operators and agents."""

    def __init__(self, state_manager: Optional[StateManager] = None, logger=None) -> None:
        self.logger = logger or get_logger("StatusReport")
        self.state_manager = state_manager or JsonStateManager(config.state_dir, logger=self.logger)

    def generate(
        self,
        run: Any,
        intake_summary: Dict[str, List[Dict[str, Any]]],
        cache_paths: Dict[str, Optional[Path]],
    ) -> StatusArtifacts:
        """Generate both JSON and Markdown status artifacts."""

        report_dir = ensure_directory(config.output_dir / 'reports' / 'status')
        json_path = report_dir / 'master_status.json'
        markdown_path = report_dir / 'master_status.md'

        missing_models = load_json_file(run.missing_file) if run.missing_file else []
        resolutions = load_json_file(run.resolutions_file) if run.resolutions_file else []

        workflows = self._build_workflow_status(
            missing_models,
            getattr(run, 'search_results', []),
            resolutions,
        )

        report = {
            'generated_at': datetime.now().isoformat(),
            'run_id': getattr(run, 'run_id', ''),
            'status': getattr(run, 'status', 'unknown'),
            'summary': {
                'workflows_scanned': getattr(run, 'workflows_scanned', 0),
                'models_found': getattr(run, 'models_found', 0),
                'models_missing': getattr(run, 'models_missing', 0),
                'models_resolved': getattr(run, 'models_resolved', 0),
                'uncertain': getattr(run, 'uncertain_models', 0),
            },
            'artifacts': {
                'missing_models_file': run.missing_file,
                'resolutions_file': run.resolutions_file,
                'download_script': run.download_script,
                'model_cache': str(cache_paths.get('model_cache')) if cache_paths.get('model_cache') else None,
                'custom_nodes_cache': str(cache_paths.get('custom_nodes_cache')) if cache_paths.get('custom_nodes_cache') else None,
            },
            'intake': intake_summary,
            'workflows': workflows,
        }

        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        markdown_path.write_text(self._render_markdown(report), encoding='utf-8')

        self.logger.info(f"Master status report updated: {json_path}")
        return StatusArtifacts(json_path=json_path, markdown_path=markdown_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_workflow_status(
        self,
        missing_models: List[Dict[str, Any]],
        search_results: List[Dict[str, Any]],
        cached_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge missing models with resolution status by workflow."""

        result_map = {}
        for record in search_results or cached_results:
            filename = record.get('filename')
            if not filename:
                continue
            result_map[filename] = record

        workflows: Dict[str, Dict[str, Any]] = {}

        for model in missing_models or []:
            workflow_name = model.get('workflow', 'unknown')
            entry = workflows.setdefault(
                workflow_name,
                {
                    'workflow': workflow_name,
                    'missing_models': [],
                    'resolved_models': 0,
                    'uncertain_models': 0,
                },
            )

            filename = model.get('filename')
            status_info = result_map.get(filename, {})
            status = status_info.get('status', 'NOT_FOUND')
            entry['missing_models'].append(
                {
                    'filename': filename,
                    'type': model.get('type'),
                    'status': status,
                    'source': status_info.get('source'),
                }
            )

            if status == 'FOUND':
                entry['resolved_models'] += 1
            elif status == 'UNCERTAIN':
                entry['uncertain_models'] += 1

        for entry in workflows.values():
            total_missing = len(entry['missing_models'])
            if total_missing == 0:
                entry['readiness'] = 'ready'
            elif entry['resolved_models'] == total_missing and entry['uncertain_models'] == 0:
                entry['readiness'] = 'ready'
            elif entry['resolved_models'] == total_missing and entry['uncertain_models'] > 0:
                entry['readiness'] = 'needs_review'
            else:
                entry['readiness'] = 'needs_attention'

        return sorted(workflows.values(), key=lambda item: item['workflow'])

    def _render_markdown(self, report: Dict[str, Any]) -> str:
        lines = ["# ComfyWatchman Master Status", ""]
        lines.append(f"Generated: {report['generated_at']}")
        lines.append(f"Run ID: {report['run_id']}")
        lines.append("")
        summary = report['summary']
        lines.append("## Summary")
        lines.append(f"- Workflows scanned: {summary['workflows_scanned']}")
        lines.append(f"- Models missing: {summary['models_missing']}")
        lines.append(f"- Models resolved: {summary['models_resolved']}")
        lines.append(f"- UNCERTAIN models: {summary['uncertain']}")
        lines.append("")

        if report['workflows']:
            lines.append("## Workflows")
            for wf in report['workflows']:
                lines.append(f"### {wf['workflow']}")
                lines.append(f"- Readiness: {wf['readiness']}")
                lines.append(f"- Missing models: {len(wf['missing_models'])}")
                lines.append(f"- Resolved: {wf['resolved_models']}")
                lines.append(f"- UNCERTAIN: {wf['uncertain_models']}")
                for model in wf['missing_models']:
                    lines.append(
                        f"  - `{model['filename']}` → {model['status']}"
                        + (f" via {model['source']}" if model.get('source') else "")
                    )
                lines.append("")

        if report['intake']:
            lines.append("## Intake")
            for key, value in report['intake'].items():
                lines.append(f"- {key}: {len(value) if isinstance(value, list) else value}")

        return "\n".join(lines) + "\n"
