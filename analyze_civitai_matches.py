#!/usr/bin/env python3
"""
Script to analyze CivitAI search matches in more detail to find exact filenames.
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional

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

BASE_URL = "https://civitai.com/api/v1"
HEADERS = {"Authorization": f"Bearer {CIVITAI_API_KEY}"}

def get_model_details(model_id: int) -> Optional[Dict]:
    """Get detailed information about a specific model."""
    try:
        response = requests.get(
            f"{BASE_URL}/models/{model_id}",
            headers=HEADERS,
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"  Error getting model details for ID {model_id}: {response.status_code}")
            return None
        
        return response.json()
    
    except Exception as e:
        print(f"  Error getting model details for ID {model_id}: {e}")
        return None

def find_exact_filename_in_model(model_data: Dict, target_filename: str) -> Optional[Dict]:
    """Check if the target filename exists in any version of the model."""
    for version in model_data.get("modelVersions", []):
        for file_info in version.get("files", []):
            if file_info.get("name", "").lower() == target_filename.lower():
                return {
                    "filename": file_info.get("name"),
                    "model_name": model_data.get("name"),
                    "model_id": model_data.get("id"),
                    "version_name": version.get("name"),
                    "version_id": version.get("id"),
                    "download_url": f"https://civitai.com/api/download/models/{version.get('id')}",
                    "sizeKB": file_info.get("sizeKB"),
                    "type": file_info.get("type"),
                    "pickleScanResult": file_info.get("pickleScanResult"),
                    "virusScanResult": file_info.get("virusScanResult")
                }
    return None

def analyze_uncertain_match(model_id: int, target_filename: str) -> Optional[Dict]:
    """Get detailed model information and check for exact filename match."""
    print(f"  Analyzing model ID {model_id} for filename: {target_filename}")
    
    model_data = get_model_details(model_id)
    if not model_data:
        return None
    
    exact_match = find_exact_filename_in_model(model_data, target_filename)
    if exact_match:
        print(f"    ✓ EXACT MATCH FOUND!")
        return exact_match
    else:
        print(f"    ✗ No exact match found")
        # List all available files in the model for reference
        print("    Available files:")
        for version in model_data.get("modelVersions", []):
            print(f"      Version: {version.get('name')}")
            for file_info in version.get("files", []):
                print(f"        - {file_info.get('name')} ({file_info.get('type')})")
        print()
        return None

def main():
    # Uncertain matches from the previous search
    uncertain_matches = [
        {"filename": "4x-AnimeSharp.pth", "model_id": 1017531},
        {"filename": "4x-ClearRealityV1.pth", "model_id": 1017531},
        {"filename": "Ana_de_Armas_FLUX_v1-000061.safetensors", "model_id": 1845672},
        {"filename": "autismmixSDXL_autismmixPony.safetensors", "model_id": 315644},
        {"filename": "BounceHighWan2_2.safetensors", "model_id": 257749},
        {"filename": "BounceLowWan2_2.safetensors", "model_id": 257749},
        {"filename": "Dark (Illustrious) v1.safetensors", "model_id": 2086934},
        {"filename": "DR34ML4Y_I2V_14B_HIGH.safetensors", "model_id": 257749},
        {"filename": "Eyes.pt", "model_id": 2087988},
        {"filename": "female-breast-v4.7.pt", "model_id": 2085057},
        {"filename": "flux1-dev-fp8.safetensors", "model_id": 2034574},
        {"filename": "furry_nsfw_1.1_e22.safetensors", "model_id": 2085528},
        {"filename": "gimmvfi_r_arb_lpips_fp32.safetensors", "model_id": 257749},
        {"filename": "high_noise_model.safetensors", "model_id": 2084928},
        {"filename": "lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors", "model_id": 2067816},
        {"filename": "low_noise_model.safetensors", "model_id": 2081043},
        {"filename": "myckpt_00001_.safetensors", "model_id": 257749},
        {"filename": "nsfw_wan_umt5-xxl_fp8_scaled.safetensors", "model_id": 1977779},
        {"filename": "pussy.pt", "model_id": 1909450},
        {"filename": "RealESRGAN_x2plus.pth", "model_id": 147821},
        {"filename": "RealESRGAN_x4plus_anime_6B.pth", "model_id": 147821},
        {"filename": "slop_twerk_HighNoise_merged3_7_v2.safetensors", "model_id": 1721929},
        {"filename": "slop_twerk_LowNoise_merged3_7_v2.safetensors", "model_id": 1721929},
        {"filename": "umt5-xxl-enc-bf16.safetensors", "model_id": 257749},
        {"filename": "umt5_xxl_fp16.safetensors", "model_id": 257749},
        {"filename": "Wan21_I2V_14B_lightx2v_cfg_step_distill_lora_rank64_fixed.safetensors", "model_id": 2075109},
        {"filename": "wan21Lightspeed_clipT5EncoderFP8.safetensors", "model_id": 257749},
        {"filename": "wan21Lightspeed_lightspeedI2v14B480p.safetensors", "model_id": 257749},
        {"filename": "Wan2_1_VAE_bf16.safetensors", "model_id": 2084396},
        {"filename": "Wan22-I2V-HIGH-Hip_Slammin_Assertive_Cowgirl.safetensors", "model_id": 2074953},
        {"filename": "Wan22-I2V-LOW-Hip_Slammin_Assertive_Cowgirl.safetensors", "model_id": 2074953},
        {"filename": "wan2.2-i2v-rapid-aio-v10-nsfw.safetensors", "model_id": 2084396},
        {"filename": "Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors", "model_id": 2084396},
        {"filename": "wan-cumshot-I2V-22epo-k3nk.safetensors", "model_id": 2084396},
        {"filename": "wan_cumshot_i2v.safetensors", "model_id": 2084396},
        {"filename": "watermarks_s_yolov8_v1.pt", "model_id": 753616}
    ]
    
    print(f"Analyzing {len(uncertain_matches)} uncertain matches for exact filename matches...")
    print("=" * 80)
    
    exact_matches = []
    no_matches = []
    
    for i, match in enumerate(uncertain_matches):
        print(f"[{i+1}/{len(uncertain_matches)}] Checking {match['filename']} in model ID {match['model_id']}")
        
        result = analyze_uncertain_match(match['model_id'], match['filename'])
        
        if result:
            exact_matches.append(result)
            print(f"  DOWNLOAD URL: {result['download_url']}")
        else:
            no_matches.append(match)
        
        print("-" * 50)
        
        # Be respectful to the API
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Exact matches found: {len(exact_matches)}")
    print(f"No matches found: {len(no_matches)}")
    
    if exact_matches:
        print("\n✅ EXACT MATCHES FOUND:")
        print("-" * 40)
        for match in exact_matches:
            print(f"• File: {match['filename']}")
            print(f"  Model: {match['model_name']}")
            print(f"  Version: {match['version_name']}")
            print(f"  Download: {match['download_url']}")
            print(f"  Size: {match.get('sizeKB', 'Unknown')} KB")
            print()
    
    if no_matches:
        print("\n❌ NO MATCHES FOUND:")
        print("-" * 40)
        for match in no_matches:
            print(f"• {match['filename']} (was looking in model ID {match['model_id']})")

if __name__ == "__main__":
    main()