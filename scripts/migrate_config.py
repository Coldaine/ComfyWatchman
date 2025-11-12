#!/usr/bin/env python3
"""
Configuration Migration Script for ComfyFixerSmart

Migrates old configuration (environment variables, hardcoded values)
to new TOML-based configuration format.

Usage:
    python scripts/migrate_config.py [--config-path PATH] [--dry-run]

Options:
    --config-path PATH    Path to output config file (default: config/default.toml)
    --dry-run            Show what would be migrated without writing files
    --force              Overwrite existing config file
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import tomllib
import tomli_w

# Add src to path to import new modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from comfywatchman.config import Config


def detect_old_config() -> Dict[str, Any]:
    """Detect and collect old configuration from environment variables and defaults."""
    old_config = {}

    # Check for environment variables that might contain old config
    env_mappings = {
        'COMFYUI_ROOT': 'comfyui_root',
        'CIVITAI_API_KEY': 'civitai_api_key',  # Not in new config but might exist
        'OUTPUT_DIR': 'output_dir',
        'LOG_DIR': 'log_dir',
        'STATE_DIR': 'state_dir',
    }

    for env_var, config_key in env_mappings.items():
        value = os.getenv(env_var)
        if value:
            if config_key in ['output_dir', 'log_dir', 'state_dir', 'comfyui_root']:
                old_config[config_key] = Path(value)
            else:
                old_config[config_key] = value

    # Check for old workflow directories in common locations
    potential_workflow_dirs = [
        Path("workflows"),
        Path("user/default/workflows"),
        Path("~/ComfyUI/user/default/workflows").expanduser(),
    ]

    workflow_dirs = []
    for wf_dir in potential_workflow_dirs:
        if wf_dir.exists() and wf_dir.is_dir():
            workflow_dirs.append(wf_dir)

    if workflow_dirs:
        old_config['workflow_dirs'] = workflow_dirs

    # Check for old ComfyUI root detection
    potential_comfyui_roots = [
        Path("~/ComfyUI").expanduser(),
        Path("../ComfyUI"),
        Path("../../ComfyUI"),
    ]

    for root in potential_comfyui_roots:
        if root.exists() and (root / "models").exists():
            old_config['comfyui_root'] = root
            break

    return old_config


def create_new_config(old_config: Dict[str, Any]) -> Config:
    """Create new Config object from old configuration."""
    new_config = Config()

    # Map old config to new config
    if 'comfyui_root' in old_config:
        new_config.comfyui_root = old_config['comfyui_root']

    if 'workflow_dirs' in old_config:
        new_config.workflow_dirs = old_config['workflow_dirs']

    if 'output_dir' in old_config:
        new_config.output_dir = Path(old_config['output_dir'])

    if 'log_dir' in old_config:
        new_config.log_dir = Path(old_config['log_dir'])

    if 'state_dir' in old_config:
        new_config.state_dir = Path(old_config['state_dir'])

    return new_config


def config_to_dict(config: Config) -> Dict[str, Any]:
    """Convert Config object to dictionary suitable for TOML serialization."""
    config_dict = {}

    # Paths
    if config.comfyui_root:
        config_dict['comfyui_root'] = str(config.comfyui_root)

    if config.workflow_dirs:
        config_dict['workflow_dirs'] = [str(d) for d in config.workflow_dirs]

    config_dict['output_dir'] = str(config.output_dir)
    config_dict['log_dir'] = str(config.log_dir)
    config_dict['state_dir'] = str(config.state_dir)

    # Search and logging
    config_dict['search_log_file'] = config.search_log_file
    config_dict['download_counter_file'] = config.download_counter_file

    # API Settings
    config_dict['civitai_api_base'] = config.civitai_api_base
    config_dict['civitai_download_base'] = config.civitai_download_base
    config_dict['civitai_api_timeout'] = config.civitai_api_timeout

    # Model Settings
    config_dict['model_extensions'] = config.model_extensions
    config_dict['model_type_mapping'] = config.model_type_mapping

    # State Management
    config_dict['state_file'] = config.state_file

    return config_dict


def main():
    parser = argparse.ArgumentParser(
        description="Migrate ComfyFixerSmart configuration from old to new format"
    )
    parser.add_argument(
        '--config-path',
        type=Path,
        default=Path('config/default.toml'),
        help='Path to output config file (default: config/default.toml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without writing files'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing config file'
    )

    args = parser.parse_args()

    print("🔍 Detecting old configuration...")
    old_config = detect_old_config()

    if not old_config:
        print("ℹ️  No old configuration detected. Using defaults.")
        old_config = {}

    print(f"📋 Found {len(old_config)} configuration items:")
    for key, value in old_config.items():
        print(f"   {key}: {value}")

    print("\n🏗️  Creating new configuration...")
    new_config = create_new_config(old_config)
    config_dict = config_to_dict(new_config)

    print("📝 New configuration preview:")
    for key, value in config_dict.items():
        print(f"   {key}: {value}")

    if args.dry_run:
        print("\n🔍 Dry run - no files written.")
        return

    # Check if config file exists
    if args.config_path.exists() and not args.force:
        print(f"\n❌ Config file {args.config_path} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Ensure config directory exists
    args.config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config file
    try:
        with open(args.config_path, 'wb') as f:
            tomli_w.dump(config_dict, f)
        print(f"\n✅ Configuration migrated successfully to {args.config_path}")
    except Exception as e:
        print(f"\n❌ Failed to write config file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()