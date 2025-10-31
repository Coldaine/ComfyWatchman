#!/usr/bin/env python3
"""
Alternative search approach for missing models.
Trying broader searches and specific model types like WAN models.
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

def search_by_model_type_and_name(model_type: str, name_query: str) -> Optional[Dict]:
    """Search for a model by type and name."""
    print(f"Searching for {model_type} with query: {name_query}")
    
    params = {
        "query": name_query,
        "types": model_type,
        "limit": 10,
        "sort": "Highest Rated"
    }
    
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
            print(f"  No results found")
            return None
        
        print(f"  Found {len(results)} results")
        
        # Return all results for further processing
        return results
    except Exception as e:
        print(f"  Error in search: {e}")
        return None

def search_for_wan_models():
    """Specifically search for WAN-related models."""
    print("Searching for WAN-related models...")
    print("-" * 50)
    
    wan_searches = [
        {"query": "WAN 2.2", "type": "LORA"},
        {"query": "WAN2", "type": "LORA"},
        {"query": "Wan2", "type": "LORA"},
        {"query": "wan2", "type": "LORA"},
        {"query": "WAN video", "type": "LORA"},
        {"query": "WAN I2V", "type": "LORA"},
        {"query": "WAN T2V", "type": "LORA"},
    ]
    
    all_results = []
    
    for search in wan_searches:
        print(f"\nSearching: {search['query']} as {search['type']}")
        results = search_by_model_type_and_name(search['type'], search['query'])
        
        if results:
            for result in results:
                all_results.append({
                    "model_name": result.get("name"),
                    "model_id": result.get("id"),
                    "type": result.get("type"),
                    "nsfw_level": result.get("nsfwLevel", 1),
                    "details": result
                })
        
        time.sleep(0.5)  # Be respectful to API
    
    return all_results

def search_for_flux_models():
    """Search for FLUX-related models."""
    print("\nSearching for FLUX-related models...")
    print("-" * 50)
    
    flux_searches = [
        {"query": "FLUX", "type": "Checkpoint"},
        {"query": "flux", "type": "LORA"},
    ]
    
    all_results = []
    
    for search in flux_searches:
        print(f"\nSearching: {search['query']} as {search['type']}")
        results = search_by_model_type_and_name(search['type'], search['query'])
        
        if results:
            for result in results:
                all_results.append({
                    "model_name": result.get("name"),
                    "model_id": result.get("id"),
                    "type": result.get("type"),
                    "nsfw_level": result.get("nsfwLevel", 1),
                    "details": result
                })
        
        time.sleep(0.5)  # Be respectful to API
    
    return all_results

def search_for_upscale_models():
    """Search for upscaling models."""
    print("\nSearching for upscaling-related models...")
    print("-" * 50)
    
    upscale_searches = [
        {"query": "RealESRGAN", "type": "Upscaler"},
        {"query": "ESRGAN", "type": "Upscaler"},
        {"query": "RealESRGAN", "type": "LORA"},
    ]
    
    all_results = []
    
    for search in upscale_searches:
        print(f"\nSearching: {search['query']} as {search['type']}")
        results = search_by_model_type_and_name(search['type'], search['query'])
        
        if results:
            for result in results:
                all_results.append({
                    "model_name": result.get("name"),
                    "model_id": result.get("id"),
                    "type": result.get("type"),
                    "nsfw_level": result.get("nsfwLevel", 1),
                    "details": result
                })
        
        time.sleep(0.5)  # Be respectful to API
    
    return all_results

def get_detailed_model_info(model_id: int) -> Optional[Dict]:
    """Get detailed information about a specific model."""
    try:
        response = requests.get(
            f"{BASE_URL}/models/{model_id}",
            headers=HEADERS,
            timeout=30,
        )
        
        if response.status_code != 200:
            return None
        
        return response.json()
    except Exception as e:
        print(f"Error getting model {model_id} details: {e}")
        return None

def check_model_for_target_files(model_data: Dict, target_patterns: List[str]) -> List[Dict]:
    """Check if a model contains files matching target patterns."""
    matches = []
    
    for version in model_data.get("modelVersions", []):
        for file_info in version.get("files", []):
            filename = file_info.get("name", "")
            
            for pattern in target_patterns:
                if pattern.lower() in filename.lower():
                    matches.append({
                        "filename": filename,
                        "model_name": model_data.get("name"),
                        "model_id": model_data.get("id"),
                        "version_name": version.get("name"),
                        "version_id": version.get("id"),
                        "download_url": f"https://civitai.com/api/download/models/{version.get('id')}",
                        "matched_pattern": pattern
                    })
    
    return matches

def main():
    print("Starting alternative search strategies for missing models...")
    print("=" * 80)
    
    # Define the target patterns from our missing models
    target_patterns = [
        # WAN-related
        "Wan2", "wan2", "WAN2", "WAN-2", "wan_2", "Wan2_1", "Wan2_2", 
        "wan2.1", "wan2.2", "Wan21", "Wan22", "WAN2.2", "WAN2.1",
        "i2v", "t2v", "I2V", "T2V", "I2v", "T2v",
        "high_noise", "low_noise", "highnoise", "lownoise",
        "umt5", "UMT5", "T5", "t5xxl", "umt5-xxl",
        
        # FLUX-related
        "FLUX", "flux", "Flux",
        
        # Upscaling
        "RealESRGAN", "realesrgan", "ESRGAN", "esrgan",
        
        # Other patterns
        "pony", "Pony", "bounce", "Bounce",
        "slop", "twerk", "slop_twerk",
        "cumshot", "cum", "pussy", "breast", "nipple"
    ]
    
    # Search for WAN models
    wan_results = search_for_wan_models()
    
    # Search for FLUX models  
    flux_results = search_for_flux_models()
    
    # Search for upscaling models
    upscale_results = search_for_upscale_models()
    
    print(f"\nCollected {len(wan_results)} WAN results, {len(flux_results)} FLUX results, {len(upscale_results)} upscale results")
    
    # Combine all results
    all_results = wan_results + flux_results + upscale_results
    unique_results = {}
    
    # Deduplicate by model ID
    for result in all_results:
        model_id = result['model_id']
        if model_id not in unique_results:
            unique_results[model_id] = result
    
    print(f"Found {len(unique_results)} unique model results to check")
    
    # Check each model for target files
    matches_found = []
    
    for i, (model_id, model_info) in enumerate(unique_results.items()):
        print(f"[{i+1}/{len(unique_results)}] Checking model: {model_info['model_name']} (ID: {model_id})")
        
        model_data = get_detailed_model_info(model_id)
        if model_data:
            matches = check_model_for_target_files(model_data, target_patterns)
            if matches:
                matches_found.extend(matches)
                for match in matches:
                    print(f"  ✓ Found: {match['filename']} (matches pattern '{match['matched_pattern']}')")
        
        time.sleep(0.5)  # Be respectful to API
    
    print("\n" + "=" * 80)
    print("ALTERNATIVE SEARCH COMPLETE")
    print("=" * 80)
    
    if matches_found:
        print(f"\n✅ FOUND {len(matches_found)} potential matches:")
        print("-" * 60)
        for match in matches_found:
            print(f"• File: {match['filename']}")
            print(f"  Model: {match['model_name']}")
            print(f"  Matched pattern: {match['matched_pattern']}")
            print(f"  Download: {match['download_url']}")
            print()
    else:
        print("\n❌ No specific matches found with alternative search strategies")
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"- WAN-related searches: {len(wan_results)} results")
    print(f"- FLUX-related searches: {len(flux_results)} results") 
    print(f"- Upscaling-related searches: {len(upscale_results)} results")
    print(f"- Total unique models checked: {len(unique_results)}")
    print(f"- Potential matches found: {len(matches_found)}")

if __name__ == "__main__":
    main()