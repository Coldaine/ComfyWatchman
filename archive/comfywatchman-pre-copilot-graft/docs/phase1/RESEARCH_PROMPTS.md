# Phase 1 Research Prompts

## R1.1: VRAM Detection on Linux
**Query:** "How to detect available GPU VRAM on Linux using Python? Need to check if at least 2GB is free before running ComfyUI workflow analysis. Prefer solutions that work with NVIDIA GPUs using nvidia-smi or pynvml."

**Expected Outputs:**
- Code snippets for VRAM detection
- Threshold recommendations
- Error handling strategies

---

## R1.2: Process Detection for ComfyUI
**Query:** "Best method to detect if ComfyUI is running on localhost? Should I check for process name, or check if port 8188 is listening? Need reliable detection for scheduling workflow analysis only when ComfyUI is active."

**Expected Outputs:**
- Comparison of process check vs. port check
- Python code examples (psutil or socket)
- Reliability considerations

---

## R1.3: LangGraph Persistence for Scheduled Jobs
**Query:** "LangGraph best practices for persisting state between scheduled runs every 2 hours. Need to save workflow health check results and resume if interrupted. Should I use SQLite checkpointing or JSON file persistence for privacy-first local storage?"

**Expected Outputs:**
- LangGraph persistence backends comparison
- Code examples for JSON-based persistence
- Performance considerations for 50+ workflows

---

## R1.4: ComfyUI Workflow JSON Structure
**Query:** "ComfyUI workflow JSON schema and structure. Need to understand how to parse workflow files to extract model references, custom node dependencies, and parameter settings. Looking for official documentation or robust parsing examples."

**Expected Outputs:**
- Workflow JSON schema overview
- Common node types and their parameters
- Model reference patterns (checkpoints, LoRAs, embeddings)

---

## R1.5: Static Dashboard Generation
**Query:** "Generate a static HTML dashboard from JSON data without hosting a web server. Need a single-file HTML with embedded CSS/JS that reads workflow status JSON and displays it as an interactive dashboard. No build tools or npm dependencies."

**Expected Outputs:**
- Template HTML with embedded JavaScript
- JSON data binding examples
- Responsive design patterns for status displays

---

## R1.6: Systemd User Timer Setup
**Query:** "How to set up systemd user timer (not system-level) to run a Python script every 2 hours. Timer should start on boot, persist across user sessions, and log output. Include instructions for enabling/disabling timer."

**Expected Outputs:**
- Complete .timer and .service file examples
- Installation commands
- Logging configuration

---

## R1.7: LangGraph Conditional Execution
**Query:** "LangGraph conditional edges pattern for skipping workflow execution based on runtime checks. Need to check system state (VRAM, process running) and either proceed with analysis or skip and schedule next run."

**Expected Outputs:**
- Conditional edge syntax examples
- State-based routing patterns
- Best practices for early termination
