#!/usr/bin/env python3
"""
Test PNG Workflow Extraction from Civitai Images

Tests whether Civitai preserves workflow metadata in PNG images.
Downloads sample images from a model's gallery and attempts to extract workflows.

Usage:
  python test_png_extraction.py 1952032  # Perfect Fingering model
  python test_png_extraction.py 1952032 --limit 20
  python test_png_extraction.py 1952032 --version-id 2209481
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image

# Add ComfyFixerSmart source to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from comfyfixersmart.utils import validate_civitai_response

# Configuration
OUTPUT_DIR = "output/png_test"
LOG_DIR = "log"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = f"{LOG_DIR}/png_extraction_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def log(msg, level="INFO"):
    """Log with timestamp to both console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {msg}"
    print(log_msg)

    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')


def get_api_key():
    """Get Civitai API key from environment"""
    key = os.getenv('CIVITAI_API_KEY')
    if not key:
        log("ERROR: CIVITAI_API_KEY not found. Set in ~/.secrets", "ERROR")
        sys.exit(1)
    return key


def get_images_for_model(model_id, version_id=None, limit=10):
    """
    Fetch image URLs from Civitai API

    Try multiple endpoints:
    1. /api/v1/images?modelId={id}
    2. /api/v1/images?modelVersionId={version_id}
    3. Fallback: Get model info and extract version IDs
    """
    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    images = []

    # Try 1: modelId parameter
    log(f"Trying /api/v1/images?modelId={model_id}")
    try:
        response = requests.get(
            f'https://civitai.com/api/v1/images',
            headers=headers,
            params={'modelId': model_id, 'limit': limit},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            images = data.get('items', [])
            if images:
                log(f"  ✅ Found {len(images)} images via modelId")
                return images
            else:
                log(f"  ⚠️ No images returned via modelId")
    except Exception as e:
        log(f"  ❌ Error with modelId query: {e}", "ERROR")

    # Try 2: modelVersionId parameter (if provided)
    if version_id:
        log(f"Trying /api/v1/images?modelVersionId={version_id}")
        try:
            response = requests.get(
                f'https://civitai.com/api/v1/images',
                headers=headers,
                params={'modelVersionId': version_id, 'limit': limit},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                images = data.get('items', [])
                if images:
                    log(f"  ✅ Found {len(images)} images via modelVersionId")
                    return images
                else:
                    log(f"  ⚠️ No images returned via modelVersionId")
        except Exception as e:
            log(f"  ❌ Error with modelVersionId query: {e}", "ERROR")

    # Try 3: Get model info and extract version IDs
    log(f"Trying to get model info for ID {model_id} to find versions")
    try:
        response = requests.get(
            f'https://civitai.com/api/v1/models/{model_id}',
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            model_data = response.json()

            # Validate response
            validation = validate_civitai_response(
                model_data,
                requested_id=int(model_id),
                endpoint_type='model'
            )

            if not validation['valid']:
                log(f"  ❌ Model validation failed: {validation['error_message']}", "ERROR")
                return []

            # Try each version
            versions = model_data.get('modelVersions', [])
            log(f"  Found {len(versions)} versions, trying each...")

            for version in versions[:3]:  # Try first 3 versions max
                vid = version['id']
                log(f"    Trying version {version.get('name', vid)} (ID: {vid})")

                response = requests.get(
                    f'https://civitai.com/api/v1/images',
                    headers=headers,
                    params={'modelVersionId': vid, 'limit': limit},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    images = data.get('items', [])
                    if images:
                        log(f"      ✅ Found {len(images)} images for version {vid}")
                        return images
        else:
            log(f"  ❌ Model info request failed: {response.status_code}", "ERROR")

    except Exception as e:
        log(f"  ❌ Error getting model info: {e}", "ERROR")

    return []


def download_png(url, dest_path):
    """Download PNG image from URL"""
    try:
        response = requests.get(url, stream=True, timeout=60)

        if response.status_code != 200:
            log(f"    ❌ Download failed: {response.status_code}", "ERROR")
            return False

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True

    except Exception as e:
        log(f"    ❌ Download error: {e}", "ERROR")
        return False


def extract_workflow_from_png(png_path):
    """
    Extract ComfyUI workflow from PNG metadata

    ComfyUI embeds workflows in PNG chunks with keys:
    - 'workflow' (JSON string or dict)
    - 'Workflow' (alternate capitalization)
    - 'prompt' (generation parameters)
    """
    try:
        img = Image.open(png_path)

        # Check for workflow in PNG info
        workflow_data = None

        if 'workflow' in img.info:
            workflow_data = img.info['workflow']
            log(f"      Found 'workflow' key")
        elif 'Workflow' in img.info:
            workflow_data = img.info['Workflow']
            log(f"      Found 'Workflow' key")

        if workflow_data:
            # Convert to dict if it's a JSON string
            if isinstance(workflow_data, str):
                workflow_data = json.loads(workflow_data)

            return workflow_data
        else:
            # Log all available PNG info keys for debugging
            available_keys = list(img.info.keys())
            log(f"      No workflow found. Available keys: {available_keys}")
            return None

    except Exception as e:
        log(f"      ❌ Extraction error: {e}", "ERROR")
        return None


def search_workflow_for_lora(workflow, lora_filename):
    """
    Search workflow JSON for specific LoRA filename
    Returns True if found
    """
    if not workflow:
        return False

    workflow_str = json.dumps(workflow).lower()
    lora_base = lora_filename.lower().replace('.safetensors', '')

    # Check for exact filename or base name
    if lora_filename.lower() in workflow_str or lora_base in workflow_str:
        return True

    return False


def main():
    parser = argparse.ArgumentParser(
        description='Test PNG workflow extraction from Civitai images'
    )
    parser.add_argument('model_id', type=int, help='Civitai model ID')
    parser.add_argument('--version-id', type=int, help='Specific version ID (optional)')
    parser.add_argument('--limit', type=int, default=10, help='Number of images to test (default: 10)')
    parser.add_argument('--search-lora', type=str, help='LoRA filename to search for in workflows')

    args = parser.parse_args()

    log("=" * 70)
    log("PNG Workflow Extraction Test - Starting")
    log("=" * 70)
    log(f"Model ID: {args.model_id}")
    log(f"Version ID: {args.version_id if args.version_id else 'Auto-detect'}")
    log(f"Image limit: {args.limit}")
    if args.search_lora:
        log(f"Searching for LoRA: {args.search_lora}")

    # Get images
    images = get_images_for_model(args.model_id, args.version_id, args.limit)

    if not images:
        log("❌ No images found. Cannot test extraction.", "ERROR")
        sys.exit(1)

    log("")
    log(f"Found {len(images)} images to test")
    log("=" * 70)

    # Test extraction on each image
    results = {
        'total': len(images),
        'downloaded': 0,
        'has_workflow': 0,
        'no_workflow': 0,
        'contains_lora': 0,
        'workflows': []
    }

    for i, image_data in enumerate(images, 1):
        image_id = image_data.get('id', 'unknown')
        image_url = image_data.get('url', '')

        log(f"\n[{i}/{len(images)}] Testing image {image_id}")
        log(f"  URL: {image_url}")

        if not image_url:
            log("  ⚠️ No URL found, skipping")
            continue

        # Download PNG
        png_filename = f"test_image_{image_id}.png"
        png_path = os.path.join(OUTPUT_DIR, png_filename)

        log(f"  Downloading...")
        if not download_png(image_url, png_path):
            continue

        results['downloaded'] += 1
        file_size = os.path.getsize(png_path) / (1024 * 1024)
        log(f"    ✅ Downloaded ({file_size:.2f} MB)")

        # Extract workflow
        log(f"  Extracting workflow metadata...")
        workflow = extract_workflow_from_png(png_path)

        if workflow:
            results['has_workflow'] += 1
            log(f"      ✅ Workflow extracted!")

            # Check structure
            has_nodes = 'nodes' in workflow
            has_links = 'links' in workflow
            node_count = len(workflow.get('nodes', []))

            log(f"      Nodes: {node_count}, Has links: {has_links}")

            # Save workflow
            workflow_filename = f"workflow_{image_id}.json"
            workflow_path = os.path.join(OUTPUT_DIR, workflow_filename)
            with open(workflow_path, 'w') as f:
                json.dump(workflow, f, indent=2)
            log(f"      Saved to: {workflow_path}")

            # Search for LoRA if specified
            if args.search_lora:
                if search_workflow_for_lora(workflow, args.search_lora):
                    results['contains_lora'] += 1
                    log(f"      🎯 FOUND LoRA: {args.search_lora}")
                    results['workflows'].append({
                        'image_id': image_id,
                        'image_url': image_url,
                        'workflow_path': workflow_path,
                        'contains_lora': True
                    })
                else:
                    log(f"      ⚠️ LoRA not found in workflow")
                    results['workflows'].append({
                        'image_id': image_id,
                        'image_url': image_url,
                        'workflow_path': workflow_path,
                        'contains_lora': False
                    })
        else:
            results['no_workflow'] += 1
            log(f"      ❌ No workflow metadata found")

    # Summary
    log("")
    log("=" * 70)
    log("Test Results Summary")
    log("=" * 70)
    log(f"Total images tested: {results['total']}")
    log(f"Successfully downloaded: {results['downloaded']}")
    log(f"Images with workflow: {results['has_workflow']}")
    log(f"Images without workflow: {results['no_workflow']}")

    if results['downloaded'] > 0:
        extraction_rate = (results['has_workflow'] / results['downloaded']) * 100
        log(f"Extraction success rate: {extraction_rate:.1f}%")

    if args.search_lora:
        log("")
        log(f"Workflows containing '{args.search_lora}': {results['contains_lora']}")
        if results['has_workflow'] > 0:
            lora_rate = (results['contains_lora'] / results['has_workflow']) * 100
            log(f"LoRA presence rate: {lora_rate:.1f}%")

    # Save full results
    results_file = os.path.join(OUTPUT_DIR, 'extraction_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    log("")
    log(f"Full results saved to: {results_file}")
    log(f"Log file: {LOG_FILE}")
    log("=" * 70)

    # Exit with appropriate code
    if results['has_workflow'] > 0:
        log("")
        log("✅ SUCCESS: PNG workflow extraction is VIABLE!")
        sys.exit(0)
    else:
        log("")
        log("❌ FAILURE: No workflows extracted. Hypothesis disproven.")
        sys.exit(1)


if __name__ == "__main__":
    main()
