#!/usr/bin/env python3
"""
Organize Lazy Models Script

This script scans the LAzy directory and moves model files to their appropriate
subdirectories in the ComfyUI models folder based on detected model types.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add the ScanTool directory to the path
SCAN_TOOL_PATH = "/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart/ScanTool"
sys.path.append(SCAN_TOOL_PATH)

from comfyui_model_scanner import scan, setup_logging


def create_directories_if_not_exist(base_path):
    """Create all necessary model directories if they don't exist"""
    directories = [
        "checkpoints",
        "loras", 
        "vae",
        "embeddings",
        "controlnet",
        "upscale_models",
        "clip",
        "clip_vision",
        "diffusion_models",
        "unet",
        "gligen",
        "hypernetworks",
        "photomaker"
    ]
    
    for directory in directories:
        dir_path = Path(base_path) / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")


def get_target_directory(model_type):
    """Map model type to target directory"""
    mapping = {
        "checkpoint": "checkpoints",
        "lora": "loras",
        "vae": "vae", 
        "controlnet": "controlnet",
        "embedding": "embeddings",
        "upscale": "upscale_models",
        "clip": "clip",
        "clip_vision": "clip_vision",
        "diffusion_model": "diffusion_models",
        "unet": "unet",
        "gligen": "gligen",
        "hypernetwork": "hypernetworks",
        "photomaker": "photomaker"
    }
    
    # Default to loras for unknown types or fallback
    return mapping.get(model_type.lower(), "loras")


def organize_models():
    """Main function to organize models from LAzy directory"""
    # Setup logging
    logger = setup_logging(1)
    
    # Define paths
    lazy_dir = "/home/coldaine/StableDiffusionWorkflow/LAzy"
    comfy_models_dir = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models"
    
    print(f"Organizing models from: {lazy_dir}")
    print(f"To ComfyUI models directory: {comfy_models_dir}")
    
    # Ensure all necessary directories exist
    create_directories_if_not_exist(comfy_models_dir)
    
    # Scan the LAzy directory
    print("\nScanning LAzy directory...")
    results = scan(comfy_root=lazy_dir, logger=logger)
    
    print(f"\nFound {len(results)} model files to organize")
    
    # Organize files by type
    moved_count = 0
    error_count = 0
    
    for model in results:
        try:
            source_path = Path(model["path"])
            model_type = model.get("type_hint", "unknown")
            
            # Get target directory based on model type
            target_subdir = get_target_directory(model_type)
            target_dir = Path(comfy_models_dir) / target_subdir
            
            # Create target filename (preserve original name)
            target_filename = source_path.name
            target_path = target_dir / target_filename
            
            # Skip if file already exists in target location
            if target_path.exists():
                print(f"Skipping (already exists): {target_filename}")
                continue
                
            # Move file
            print(f"Moving {model_type}: {target_filename} -> {target_path}")
            shutil.move(str(source_path), str(target_path))
            moved_count += 1
            
        except Exception as e:
            print(f"Error moving {model.get('path', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\n=== Organization Complete ===")
    print(f"Successfully moved: {moved_count} files")
    print(f"Errors: {error_count} files")
    print(f"Total processed: {len(results)} files")
    
    if moved_count > 0:
        print(f"\nModels have been organized into: {comfy_models_dir}")
        print("You can now run the ComfyFixerSmart download script to get any remaining missing models.")


if __name__ == "__main__":
    organize_models()