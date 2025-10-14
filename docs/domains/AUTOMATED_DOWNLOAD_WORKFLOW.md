# Domain Framework: Automated Download & Verification Workflow

**Owner:** Tooling Team
**Status:** Proposed

---

## 1. Overview

This document provides the exhaustive framework for the "Download & Verification Service," a persistent, asynchronous system designed to fully automate the lifecycle of resolving, downloading, and verifying missing ComfyUI models.

This system addresses the core pain points of long-running, failure-prone downloads and eliminates the need for manual script execution and supervision. It evolves the `ComfyFixerSmart` tool from a diagnostic helper into a true, "fire-and-forget" download management system.

The architecture is composed of three primary components: a **Job Dispatcher** (the existing `ComfyWatchman` tool), a **Persistent Job Queue**, and a **Background Worker Service**.

## 2. Architectural Components

### 2.1. The Job Dispatcher (`comfy_doctor`)

The role of the existing `comfy_doctor` tool will shift from a script generator to a job dispatcher.

*   **Function:** Its responsibility ends after the `QwenSearch` agent successfully identifies the download links for missing models.
*   **Action:** Instead of generating a `.sh` script, it will connect to the persistent job queue and enqueue a new job for each found model.
*   **User Feedback:** The tool will provide immediate feedback to the user that the jobs have been successfully dispatched to the background worker.

### 2.2. The Persistent Job Queue

This is the backbone of the asynchronous system, providing a durable, thread-safe to-do list.

*   **Technology:** The `persist-queue` Python library will be adopted. It is lightweight, file-based, and requires no external dependencies (like Redis).
*   **Location:** The queue database will be stored within the `ComfyFixerSmart` project, likely in the `state/` directory.
*   **Job Schema:** Each job added to the queue will be a JSON object with the following structure:
    ```json
    {
      "job_id": "uuid-here",
      "status": "PENDING",
      "added_at": "iso-timestamp",
      "attempts": 0,
      "model_info": {
        "expected_filename": "epic_lora_v2.safetensors",
        "model_type": "loras",
        "download_url": "http://example.com/model.safetensors",
        "source": "civitai_hash"
      },
      "history": [
        {"timestamp": "...", "event": "Job created"}
      ]
    }
    ```
    *   `status` can be: `PENDING`, `DOWNLOADING`, `VERIFYING`, `SUCCESS`, `FAILED`.
    *   `source` is critical for the verification rubric.

### 2.3. The Background Worker Service (`download_worker.py`)

This is a new, standalone, long-running Python script that acts as the core of the service.

*   **Execution:** It is designed to be run continuously in a background session (e.g., `tmux`, `screen`, or as a `systemd` service).
*   **Logic Loop:** The worker will continuously perform the following actions:
    1.  Poll the job queue for the next `PENDING` job.
    2.  If a job is found, atomically get it and update its status to `DOWNLOADING`.
    3.  Execute the download.
    4.  Upon completion, update the job status to `VERIFYING` and trigger the Agentic Verification step.
    5.  Based on the agent's verdict, take the final action (move or delete the file) and update the job's final status to `SUCCESS` or `FAILED`.
    6.  If no jobs are found, wait for a configured interval (e.g., 30 seconds) before polling again.

## 3. The Download & Verification Lifecycle (Detailed Steps)

### Step 1: Job Enqueueing

The `comfy_doctor` tool adds a job to the `persist-queue`.

### Step 2: Asynchronous Download

The `download_worker.py` picks up the job.
*   **Staging Directory:** The download will be performed into a temporary, isolated staging directory (e.g., `ComfyFixerSmart/staging/<job_id>/`). This prevents incomplete files from ever entering the main model library.
*   **Resilience:** The download will be executed using a robust method (e.g., `wget -c`) that automatically handles retries and resumes interrupted downloads.

### Step 3: Agentic Verification

This is the most critical and intelligent part of the service.
*   **Trigger:** Once the download is complete, the worker invokes the Qwen agent.
*   **Prompt:** It uses a specialized, detailed prompt (`verify_download_prompt.txt`) that provides the agent with the file's context and a strict verification rubric.
*   **Rubric Summary:**
    *   **Auto-Pass:** If the download `source` was `civitai_hash`, the file is considered trusted and passes automatically.
    *   **Strict Rejections:** The agent will reject the file for mismatches in file type (e.g., expected `.safetensors`, got `.zip`), unexpected executables in archives, or multiple ambiguous model files within a single archive.
*   **Output:** The agent's sole output is a structured JSON object containing the verdict (`VERIFIED` or `REJECTED`) and a human-readable `reason`.

### Step 4: Final Action & Logging

The worker takes action based on the agent's verdict.
*   **On `VERIFIED`:**
    1.  The downloaded file is moved from the staging directory to its correct final destination (e.g., `ComfyUI-stable/models/loras/`).
    2.  The job status is updated to `SUCCESS`.
*   **On `REJECTED`:**
    1.  The staging directory and its contents are deleted.
    2.  The job status is updated to `FAILED`.
    3.  The agent's `reason` is written to a dedicated log file (`verification_failures.log`).
*   **State Management:** All status changes and the final outcome are recorded in the central state manager, making them available to the UI.

## 4. Tooling and Maintenance

*   **Logging:** The `download_worker.py` will maintain its own log file, recording all major events (job start, download progress, verification results, errors).
*   **Dashboard Integration:** The diagnostic UI will be updated to read the job queue and state manager, providing a real-time view of pending, in-progress, and completed/failed downloads.
*   **Manual Retry:** The UI will provide a "Retry" button for failed jobs, which will simply change their status back to `PENDING` for the worker to pick up again.
