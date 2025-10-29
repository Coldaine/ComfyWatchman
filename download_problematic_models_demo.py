#!/usr/bin/env python3
"""
Simple download demonstration for Civitai Advanced Search.

Shows how to download the problematic models using the enhanced Python functionality.
"""

import sys
import os
import requests
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, 'src')

# Set the API key from environment
os.environ['CIVITAI_API_KEY'] = os.environ.get('CIVITAI_API_KEY', '')

from comfyfixersmart.search import CivitaiSearch


def download_model_by_id(model_id: int, output_dir: str = "./downloads"):
    """
    Download a model by direct ID using the enhanced Civitai search.
    
    Args:
        model_id: Civitai model ID
        output_dir: Directory to save the downloaded model
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize search
    civitai_search = CivitaiSearch()
    
    # Find model via direct ID lookup
    print(f"🔍 Looking up model {model_id}...")
    result = civitai_search.search_by_id(model_id)
    
    if not result or result.status != 'FOUND':
        print(f"❌ Could not find model {model_id}")
        return False
    
    print(f"✅ Found model: {result.civitai_name}")
    print(f"📥 Download URL: {result.download_url}")
    
    # Extract filename from the result
    filename = result.filename or f"model_{model_id}.safetensors"
    output_path = Path(output_dir) / filename
    
    print(f"💾 Saving to: {output_path}")
    
    # Download with authorization header
    headers = {}
    if os.environ.get('CIVITAI_API_KEY'):
        headers['Authorization'] = f'Bearer {os.environ["CIVITAI_API_KEY"]}'
    
    try:
        print("⚡ Starting download...")
        response = requests.get(result.download_url, headers=headers, stream=True, timeout=300)
        response.raise_for_status()
        
        # Save file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = output_path.stat().st_size
        print(f"✅ Download completed: {file_size:,} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def main():
    """Main function to demonstrate downloading the problematic models."""
    print("=" * 60)
    print("CIVITAI ADVANCED SEARCH - DOWNLOAD DEMONSTRATION")
    print("=" * 60)
    print("This script demonstrates downloading the two previously")
    print("problematic models using direct ID lookup.")
    print()
    
    # The two problematic models that previously failed
    models_to_download = [
        {
            "id": 1091495,
            "name": "Better detailed pussy and anus v3.0"
        },
        {
            "id": 670378,
            "name": "Eyes High Definition V1"
        }
    ]
    
    success_count = 0
    
    for model in models_to_download:
        print(f"\n📦 Downloading: {model['name']} (ID: {model['id']})")
        print("-" * 50)
        
        if download_model_by_id(model['id']):
            success_count += 1
            print(f"✅ Successfully downloaded {model['name']}")
        else:
            print(f"❌ Failed to download {model['name']}")
    
    print("\n" + "=" * 60)
    print(f"📊 DOWNLOAD SUMMARY: {success_count}/{len(models_to_download)} models downloaded")
    if success_count == len(models_to_download):
        print("🎉 ALL DOWNLOADS COMPLETED SUCCESSFULLY!")
        print("The Civitai Advanced Search implementation successfully")
        print("downloads the two previously impossible models!")
    else:
        print("⚠️  Some downloads failed. Check the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()