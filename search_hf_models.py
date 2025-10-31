#!/usr/bin/env python3
"""
Search for models on HuggingFace as an alternative to Civitai.
"""

import os
import requests
import json
import time
from huggingface_hub import HfApi, hf_hub_download
from pathlib import Path

# Try to get HF token from environment
HF_TOKEN = os.getenv("HF_TOKEN", "")
if not HF_TOKEN:
    secrets_path = os.path.expanduser("~/.secrets")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                if line.startswith("export HF_TOKEN="):
                    HF_TOKEN = line.split("=")[1].strip().strip('"\'')
                    break

def search_hf_model(model_name: str) -> list:
    """Search for a model on HuggingFace."""
    try:
        api = HfApi()
        models = api.list_models(search=model_name, limit=5)
        return list(models)
    except Exception as e:
        print(f"Error searching for {model_name} on HuggingFace: {e}")
        return []

def download_hf_model(repo_id: str, filename: str, local_dir: str) -> bool:
    """Download a model file from HuggingFace."""
    try:
        print(f"  📥 Downloading {filename} from {repo_id}")
        
        # Create directory if it doesn't exist
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        
        # Download the file
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            token=HF_TOKEN if HF_TOKEN else None
        )
        
        print(f"  ✅ Successfully downloaded to: {local_dir}/{filename}")
        return True
    except Exception as e:
        print(f"  ❌ Error downloading {filename}: {e}")
        return False

def main():
    # Models we're looking for
    target_models = [
        "wan2.2bullet_time_high_noise",
        "wan2.2DEEPFAKE_high_noise",
        "fluxtraitFLUX1DEVFor",
        "RealESRGAN_x4plus_Anime_6B",
        "4x-AnimeSharp",
        "4x-ClearRealityV1"
    ]
    
    print("Searching for models on HuggingFace...")
    print("=" * 60)
    
    found_models = []
    
    for model_name in target_models:
        print(f"Searching for: {model_name}")
        models = search_hf_model(model_name)
        
        if models:
            print(f"  Found {len(models)} potential matches:")
            for model in models[:3]:  # Show top 3 matches
                print(f"    - {model.id}")
                found_models.append(model)
        else:
            print(f"  No matches found")
        
        print("-" * 40)
        time.sleep(1)  # Be respectful to the API
    
    if found_models:
        print(f"\nFound {len(found_models)} potential models on HuggingFace")
        print("You can manually download them using:")
        print("  huggingface-cli download <repo_id> <filename> --local-dir <destination>")
        
        for model in found_models[:5]:  # Show top 5
            print(f"  huggingface-cli download {model.id} <filename> --local-dir /path/to/download")
    else:
        print("\nNo models found on HuggingFace")

if __name__ == "__main__":
    main()