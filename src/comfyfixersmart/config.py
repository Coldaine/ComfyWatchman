import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import shlex

import tomllib


@dataclass
class CopilotConfig:
    """Configuration for the ComfyUI-Copilot integration."""

    enable_validation: bool = False
    enable_auto_repair: bool = False
    enable_modelscope: bool = False


@dataclass
class SearchConfig:
    """Configuration for model search functionalities."""

    backend_order: List[str] = field(default_factory=list)  # Will be set dynamically
    civitai_api_key: Optional[str] = os.getenv("CIVITAI_API_KEY")
    enable_cache: bool = True
    cache_ttl: int = 86400
    known_models_map: str = "civitai_tools/config/known_models.json"
    civitai_use_direct_id: bool = True
    min_confidence_threshold: int = 50
    enable_qwen: bool = True
    qwen_timeout: int = 900  # seconds
    qwen_cache_ttl: int = 30 * 24 * 3600  # 30 days
    qwen_binary: str = field(default_factory=lambda: os.getenv("QWEN_BINARY", "qwen"))
    qwen_extra_args: List[str] = field(default_factory=list)


@dataclass
class StateConfig:
    """Configuration for state management."""

    backend: str = "json"  # or "sql"
    json_path: str = "state/"
    sql_url: str = "sqlite:///state.db"


@dataclass
class DownloadConfig:
    """Configuration for model download functionality."""

    mode: str = "python"  # python | script | both
    verify_hashes: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class Config:
    """Configuration class for ComfyFixerSmart with defaults, TOML loading, and env overrides."""

    # Core settings
    comfyui_root: Optional[Path] = None
    workflow_dirs: List[Path] = field(default_factory=list)
    output_dir: Path = Path("output")
    log_dir: Path = Path("log")
    temp_dir: Path = Path("/tmp") / "qwen_search_results"
    run_id_format: str = "%Y%m%d_%H%M%S"

    # Nested configurations
    copilot: CopilotConfig = field(default_factory=CopilotConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    state: StateConfig = field(default_factory=StateConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)

    # API
    civitai_api_base: str = "https://civitai.com/api/v1"
    civitai_download_base: str = "https://civitai.com/api/download/models"
    civitai_api_timeout: int = 30

    # Model settings
    model_extensions: List[str] = field(
        default_factory=lambda: [".safetensors", ".ckpt", ".pt", ".bin", ".pth"]
    )
    model_type_mapping: Dict[str, str] = field(
        default_factory=lambda: {
            "CheckpointLoaderSimple": "checkpoints",
            "CheckpointLoader": "checkpoints",
            "LoraLoader": "loras",
            "LoraLoaderModelOnly": "loras",
            "VAELoader": "vae",
            "CLIPLoader": "clip",
            "DualCLIPLoader": "clip",
            "ControlNetLoader": "controlnet",
            "UpscaleModelLoader": "upscale_models",
            "CLIPVisionLoader": "clip_vision",
            "UNETLoader": "unet",
            "SAMLoader": "sams",
            "GroundingDinoModelLoader": "grounding-dino",
            # Video Frame Interpolation (VFI) models - stored in checkpoints directory
            "RIFE VFI": "checkpoints",
            "GMFSS Fortuna VFI": "checkpoints",
            "IFRNet VFI": "checkpoints",
            "IFUnet VFI": "checkpoints",
            "M2M VFI": "checkpoints",
            "Sepconv VFI": "checkpoints",
            "AMT VFI": "checkpoints",
            "FILM VFI": "checkpoints",
            "STMFNet VFI": "checkpoints",
            "FLAVR VFI": "checkpoints",
            "CAIN VFI": "checkpoints",
            "DownloadAndLoadGIMMVFIModel": "checkpoints",
            # Ultralytics YOLO detection models
            "UltralyticsDetectorProvider": "ultralytics",
            # HunyuanVideo models
            "HunyuanVideoLoraLoader": "loras",
            # WanVideo models
            "WanVideoLoraSelect": "loras",
            "WanVideoLoraSelectMulti": "loras",
            "LoadWanVideoT5TextEncoder": "text_encoders",
            "WanVideoVAELoader": "vae",
            "WanVideoModelLoader": "diffusion_models",
            "WanVideoControlnetLoader": "controlnet",
            "TextualInversionLoader": "embeddings",
            "TextualInversionApply": "embeddings",
            "EmbeddingLoader": "embeddings",
            "EmbeddingSelector": "embeddings",
            "TextEmbeddingLoader": "embeddings",
        }
    )

    # Logging
    log_format: str = "%Y-%m-%d %H:%M:%S"
    search_log_file: str = "qwen_search_history.log"

    # Validation thresholds
    min_model_size: int = 1_000_000  # 1MB minimum for valid models
    recent_attempt_hours: int = 1  # Hours to consider recent failure

    def __post_init__(self):
        """Initialize after creation."""
        self._load_from_toml()
        self._apply_env_overrides()
        self._set_default_backend_order()
        self._ensure_dirs()

    @property
    def state_dir(self) -> Path:
        """Provide backward compatibility for state_dir access."""
        return Path(self.state.json_path)

    def _load_from_toml(self):
        """Load configuration from default.toml if exists."""
        config_file = Path("config") / "default.toml"
        if config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    toml_data = tomllib.load(f)
                self._update_from_dict(self, toml_data)
            except Exception as e:
                print(f"Warning: Failed to load TOML config: {e}", file=sys.stderr)

    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        env_map = {
            "COMFYUI_ROOT": ("comfyui_root", lambda v: Path(v)),
            "OUTPUT_DIR": ("output_dir", lambda v: Path(v)),
            "LOG_DIR": ("log_dir", lambda v: Path(v)),
            "TEMP_DIR": ("temp_dir", lambda v: Path(v)),
            "CIVITAI_API_TIMEOUT": ("civitai_api_timeout", int),
            "MIN_MODEL_SIZE": ("min_model_size", int),
            "RECENT_ATTEMPT_HOURS": ("recent_attempt_hours", int),
        }

        # Apply download-specific environment variables
        download_env_map = {
            "DOWNLOAD_MODE": "mode",
            "DOWNLOAD_VERIFY_HASHES": ("verify_hashes", lambda v: v.lower() in ("true", "1", "yes")),
            "DOWNLOAD_MAX_RETRIES": ("max_retries", int),
            "DOWNLOAD_TIMEOUT": ("timeout_seconds", int),
        }

        for env_key, (attr, converter) in env_map.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    value = converter(env_value) if converter else env_value
                    setattr(self, attr, value)
                except ValueError:
                    print(f"Warning: Invalid value for {env_key}: {env_value}", file=sys.stderr)

        # Apply download config environment overrides
        for env_key, attr_info in download_env_map.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    if isinstance(attr_info, tuple):
                        attr, converter = attr_info
                        value = converter(env_value)
                    else:
                        attr = attr_info
                        value = env_value
                    setattr(self.download, attr, value)
                except ValueError:
                    print(f"Warning: Invalid value for {env_key}: {env_value}", file=sys.stderr)

        # Apply search config environment overrides
        search_env_map = {
            "ENABLE_QWEN": ("enable_qwen", lambda v: v.lower() in ("true", "1", "yes")),
            "QWEN_TIMEOUT": ("qwen_timeout", int),
            "QWEN_CACHE_TTL": ("qwen_cache_ttl", int),
            "QWEN_BINARY": ("qwen_binary", str),
            "QWEN_EXTRA_ARGS": ("qwen_extra_args", lambda v: shlex.split(v)),
        }

        for env_key, attr_info in search_env_map.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    attr, converter = attr_info
                    setattr(self.search, attr, converter(env_value))
                except ValueError:
                    print(f"Warning: Invalid value for {env_key}: {env_value}", file=sys.stderr)

    def _update_from_dict(self, config_obj: Any, data: Dict[str, Any]):
        """Recursively update config from a dictionary."""
        for key, value in data.items():
            if hasattr(config_obj, key):
                attr = getattr(config_obj, key)
                if isinstance(
                    attr, (CopilotConfig, SearchConfig, StateConfig, DownloadConfig)
                ) and isinstance(value, dict):
                    self._update_from_dict(attr, value)
                elif isinstance(value, dict) and hasattr(attr, "__dataclass_fields__"):
                    self._update_from_dict(attr, value)
                else:
                    # Handle special types
                    if key == "comfyui_root" and value is not None:
                        setattr(config_obj, key, Path(value) if isinstance(value, str) else value)
                    elif key == "workflow_dirs" and isinstance(value, list):
                        setattr(
                            config_obj, key, [Path(p) if isinstance(p, str) else p for p in value]
                        )
                    elif key in ["output_dir", "log_dir", "temp_dir"] and isinstance(value, str):
                        setattr(config_obj, key, Path(value))
                    else:
                        setattr(config_obj, key, value)

    def validate(self, require_comfyui_path: bool = True):
        """Validate configuration settings.

        Args:
            require_comfyui_path: If True, require ComfyUI root path to exist
        """
        if require_comfyui_path and self.comfyui_root is None:
            raise ValueError("comfyui_root must be configured")

        if (
            require_comfyui_path
            and self.comfyui_root is not None
            and not self.comfyui_root.exists()
        ):
            raise ValueError(f"ComfyUI root does not exist: {self.comfyui_root}")

        if self.civitai_api_timeout < 5:
            raise ValueError("civitai_api_timeout must be at least 5 seconds")

        if self.min_model_size < 0:
            raise ValueError("min_model_size must be non-negative")

    def _ensure_dirs(self):
        """Ensure configuration directories exist."""
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        # Ensure state path from config is created
        Path(self.state.json_path).mkdir(exist_ok=True)

    def _set_default_backend_order(self):
        """Set the default backend order based on available backends and configuration."""
        # Import here to avoid circular imports
        from .adapters import MODELSCOPE_AVAILABLE

        # Default order: Qwen as primary agentic search orchestrator, then direct API backends
        # Qwen provides intelligent multi-source search with reasoning and result synthesis
        default_order = ["qwen", "civitai"]

        # Add ModelScope if enabled and available
        if self.copilot.enable_modelscope and MODELSCOPE_AVAILABLE:
            default_order.insert(1, "modelscope")  # Add after Qwen but before others

        # Use configured order if provided, otherwise use default
        if not self.search.backend_order:
            self.search.backend_order = default_order

    @property
    def models_dir(self) -> Optional[Path]:
        """ComfyUI models directory."""
        return self.comfyui_root / "models" if self.comfyui_root else None

    @property
    def state_file_path(self) -> Path:
        """Full path to state file."""
        return Path(self.state.json_path) / "download_state.json"

    def get_log_file(self, run_id: Optional[str] = None) -> str:
        """Get log file path with optional run ID."""
        if run_id:
            return str(self.log_dir / f"run_{run_id}.log")
        return str(self.log_dir / f"run_{datetime.now().strftime(self.run_id_format)}.log")

    def get_search_log_file(self) -> str:
        """Get search log file path."""
        return str(self.log_dir / self.search_log_file)


# Global config instance
config = Config()  # Kilo Experiment - Copilot Configuration Flags
