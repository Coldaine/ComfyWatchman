# ComfyWatchman civitai_tools Integration Plan

## Problem Statement

PR #5 added sophisticated Python-based download tools (`CivitaiDirectDownloader`, `CivitaiBatchDownloader`, `DirectIDBackend`) but failed to integrate them into the main workflow. The current production code still generates wget bash scripts, leading to:

- No hash verification
- Numbered duplicate files when scripts rerun
- Files downloaded to wrong directories
- No Python-based control over downloads

## Architecture Goals

1. **AUTOMATIC DOWNLOADS** - Models download automatically, zero manual intervention required
2. **Use Python downloaders** - Replace wget scripts with CivitaiDirectDownloader/BatchDownloader
3. **Integrate DirectIDBackend** - Use known model lookups before API searches
4. **Add HuggingFace support** - Implement real HuggingFace search/download
5. **Real-time progress** - Show download progress, success/failure immediately
6. **Hash verification** - Automatic SHA256 verification, delete corrupted files
7. **Deprecate script generation** - Remove wget script generation from main workflow

## Integration Plan

### Phase 1: Search Layer Integration

**File: `src/comfywatchman/search.py`**

**Changes to `CivitaiSearch.search()` method:**

1. Add DirectIDBackend as first-pass lookup before API search
2. If DirectID finds model → return immediately with high confidence
3. If not found → fall back to existing API search logic
4. Ensure proper error handling and logging

**Implementation:**
```python
def search(self, model_info: Dict[str, Any]) -> SearchResult:
    filename = model_info["filename"]

    # NEW: Try DirectIDBackend first
    try:
        from .civitai_tools.direct_id_backend import DirectIDBackend
        direct_backend = DirectIDBackend()

        # Extract name for lookup (remove file extension)
        name = filename.rsplit('.', 1)[0]
        result = direct_backend.lookup_by_name(name)

        if result and result.get('found'):
            # Convert to SearchResult
            return self._create_search_result_from_direct_lookup(result, filename, model_info)
    except Exception as e:
        self.logger.warning(f"DirectID lookup failed: {e}, falling back to API search")

    # EXISTING: Fall back to API search
    return self._search_via_api(model_info)
```

### Phase 2: Download Layer Integration

**File: `src/comfywatchman/download.py`**

**Replace `DownloadManager` with automatic Python downloads:**

```python
def download_models_automatically(
    self,
    search_results: List[SearchResult],
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    AUTOMATICALLY download models using Python (CivitaiBatchDownloader).

    This replaces the old script generation workflow. Downloads happen
    immediately, with real-time progress, hash verification, and state updates.

    Args:
        search_results: Search results with download info
        run_id: Run identifier for logging

    Returns:
        Summary dict with success/failure counts and file paths
    """
    from .civitai_tools.batch_downloader import (
        CivitaiBatchDownloader,
        BatchJob,
        BatchStatus
    )

    self.logger.info("=== Starting Automatic Downloads ===")

    # Convert search results to BatchJob objects
    jobs = []
    for result in search_results:
        if result.status == "FOUND" and result.civitai_id:
            # Determine target directory based on model type
            if result.type:
                target_dir = Path(config.models_dir) / result.type
            else:
                target_dir = Path(config.models_dir) / "checkpoints"

            job = BatchJob(
                model_id=result.civitai_id,
                model_name=result.filename,
                version_id=result.version_id
            )
            jobs.append(job)

    if not jobs:
        self.logger.warning("No models to download")
        return {"successful": 0, "failed": 0, "skipped": 0}

    # Execute batch download with progress
    downloader = CivitaiBatchDownloader(
        download_dir=str(config.models_dir),
        max_retries=3,
        delay_between_downloads=1.0
    )

    self.logger.info(f"Downloading {len(jobs)} models...")
    summary = downloader.download_batch(jobs, continue_on_failure=True)

    # Update state manager for each download
    if self.state_manager:
        for job in summary.jobs:
            if job.result:
                status = "success" if job.status == BatchStatus.COMPLETED else "failed"
                self.state_manager.update_download_status(
                    job.model_name,
                    status,
                    file_path=job.result.file_path if job.result.file_path else None
                )

    # Log summary
    self.logger.info("=== Download Summary ===")
    self.logger.info(f"✓ Successful: {summary.successful}")
    self.logger.info(f"✗ Failed: {summary.failed}")
    self.logger.info(f"⏭ Skipped: {summary.skipped}")

    return summary.to_dict()
```

**Deprecate old script generation (keep for debugging only):**
```python
def generate_download_script(
    self,
    search_results: List[SearchResult],
    run_id: Optional[str] = None
) -> str:
    """
    DEPRECATED: Generate bash script for manual downloads.

    This method is kept for debugging/export purposes only.
    Normal workflow uses download_models_automatically() instead.
    """
    self.logger.warning("Script generation is deprecated, use automatic downloads instead")
    # ... keep existing implementation for backward compat ...
```

### Phase 3: Core Workflow Updates

**File: `src/comfywatchman/core.py`**

**Replace `_generate_download_script()` with automatic downloads:**
```python
def _download_models(self, search_results: List[SearchResult]) -> Optional[Dict[str, Any]]:
    """
    AUTOMATICALLY download and organize models.

    Models are downloaded to the correct ComfyUI subdirectories based on type:
    - checkpoints/ for checkpoint models
    - loras/ for LoRA models
    - vae/ for VAE models
    - etc.
    """
    self.logger.info("=== Downloading Models ===")

    if not search_results:
        self.logger.info("No models to download")
        return None

    # Execute automatic downloads
    download_summary = self.download_manager.download_models_automatically(
        search_results,
        run_id=self.current_run.run_id
    )

    # Update run statistics
    self.current_run.downloads_generated = download_summary.get("successful", 0)

    # Log results
    self.logger.info(f"✓ Successfully downloaded: {download_summary.get('successful', 0)} models")
    if download_summary.get("failed", 0) > 0:
        self.logger.warning(f"✗ Failed downloads: {download_summary.get('failed', 0)} models")

    return download_summary


# In run_workflow_analysis(), replace the script generation step:
def run_workflow_analysis(...):
    # ... existing steps ...

    # Step 4: Search for missing models
    search_results = self._search_missing_models(missing_models, backends)

    # Step 5: AUTOMATICALLY DOWNLOAD (no more scripts!)
    download_summary = self._download_models(search_results)

    # Complete run
    self._complete_run("completed")
```

### Phase 4: Configuration Updates

**File: `src/comfywatchman/config.py`**

**Add simple download configuration:**
```python
@dataclass
class DownloadConfig:
    """Automatic download configuration."""
    auto_download: bool = True  # Set to False to disable automatic downloads
    verify_hashes: bool = True   # SHA256 verification
    max_retries: int = 3
    timeout_seconds: int = 300
    delay_between_downloads: float = 1.0  # Seconds between downloads (rate limiting)

class Config:
    # ... existing config ...

    def __init__(self):
        # ... existing init ...
        self.download = DownloadConfig()
```

**Note:** Models are ALWAYS organized into appropriate folders automatically:
- Search results include `type` field (checkpoints, loras, vae, etc.)
- BatchDownloader passes this to CivitaiDirectDownloader
- Files download directly to `ComfyUI/models/{type}/filename.safetensors`
- No manual file moving required

### Phase 5: HuggingFace Implementation

**New File: `src/comfywatchman/civitai_tools/hf_downloader.py`**

```python
"""
HuggingFace model downloader.
Provides search and download capabilities for HuggingFace Hub models.
"""

from huggingface_hub import hf_hub_download, HfApi
from pathlib import Path
from typing import Optional, Dict, Any
import re

class HFDownloader:
    """HuggingFace Hub model downloader."""

    def __init__(self, download_dir: Optional[str] = None, token: Optional[str] = None):
        self.download_dir = Path(download_dir or "./downloads")
        self.token = token or os.environ.get("HF_TOKEN")
        self.api = HfApi(token=self.token)

    def search_model(self, query: str, model_type: str = "diffusion") -> Optional[Dict[str, Any]]:
        """Search for a model on HuggingFace Hub."""
        # Implementation using HfApi.list_models()
        pass

    def download_model(self, repo_id: str, filename: str) -> str:
        """Download a model file from HuggingFace Hub."""
        filepath = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=str(self.download_dir),
            token=self.token
        )
        return filepath
```

**Update `src/comfywatchman/search.py`:**
```python
class HuggingFaceSearch(SearchBackend):
    """HuggingFace Hub search backend."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("HuggingFaceSearch")
        try:
            from .civitai_tools.hf_downloader import HFDownloader
            self.downloader = HFDownloader()
            self.available = True
        except ImportError:
            self.logger.warning("huggingface_hub not available")
            self.available = False

    def search(self, model_info: Dict[str, Any]) -> SearchResult:
        if not self.available:
            return SearchResult(
                status="NOT_FOUND",
                filename=model_info["filename"],
                metadata={"reason": "huggingface_hub not installed"}
            )

        # Real implementation using HFDownloader.search_model()
        # ...
```

**Add to `pyproject.toml`:**
```toml
[project.optional-dependencies]
huggingface = [
    "huggingface-hub>=0.20.0",
]
```

## Implementation Order

1. **Phase 1: Search Integration** (1-2 hours)
   - Update CivitaiSearch.search()
   - Test DirectIDBackend integration

2. **Phase 2: Download Integration** (2-3 hours)
   - Add download modes to config
   - Implement download_models_direct()
   - Update DownloadManager.process_downloads()

3. **Phase 3: Core Updates** (1 hour)
   - Update core.py orchestration
   - Update CLI to support new modes

4. **Phase 4: HuggingFace** (2-3 hours)
   - Create HFDownloader
   - Implement HuggingFaceSearch
   - Add dependency

5. **Phase 5: Testing & Validation** (2-3 hours)
   - Update unit tests
   - Run integration tests
   - Test end-to-end workflow

## Testing Strategy

1. Unit tests for each new component
2. Integration test for full workflow with Python downloads
3. Integration test for backward compatibility (script mode)
4. Manual test with real Civitai models
5. Manual test with real HuggingFace models

## Rollback Plan

If issues arise:
- Set `config.download.auto_download = False` to disable automatic downloads
- Old wget script generation code remains available for manual export
- Workflow will complete search but skip downloads if disabled

## Success Criteria

- [ ] DirectIDBackend integrated into search flow (known models found instantly)
- [ ] Python downloads execute automatically, zero manual intervention
- [ ] Hash verification happens on every download
- [ ] Models automatically organized into correct folders (checkpoints/, loras/, vae/)
- [ ] No more duplicate numbered files (.1, .2, .3)
- [ ] Real-time progress indicators during downloads
- [ ] HuggingFace models can be searched and downloaded
- [ ] All existing tests updated and passing
- [ ] End-to-end test: `comfywatchman` → models automatically download to correct folders
