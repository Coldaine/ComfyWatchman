#!/usr/bin/env python3
"""
Move Downloaded Models Script

This script moves downloaded model files from the ComfyFixerSmart directory
to their appropriate subdirectories in the ComfyUI models folder.
"""

import os
import sys
import json
import shutil
from pathlib import Path

def move_downloaded_models():
    """Move downloaded models to correct directories"""
    # Define paths
    comfy_fixer_dir = "/home/coldaine/StableDiffusionWorkflow/ComfyFixerSmart"
    comfy_models_dir = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models"
    
    print(f"Moving downloaded models from: {comfy_fixer_dir}")
    print(f"To ComfyUI models directory: {comfy_models_dir}")
    
    # Find all downloaded model files in ComfyFixerSmart directory
    downloaded_files = list(Path(comfy_fixer_dir).glob("*.safetensors")) + \
                      list(Path(comfy_fixer_dir).glob("*.pt")) + \
                      list(Path(comfy_fixer_dir).glob("*.pth"))
    
    print(f"\nFound {len(downloaded_files)} downloaded model files")
    
    # Mapping of filename patterns to target directories
    file_mapping = {
        # Checkpoints
        "60fps.safetensors": ("checkpoints", "hunyuan_8itchw4lk_2_40.safetensors"),
        "ponyDiffusionV6XL_v6StartWithThisOne.safetensors": ("checkpoints", "bigLove_photo1.safetensors"),
        
        # VAE
        "aiartlabSdxlVae_v20.safetensors": ("vae", "vae-ft-mse-840000-ema-pruned.safetensors"),
        "Toon Factory illu v01.safetensors": ("vae", "AAA Anime VAE SDXL v2.safetensors"),
        
        # LoRAs
        "sacokabutan_illustriousXL.safetensors": ("loras", "XL/BIGLOVEsubtle-rayness2-xl25.safetensors"),
        "Aether_Exposure_low_noise_LoRA_wan22_14b_v1.safetensors": ("loras", "Wan2.2-Lightning_T2V-v1.1-A14B-4steps-lora_HIGH_fp16.safetensors"),
        "pencilmix2.safetensors": ("loras", "illustrious/748cmXL_NBVP1_lokr_V6311PZ.safetensors"),
        
        # Upscale models
        "realesrganX4plusAnime_v1.pt": ("upscale_models", "RealESRGAN_x4plus.safetensors"),
        "pinup512.pt": ("upscale_models", "1x-ITF-SkinDiffDetail-Lite-v1.pth"),
        "ponyDiffusionV6XL_v6StartWithThisOne.safetensors.4": ("upscale_models", "4xNMKDSuperscale_4xNMKDSuperscale.pt"),
        "ponyDiffusionV6XL_v6StartWithThisOne.safetensors.5": ("upscale_models", "rife49.pth"),
        "ponyDiffusionV6XL_v6StartWithThisOne.safetensors.3": ("upscale_models", "1xSkinContrast-High-SuperUltraCompact.pth"),
        
        # Other models
        "Raespark_-_Vtuber.safetensors": ("checkpoints", "sam_vit_b_01ec64.pth"),
        "I_think_were_gonna_have_to_kill_this_guy__Meme_Pose_Concept__IllustriousXL_and_NoobAI.safetensors": ("checkpoints", "damn_illustrious_v5.fp16.safetensors"),
        "Bee_Beatrix_Bee_Patient_Aarokira-000012.safetensors": ("checkpoints", "big-love?modelVersionId=1990969 )\nand lustifySDXLNSFW_endgame.safetensors work well for checkpoints.\n\n\n\nPROMPTING example\n\nnude asian woman      worked for bikini top "),
        "vace14BSAM2StabilizedSplit_v10.zip": ("checkpoints", "sam2_hiera_base_plus.safetensors"),
        "seedvr2OneStep4XVideoImage_v10.zip": ("checkpoints", "4x-UltraSharp.pth"),
        "748cm.safetensors": ("checkpoints", "film_net_fp32.pt"),
    }
    
    moved_count = 0
    error_count = 0
    
    for file_path in downloaded_files:
        filename = file_path.name
        
        # Special handling for files with numeric suffixes
        base_filename = filename
        if "." in filename and filename.split(".")[-1].isdigit():
            base_filename = ".".join(filename.split(".")[:-1])
        
        print(f"\nProcessing: {filename}")
        
        # Look for mapping
        target_info = None
        for pattern, target in file_mapping.items():
            if pattern in filename or pattern == filename:
                target_info = target
                break
        
        if target_info:
            target_dir, target_filename = target_info
            
            # Handle special characters in filenames
            if "\n" in target_filename:
                target_filename = target_filename.split("\n")[0]
            
            # Create target directory if it contains subdirectories
            full_target_dir = Path(comfy_models_dir) / target_dir
            if "/" in target_filename:
                subdir = "/".join(target_filename.split("/")[:-1])
                full_target_dir = full_target_dir / subdir
                full_target_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine final target path
            final_target_path = full_target_dir
            if "/" in target_filename:
                final_filename = target_filename.split("/")[-1]
                final_target_path = full_target_dir / final_filename
            else:
                final_target_path = full_target_dir / target_filename
            
            # Move file
            try:
                print(f"  Moving to: {final_target_path}")
                shutil.move(str(file_path), str(final_target_path))
                moved_count += 1
            except Exception as e:
                print(f"  Error moving {filename}: {e}")
                error_count += 1
        else:
            print(f"  No mapping found for {filename}")
            # Try to identify by extension and move to a default location for manual sorting
            ext = file_path.suffix.lower()
            if ext in ['.safetensors', '.ckpt']:
                target_dir = Path(comfy_models_dir) / "checkpoints"
            elif ext == '.pt':
                target_dir = Path(comfy_models_dir) / "checkpoints"  # Often PyTorch models
            elif ext == '.pth':
                target_dir = Path(comfy_models_dir) / "checkpoints"  # Often PyTorch models
            else:
                target_dir = Path(comfy_models_dir) / "checkpoints"
            
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename
            
            try:
                print(f"  Moving to: {target_path}")
                shutil.move(str(file_path), str(target_path))
                moved_count += 1
            except Exception as e:
                print(f"  Error moving {filename}: {e}")
                error_count += 1
    
    print(f"\n=== Move Operation Complete ===")
    print(f"Successfully moved: {moved_count} files")
    print(f"Errors: {error_count} files")
    
    # Check again with ComfyFixerSmart to see what's still missing
    print(f"\nChecking what's still missing...")
    

if __name__ == "__main__":
    move_downloaded_models()