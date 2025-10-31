#!/usr/bin/env python3
"""
Script to search for missing models using the CivitAI API.
Based on the ComfyWatchman codebase but simplified for direct API usage.
"""

import os
import requests
import json
import time
from typing import Dict, List, Optional, Tuple

# Get API key from environment (loaded from ~/.secrets)
CIVITAI_API_KEY = os.getenv("CIVITAI_API_KEY", "")
if not CIVITAI_API_KEY:
    print("CIVITAI_API_KEY not found in environment")
    # Try to load from secrets file
    secrets_path = os.path.expanduser("~/.secrets")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                if line.startswith("export CIVITAI_API_KEY="):
                    CIVITAI_API_KEY = line.split("=")[1].strip().strip('"\'')
                    break

if not CIVITAI_API_KEY:
    print("ERROR: CIVITAI_API_KEY not found in environment or ~/.secrets")
    exit(1)

BASE_URL = "https://civitai.com/api/v1"
HEADERS = {"Authorization": f"Bearer {CIVITAI_API_KEY}"}

def _prepare_search_query(filename: str) -> str:
    """Prepare filename for search query."""
    # Normalize separators and remove extension
    base = filename
    # Remove common extensions
    base = base.replace(".safetensors", "").replace(".pth", ".pt").replace(".ckpt", "")
    # Replace underscores, spaces, and other separators with spaces
    import re
    query = re.sub(r"[\\/_.-]+", " ", base)
    return query.strip()

def _get_type_filter(model_type: str) -> Optional[str]:
    """Get Civitai type filter from model type."""
    type_mapping = {
        "checkpoints": "Checkpoint",
        "loras": "LORA",
        "vae": "VAE",
        "controlnet": "Controlnet",
        "upscale_models": "Upscaler",
        "clip": "TextualInversion",
        "embeddings": "TextualInversion",
        "unet": "Checkpoint",
    }
    # For automatic type detection, we'll return None and let Civitai search broadly
    return None

def search_civitai_model(filename: str, model_type: str = "") -> Optional[Dict]:
    """
    Search for a single model using the CivitAI API.
    
    Args:
        filename: The filename to search for
        model_type: Model type for filtering (optional)
    
    Returns:
        Dictionary with search results, or None if not found
    """
    print(f"Searching CivitAI for: {filename}")
    
    # Prepare search query
    query = _prepare_search_query(filename)
    print(f"  Using query: {query}")
    
    # Build search parameters
    params = {"query": query, "limit": 10, "sort": "Highest Rated"}
    
    # Add type filtering if applicable
    type_filter = _get_type_filter(model_type)
    if type_filter:
        params["types"] = type_filter
    
    try:
        response = requests.get(
            f"{BASE_URL}/models",
            params=params,
            headers=HEADERS,
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"  API error: {response.status_code}")
            return None
        
        results = response.json().get("items", [])
        
        if not results:
            print(f"  No results found for: {filename}")
            return None
        
        # Look for exact filename match in the model files
        for result in results:
            for version in result.get("modelVersions", []):
                for file_info in version.get("files", []):
                    if file_info.get("name", "").lower() == filename.lower():
                        print(f"  FOUND: {filename}")
                        return {
                            "status": "FOUND",
                            "filename": filename,
                            "civitai_id": result.get("id"),
                            "version_id": version.get("id"),
                            "civitai_name": result.get("name"),
                            "version_name": version.get("name"),
                            "download_url": f"https://civitai.com/api/download/models/{version.get('id')}",
                            "model_type": model_type,
                            "details": {
                                "model": result,
                                "version": version
                            }
                        }
        
        # If no exact match, return the top result for manual review
        top_result = results[0]
        print(f"  No exact filename match found, but top result: {top_result.get('name')}")
        return {
            "status": "UNCERTAIN",
            "filename": filename,
            "top_match": top_result.get("name"),
            "model_id": top_result.get("id"),
            "details": {
                "model": top_result
            }
        }
    
    except Exception as e:
        print(f"  Error searching for {filename}: {e}")
        return None

def search_multiple_models(filenames: List[str], model_type: str = "") -> List[Dict]:
    """Search for multiple models."""
    results = []
    for filename in filenames:
        result = search_civitai_model(filename, model_type)
        if result:
            results.append(result)
        
        # Be respectful to the API - add a small delay
        time.sleep(0.5)
    
    return results

def main():
    # List of missing models from our analysis
    missing_models = [
        '4x-AnimeSharp.pth',
        '4x-ClearRealityV1.pth',
        'Ana_de_Armas_FLUX_v1-000061.safetensors',
        'autismmixSDXL_autismmixPony.safetensors',
        'BounceHighWan2_2.safetensors',
        'BounceLowWan2_2.safetensors',
        'Dark (Illustrious) v1.safetensors',
        'DR34ML4Y_I2V_14B_HIGH.safetensors',
        'Eyes.pt',
        'female-breast-v4.7.pt',
        'flux1-dev-fp8.safetensors',
        'furry_nsfw_1.1_e22.safetensors',
        'gimmvfi_r_arb_lpips_fp32.safetensors',
        'high_noise_model.safetensors',
        'lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors',
        'low_noise_model.safetensors',
        'myckpt_00001_.safetensors',
        'nsfw_wan_umt5-xxl_fp8_scaled.safetensors',
        'pussy.pt',
        'RealESRGAN_x2plus.pth',
        'RealESRGAN_x4plus_anime_6B.pth',
        'slop_twerk_HighNoise_merged3_7_v2.safetensors',
        'slop_twerk_LowNoise_merged3_7_v2.safetensors',
        'umt5-xxl-enc-bf16.safetensors',
        'umt5_xxl_fp16.safetensors',
        'Wan21_I2V_14B_lightx2v_cfg_step_distill_lora_rank64_fixed.safetensors',
        'wan21Lightspeed_clipT5EncoderFP8.safetensors',
        'wan21Lightspeed_lightspeedI2v14B480p.safetensors',
        'Wan2_1_VAE_bf16.safetensors',
        'Wan22-I2V-HIGH-Hip_Slammin_Assertive_Cowgirl.safetensors',
        'Wan22-I2V-LOW-Hip_Slammin_Assertive_Cowgirl.safetensors',
        'wan2.2-i2v-rapid-aio-v10-nsfw.safetensors',
        'Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors',
        'wan-cumshot-I2V-22epo-k3nk.safetensors',
        'wan_cumshot_i2v.safetensors',
        'watermarks_s_yolov8_v1.pt'
    ]
    
    print(f"Searching for {len(missing_models)} missing models using CivitAI API...")
    print(f"API Key loaded: {'Yes' if CIVITAI_API_KEY else 'No'}")
    print("-" * 60)
    
    found_models = []
    uncertain_models = []
    not_found_models = []
    
    for i, filename in enumerate(missing_models):
        print(f"[{i+1}/{len(missing_models)}] {filename}")
        
        result = search_civitai_model(filename)
        
        if result and result.get("status") == "FOUND":
            found_models.append(result)
            print(f"    ✓ FOUND: {result['civitai_name']} (ID: {result['civitai_id']})")
            print(f"      Download URL: {result['download_url']}")
        elif result and result.get("status") == "UNCERTAIN":
            uncertain_models.append(result)
            print(f"    ? UNCERTAIN: Top match '{result['top_match']}' for '{filename}'")
        else:
            not_found_models.append(filename)
            print(f"    ✗ NOT FOUND: {filename}")
        
        print()
        
        # Add delay to be respectful to the API
        time.sleep(0.5)
    
    print("=" * 60)
    print("SEARCH COMPLETE")
    print("=" * 60)
    print(f"Found: {len(found_models)} models")
    print(f"Uncertain: {len(uncertain_models)} models")
    print(f"Not found: {len(not_found_models)} models")
    
    if found_models:
        print("\nFOUND MODELS:")
        print("-" * 40)
        for model in found_models:
            print(f"• {model['filename']}")
            print(f"  - Name: {model['civitai_name']}")
            print(f"  - ID: {model['civitai_id']}")
            print(f"  - Download: {model['download_url']}")
            print()
    
    if uncertain_models:
        print("\nUNCERTAIN MATCHES (Manual verification needed):")
        print("-" * 40)
        for model in uncertain_models:
            print(f"• {model['filename']} -> {model['top_match']} (ID: {model['model_id']})")
    
    if not_found_models:
        print("\nMODELS NOT FOUND:")
        print("-" * 40)
        for model in not_found_models:
            print(f"• {model}")

if __name__ == "__main__":
    main()