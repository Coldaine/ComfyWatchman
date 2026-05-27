"""
Unit tests for config.py (Config, CopilotConfig, SearchConfig, DownloadConfig dataclasses).
"""


def Config(*args, **kwargs):
    from comfywatchman.config import Config as _Config

    return _Config(*args, **kwargs)


def CopilotConfig(*args, **kwargs):
    from comfywatchman.config import CopilotConfig as _CopilotConfig

    return _CopilotConfig(*args, **kwargs)


def DownloadConfig(*args, **kwargs):
    from comfywatchman.config import DownloadConfig as _DownloadConfig

    return _DownloadConfig(*args, **kwargs)


def SearchConfig(*args, **kwargs):
    from comfywatchman.config import SearchConfig as _SearchConfig

    return _SearchConfig(*args, **kwargs)


def StateConfig(*args, **kwargs):
    from comfywatchman.config import StateConfig as _StateConfig

    return _StateConfig(*args, **kwargs)


class TestCopilotConfig:
    def test_defaults(self):
        """CopilotConfig should default to all-disabled."""
        cfg = CopilotConfig()
        assert cfg.enable_validation is False
        assert cfg.enable_auto_repair is False
        assert cfg.enable_modelscope is False

    def test_can_enable_validation(self):
        """enable_validation can be set to True."""
        cfg = CopilotConfig(enable_validation=True)
        assert cfg.enable_validation is True

    def test_can_enable_all(self):
        """All flags can be toggled independently."""
        cfg = CopilotConfig(enable_validation=True, enable_auto_repair=True, enable_modelscope=True)
        assert cfg.enable_validation is True
        assert cfg.enable_auto_repair is True
        assert cfg.enable_modelscope is True


class TestSearchConfig:
    def test_cache_enabled_by_default(self):
        """Search cache should be enabled by default."""
        cfg = SearchConfig()
        assert cfg.enable_cache is True

    def test_cache_ttl_default(self):
        """Default cache TTL should be 86400 seconds (1 day)."""
        cfg = SearchConfig()
        assert cfg.cache_ttl == 86_400

    def test_min_confidence_threshold_default(self):
        """Default minimum confidence threshold should be 50."""
        cfg = SearchConfig()
        assert cfg.min_confidence_threshold == 50

    def test_qwen_enabled_by_default(self):
        """Qwen backend should be enabled by default."""
        cfg = SearchConfig()
        assert cfg.enable_qwen is True

    def test_cache_can_be_disabled(self):
        """enable_cache can be set to False."""
        cfg = SearchConfig(enable_cache=False)
        assert cfg.enable_cache is False


class TestDownloadConfig:
    def test_default_mode_is_python(self):
        """Default download mode should be 'python'."""
        cfg = DownloadConfig()
        assert cfg.mode == "python"

    def test_verify_hashes_enabled_by_default(self):
        """Hash verification should be enabled by default."""
        cfg = DownloadConfig()
        assert cfg.verify_hashes is True

    def test_default_max_retries(self):
        """Default max retries should be 3."""
        cfg = DownloadConfig()
        assert cfg.max_retries == 3

    def test_can_override_mode(self):
        """Download mode can be changed to 'script'."""
        cfg = DownloadConfig(mode="script")
        assert cfg.mode == "script"


class TestStateConfig:
    def test_default_backend_is_json(self):
        """Default state backend should be 'json'."""
        cfg = StateConfig()
        assert cfg.backend == "json"

    def test_json_path_default(self):
        """Default JSON state path should be 'state/'."""
        cfg = StateConfig()
        assert cfg.json_path == "state/"


class TestConfigModelTypeMapping:
    def test_checkpoint_loader_maps_to_checkpoints(self):
        """CheckpointLoaderSimple must map to 'checkpoints' directory."""
        cfg = Config()
        assert cfg.model_type_mapping["CheckpointLoaderSimple"] == "checkpoints"

    def test_lora_loader_maps_to_loras(self):
        """LoraLoader must map to 'loras' directory."""
        cfg = Config()
        assert cfg.model_type_mapping["LoraLoader"] == "loras"

    def test_vae_loader_maps_to_vae(self):
        """VAELoader must map to 'vae' directory."""
        cfg = Config()
        assert cfg.model_type_mapping["VAELoader"] == "vae"

    def test_controlnet_loader_maps_to_controlnet(self):
        """ControlNetLoader must map to 'controlnet' directory."""
        cfg = Config()
        assert cfg.model_type_mapping["ControlNetLoader"] == "controlnet"

    def test_model_extensions_defaults(self):
        """Default model extensions should include .safetensors and .ckpt."""
        cfg = Config()
        assert ".safetensors" in cfg.model_extensions
        assert ".ckpt" in cfg.model_extensions
