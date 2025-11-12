"""Background scheduler for ComfyWatchman runs."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional

import psutil

from .config import config
from .core import ComfyFixerCore
from .logging import get_logger


class Scheduler:
    """Run ComfyFixerSmart analysis on an interval with resource guards."""

    def __init__(
        self,
        interval_minutes: int = 120,
        min_vram_gb: float = 8.0,
        enable_vram_guard: bool = True,
        logger=None,
    ) -> None:
        self.interval = timedelta(minutes=interval_minutes)
        self.min_vram_gb = float(min_vram_gb)
        self.enable_vram_guard = enable_vram_guard
        self.logger = logger or get_logger("ComfyFixerScheduler")
        self._stop_event = threading.Event()
        self._is_running = threading.Lock()
        self.core = ComfyFixerCore(logger=self.logger)
        self.last_run: Optional[datetime] = None

    def start(
        self,
        specific_workflows: Optional[List[str]] = None,
        workflow_dirs: Optional[List[str]] = None,
        search_backends: Optional[List[str]] = None,
        generate_script: bool = False,
        verify_urls: bool = False,
    ) -> None:
        """Begin the scheduler loop (blocking)."""
        self.logger.info(
            "Scheduler started (interval=%s minutes, min_vram=%s GB, vram_guard=%s)",
            self.interval.total_seconds() / 60,
            self.min_vram_gb,
            self.enable_vram_guard,
        )

        try:
            while not self._stop_event.is_set():
                if self._should_run():
                    self._run_cycle(
                        specific_workflows=specific_workflows,
                        workflow_dirs=workflow_dirs,
                        search_backends=search_backends,
                        generate_script=generate_script,
                        verify_urls=verify_urls,
                    )
                self._wait_for_next_cycle()
        finally:
            self.logger.info("Scheduler stopped")

    def stop(self) -> None:
        """Signal the scheduler loop to stop."""
        self._stop_event.set()

    def _run_cycle(
        self,
        *,
        specific_workflows: Optional[List[str]],
        workflow_dirs: Optional[List[str]],
        search_backends: Optional[List[str]],
        generate_script: bool,
        verify_urls: bool,
    ) -> None:
        if not self._is_running.acquire(blocking=False):
            self.logger.info("Previous run still in progress; skipping this interval")
            return

        try:
            self.logger.info(f"Starting scheduled run at {datetime.now().isoformat()}")
            result = self.core.run_workflow_analysis(
                specific_workflows=specific_workflows,
                workflow_dirs=workflow_dirs,
                search_backends=search_backends,
                generate_script=generate_script,
                verify_urls=verify_urls,
            )
            self.last_run = datetime.now()
            if result and result.errors:
                for error in result.errors:
                    self.logger.warning("Scheduled run error: %s", error)
        except Exception as exc:  # pragma: no cover - Safety net for background loop
            self.logger.error("Scheduled run failed: %s", exc)
        finally:
            self._is_running.release()

    def _wait_for_next_cycle(self) -> None:
        next_run = datetime.now() + self.interval
        self.logger.info(f"Next run scheduled for {next_run.isoformat()}")
        self._stop_event.wait(self.interval.total_seconds())

    def _should_run(self) -> bool:
        if self.enable_vram_guard:
            available = self._detect_vram_gb()
            if available is not None and available < self.min_vram_gb:
                self.logger.info(
                    "Skipping run: available VRAM %.2f GB < required %.2f GB",
                    available,
                    self.min_vram_gb,
                )
                return False
        if not self._is_comfyui_running():
            self.logger.info("Skipping run: ComfyUI process not found.")
            return False
        return True

    def _is_comfyui_running(self) -> bool:
        """Check if a ComfyUI-like process is running."""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                # Heuristic check for ComfyUI. This might need adjustment.
                if 'python' in proc.info['name'] and any('main.py' in part for part in proc.info['cmdline']):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def _detect_vram_gb(self) -> Optional[float]:
        """Return available GPU memory (GB) using nvidia-smi; None if unknown."""
        binary = os.environ.get("CUDA_SMI_BINARY", "nvidia-smi")
        try:
            result = subprocess.run(  # nosec B603, B607
                [binary, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
        except FileNotFoundError:
            self.logger.debug("nvidia-smi not available; VRAM guard disabled")
            return None
        except subprocess.SubprocessError as exc:
            self.logger.debug("Unable to query VRAM: %s", exc)
            return None

        values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not values:
            return None

        try:
            # memory.total returns MB; convert to GB
            gb_values = [float(value) / 1024 for value in values]
            return max(gb_values)
        except ValueError:
            return None
