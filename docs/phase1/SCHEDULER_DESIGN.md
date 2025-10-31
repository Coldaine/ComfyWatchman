# Scheduler Design

## Overview
This document details the design for the ComfyWatchman scheduler, which is responsible for triggering the workflow health check every two hours.

## Recommended Implementation: Systemd User Timer

The primary recommendation is to use a **systemd user timer**. This approach is robust, reliable, and well-integrated into modern Linux systems.

### Timer Configuration (`~/.config/systemd/user/comfywatchman.timer`)
```ini
[Unit]
Description=ComfyWatchman Workflow Health Check

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Persistent=true

[Install]
WantedBy=timers.target
```
*   `OnBootSec=5min`: Runs 5 minutes after the user logs in.
*   `OnUnitActiveSec=2h`: Runs every 2 hours after the service was last activated.
*   `Persistent=true`: If the machine was asleep when a run was scheduled, the timer will trigger as soon as it wakes up.

### Service Configuration (`~/.config/systemd/user/comfywatchman.service`)
```ini
[Unit]
Description=ComfyWatchman Workflow Health Check Service

[Service]
Type=oneshot
ExecStart=/path/to/your/python/venv/bin/python -m comfywatchman.cli --run-check
WorkingDirectory=/path/to/comfywatchman/repo
```
*   `Type=oneshot`: The service is expected to start, run to completion, and then stop.
*   `ExecStart`: The command to execute. This should point to the Python executable within the project's virtual environment and invoke the main CLI function for the health check.
*   `WorkingDirectory`: Sets the working directory to the repository root.

### Management Commands
*   `systemctl --user enable --now comfywatchman.timer`: Enables and starts the timer.
*   `systemctl --user start comfywatchman.service`: Manually triggers a run.
*   `journalctl --user -u comfywatchman.service`: Views the logs for the service.

## Alternative Implementation: APScheduler

If a systemd-independent solution is required, **APScheduler** is a viable alternative.

### Implementation
```python
# In the main CLI application
from apscheduler.schedulers.background import BackgroundScheduler
import time

def run_health_check_job():
    # This function invokes the LangGraph workflow
    print("Running scheduled health check...")
    # graph.invoke(...)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_health_check_job, 'interval', hours=2)
    scheduler.start()
    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
```

### Pros and Cons
*   **Pros:**
    *   Platform-independent (works on Windows, macOS, etc.).
    *   Contained within the Python application.
*   **Cons:**
    *   Requires the application to be running as a long-running process.
    *   Less resilient to system reboots compared to systemd.

## Failure Recovery Strategy

*   **Systemd:** Systemd provides built-in retry mechanisms if needed, but for a 2-hour cycle, the `Persistent=true` setting is generally sufficient to handle transient system states (like being asleep). The LangGraph workflow itself is responsible for checking system health (VRAM, ComfyUI running) and gracefully skipping a cycle if the prerequisites are not met.
*   **APScheduler:** The `run_health_check_job` function should include a `try...except` block to catch any exceptions during the graph execution and log them appropriately. The scheduler will continue to trigger the job at the next interval regardless of the previous run's success or failure.

## Logging and Monitoring

*   **Systemd:** All output (stdout and stderr) from the `ExecStart` command is captured by the systemd journal. This provides a robust, centralized logging solution.
*   **APScheduler:** Logging should be configured within the Python application using the standard `logging` module to write to a file (e.g., `comfywatchman.log`).
