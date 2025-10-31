#!/usr/bin/env python3
"""
Improved download script with better authentication handling.
"""

import os
import requests
import time
from pathlib import Path

# Get API key from environment
CIVITAI_API_KEY = os.getenv("CIVITAI_API_KEY", "")
if not CIVITAI_API_KEY:
    secrets_path = os.path.expanduser("~/.secrets")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                if line.startswith("export CIVITAI_API_KEY="):
                    CIVITAI_API_KEY = line.split("=")[1].strip().strip('"\'')
                    break

if not CIVITAI_API_KEY:
    print("ERROR: CIVITAI_API_KEY not found")
    exit(1)

def download_with_auth(url: str, filename: str, directory: str) -> bool:
    """Download a model file with proper authentication."""
    try:
        # Create directory if it doesn't exist
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Full path for the file
        filepath = os.path.join(directory, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            print(f"  ⚠️  File already exists: {filepath}")
            return True
        
        print(f"  📥 Downloading {filename}...")
        
        # Make the download request with proper headers
        headers = {
            "Authorization": f"Bearer {CIVITAI_API_KEY}",
            "User-Agent": "ComfyFixerSmart/2.0"
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=120)
        
        if response.status_code == 200:
            # Get the total file size
            total_size = response.headers.get('content-length')
            if total_size:
                total_size = int(total_size)
            
            # Write the content to file
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"\r    Progress: {percent:.1f}% ({downloaded/1024/1024:.1f}MB/{total_size/1024/1024:.1f}MB)", end='', flush=True)
            
            if total_size:
                print()  # New line after progress
            
            print(f"  ✅ Successfully downloaded to: {filepath}")
            return True
        elif response.status_code == 401:
            print(f"  ❌ Authentication failed (401) - Check API key")
            return False
        elif response.status_code == 403:
            print(f"  ❌ Access forbidden (403) - May require login or have download restrictions")
            return False
        elif response.status_code == 404:
            print(f"  ❌ File not found (404) - URL may be incorrect")
            return False
        else:
            print(f"  ❌ Download failed with status {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error downloading {filename}: {e}")
        return False

def main():
    # Models that we want to download
    models_to_download = [
        # WAN-related models in LORA directory
        {
            "download_url": "https://civitai.com/api/download/models/2358413",
            "filename": "wan2.2bullet_time_high_noise.safetensors",
            "directory": "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/loras"
        },
        {
            "download_url": "https://civitai.com/api/download/models/2350641", 
            "filename": "wan2.2DEEPFAKE_high_noise_x1.30.safetensors",
            "directory": "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/loras"
        },
        # FLUX model in checkpoints directory
        {
            "download_url": "https://civitai.com/api/download/models/2360245",
            "filename": "fluxtraitFLUX1DEVFor_v10FP8.safetensors",
            "directory": "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/checkpoints"
        }
    ]
    
    print(f"Attempting to download {len(models_to_download)} models with improved authentication...")
    print("=" * 80)
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, model in enumerate(models_to_download):
        print(f"[{i+1}/{len(models_to_download)}] {model['filename']}")
        print(f"  From: {model['download_url']}")
        print(f"  To: {model['directory']}/{model['filename']}")
        
        success = download_with_auth(
            model['download_url'], 
            model['filename'], 
            model['directory']
        )
        
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        print("-" * 50)
        
        # Small delay between downloads to be respectful to the server
        time.sleep(2)
    
    print("\n" + "=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total attempted: {len(models_to_download)}")
    
    if successful_downloads > 0:
        print(f"\nThe models have been downloaded to:")
        print(f"  LORA models: /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/loras/")
        print(f"  Checkpoint models: /home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/models/checkpoints/")

if __name__ == "__main__":
    main()