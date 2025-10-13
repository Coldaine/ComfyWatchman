from dataclasses import dataclass, field
from pathlib import Path
import os
import tomllib
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

@dataclass
class Config:
    """Configuration class for ComfyFixerSmart with defaults, TOML loading, and env overrides."""

    # Paths
    comfyui_root: Optional[Path] = None
    workflow_dirs: List[Path] = field(default_factory=list)
    output_dir: Path = Path("output")
    log_dir: Path = Path("log")
    state_dir: Path = Path("state")
    search_log_file: str = "qwen_search_history.log"
    download_counter_file: str = "download_counter.txt"
    temp_dir: Path = Path("/tmp") / "qwen_search_results"

    # API
    civitai_api_base: str = "https://civitai.com/api/v1"
    civitai_download_base: str = "https://civitai.com/api/download/models"
    civitai_api_timeout: int = 30

    # Model settings
    model_extensions: List[str] = field(default_factory=lambda: [
        ".safetensors", ".ckpt", ".pt", ".bin", ".pth"
    ])
    model_type_mapping: Dict[str, str] = field(default_factory=lambda: {
        'CheckpointLoaderSimple': 'checkpoints',
        'CheckpointLoader': 'checkpoints',
        'LoraLoader': 'loras',
        'LoraLoaderModelOnly': 'loras',
        'VAELoader': 'vae',
        'CLIPLoader': 'clip',
        'DualCLIPLoader': 'clip',
        'ControlNetLoader': 'controlnet',
        'UpscaleModelLoader': 'upscale_models',
        'CLIPVisionLoader': 'clip_vision',
        'UNETLoader': 'unet',
        'SAMLoader': 'sams',
        'GroundingDinoModelLoader': 'grounding-dino',
    })

    # State management
    state_file: str = "download_state.json"

    # Logging
    log_format: str = "%Y-%m-%d %H:%M:%S"

    # Run settings
    run_id_format: str = "%Y%m%d_%H%M%S"
    enable_claude_verification: bool = False

    # Validation thresholds
    min_model_size: int = 1_000_000  # 1MB minimum for valid models
    recent_attempt_hours: int = 1  # Hours to consider recent failure

    def __post_init__(self):
        """Initialize after creation."""
        self._load_from_toml()
        self._apply_env_overrides()
        self._ensure_dirs()

    def _load_from_toml(self):
        """Load configuration from default.toml if exists."""
        config_file = Path("config") / "default.toml"
        if config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    toml_data = tomllib.load(f)
                self._update_from_dict(toml_data)
            except Exception as e:
                print(f"Warning: Failed to load TOML config: {e}", file=sys.stderr)

    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        env_map = {
            "COMFYUI_ROOT": ("comfyui_root", lambda v: Path(v)),
            "OUTPUT_DIR": ("output_dir", lambda v: Path(v)),
            "LOG_DIR": ("log_dir", lambda v: Path(v)),
            "STATE_DIR": ("state_dir", lambda v: Path(v)),
            "TEMP_DIR": ("temp_dir", lambda v: Path(v)),
            "CIVITAI_API_TIMEOUT": ("civitai_api_timeout", int),
            "MIN_MODEL_SIZE": ("min_model_size", int),
            "RECENT_ATTEMPT_HOURS": ("recent_attempt_hours", int),
            "ENABLE_CLAUDE_VERIFICATION": ("enable_claude_verification", lambda v: v.lower() in ('true', '1', 'yes', 'on')),
        }

        for env_key, (attr, converter) in env_map.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    value = converter(env_value) if converter else env_value
                    setattr(self, attr, value)
                except ValueError:
                    print(f"Warning: Invalid value for {env_key}: {env_value}", file=sys.stderr)

    def _update_from_dict(self, data: Dict[str, Any]):
        """Update config from a dictionary (TOML or env)."""
        for key, value in data.items():
            if hasattr(self, key):
                # Handle special types
                if key == 'comfyui_root' and value is not None:
                    setattr(self, key, Path(value) if isinstance(value, str) else value)
                elif key == 'workflow_dirs' and isinstance(value, list):
                    setattr(self, key, [Path(p) if isinstance(p, str) else p for p in value])
                elif key == 'output_dir' and isinstance(value, str):
                    setattr(self, key, Path(value))
                elif key == 'log_dir' and isinstance(value, str):
                    setattr(self, key, Path(value))
                elif key == 'state_dir' and isinstance(value, str):
                    setattr(self, key, Path(value))
                elif key == 'temp_dir' and isinstance(value, str):
                    setattr(self, key, Path(value))
                # Handle lists and dicts
                elif isinstance(getattr(self, key), list) and isinstance(value, list):
                    setattr(self, key, value)
                elif isinstance(getattr(self, key), dict) and isinstance(value, dict):
                    setattr(self, key, value)
                elif key == 'enable_claude_verification' and isinstance(value, str):
                    setattr(self, key, value.lower() in ('true', '1', 'yes', 'on'))
                else:
                    setattr(self, key, value)

    def validate(self, require_comfyui_path: bool = True):
        """Validate configuration settings.

        Args:
            require_comfyui_path: If True, require ComfyUI root path to exist
        """
        if require_comfyui_path and self.comfyui_root is None:
            raise ValueError("comfyui_root must be configured")

        if require_comfyui_path and self.comfyui_root is not None and not self.comfyui_root.exists():
            raise ValueError(f"ComfyUI root does not exist: {self.comfyui_root}")

        if self.civitai_api_timeout < 5:
            raise ValueError("civitai_api_timeout must be at least 5 seconds")

        if self.min_model_size < 0:
            raise ValueError("min_model_size must be non-negative")

    def _ensure_dirs(self):
        """Ensure configuration directories exist."""
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        self.state_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

    @property
    def models_dir(self) -> Optional[Path]:
        """ComfyUI models directory."""
        return self.comfyui_root / "models" if self.comfyui_root else None

    @property
    def state_file_path(self) -> Path:
        """Full path to state file."""
        return self.state_dir / self.state_file

    def get_log_file(self, run_id: Optional[str] = None) -> str:
        """Get log file path with optional run ID."""
        if run_id:
            return str(self.log_dir / f"run_{run_id}.log")
        return str(self.log_dir / f"run_{datetime.now().strftime(self.run_id_format)}.log")

    def get_search_log_file(self) -> str:
        """Get search log file path."""
        return str(self.log_dir / self.search_log_file)

    def get_download_counter_file(self) -> str:
        """Get download counter file path."""
        return str(self.output_dir / self.download_counter_file)

    def get_missing_models_file(self, run_id: Optional[str] = None) -> str:
        """Get missing models file path."""
        if run_id:
            return str(self.output_dir / f"missing_models_{run_id}.json")
        return str(self.output_dir / "missing_models.json")

    def get_resolutions_file(self, run_id: Optional[str] = None) -> str:
        """Get resolutions file path."""
        if run_id:
            return str(self.output_dir / f"resolutions_{run_id}.json")
        return str(self.output_dir / "resolutions.json")

# Global config instance
config = Config()