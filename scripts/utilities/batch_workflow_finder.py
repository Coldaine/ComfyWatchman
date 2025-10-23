#!/usr/bin/env python3
"""
Batch Workflow Finder for ComfyFixerSmart

Automates finding workflows that use a specific LoRA by:
1. Searching Civitai for workflows via multiple strategies
2. Downloading and verifying workflow files
3. Checking if workflows actually contain the LoRA reference
4. Generating a comprehensive report

Usage:
  python batch_workflow_finder.py 1952032  # Perfect Fingering LoRA
  python batch_workflow_finder.py 1952032 --limit 20 --download-pngs
  python batch_workflow_finder.py 1952032 --creator-workflows --top-users

Requirements:
- CIVITAI_API_KEY in ~/.secrets
- requests, Pillow: pip install requests pillow
"""

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image

# Add ComfyFixerSmart source to path for utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from comfyfixersmart.utils import validate_civitai_response

# Configuration
OUTPUT_DIR = "output/workflow_finder"
LOG_DIR = "log"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = f"{LOG_DIR}/batch_workflow_finder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between API calls
REQUEST_TIMEOUT = 30  # seconds


class WorkflowFinderStats:
    """Statistics tracker for workflow search operations"""
    def __init__(self):
        self.api_calls = 0
        self.workflows_found = 0
        self.workflows_downloaded = 0
        self.workflows_with_lora = 0
        self.png_images_checked = 0
        self.png_with_workflow = 0
        self.errors = 0
        self.start_time = datetime.now()

    def summary(self) -> Dict:
        """Generate summary statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            'duration_seconds': elapsed,
            'api_calls': self.api_calls,
            'workflows_found': self.workflows_found,
            'workflows_downloaded': self.workflows_downloaded,
            'workflows_with_lora': self.workflows_with_lora,
            'png_images_checked': self.png_images_checked,
            'png_with_workflow': self.png_with_workflow,
            'errors': self.errors,
            'success_rate': (self.workflows_with_lora / self.workflows_found * 100) if self.workflows_found > 0 else 0
        }


def log(msg, level="INFO"):
    """Log with timestamp to both console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {msg}"
    print(log_msg)

    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')


def get_api_key() -> str:
    """Get Civitai API key from environment"""
    key = os.getenv('CIVITAI_API_KEY')
    if not key:
        log("ERROR: CIVITAI_API_KEY not found. Set in ~/.secrets", "ERROR")
        sys.exit(1)
    return key


def rate_limited_request(url: str, params: Optional[Dict] = None,
                        headers: Optional[Dict] = None, stats: Optional[WorkflowFinderStats] = None) -> requests.Response:
    """Make rate-limited API request with logging"""
    time.sleep(RATE_LIMIT_DELAY)

    if stats:
        stats.api_calls += 1

    log(f"API Request: {url}", "DEBUG")
    if params:
        log(f"  Params: {params}", "DEBUG")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        log(f"  Status: {response.status_code}", "DEBUG")
        return response
    except Exception as e:
        log(f"  Request failed: {e}", "ERROR")
        if stats:
            stats.errors += 1
        raise


def get_model_info(model_id: int, stats: Optional[WorkflowFinderStats] = None) -> Optional[Dict]:
    """
    Fetch model information from Civitai API with validation

    Returns model data including:
    - name, type, creator info
    - modelVersions with files and metadata
    """
    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    log(f"Fetching model info for ID: {model_id}")

    try:
        response = rate_limited_request(
            f'https://civitai.com/api/v1/models/{model_id}',
            headers=headers,
            stats=stats
        )

        if response.status_code != 200:
            log(f"API error: {response.status_code}", "ERROR")
            return None

        data = response.json()

        # CRITICAL: Validate response matches request
        validation = validate_civitai_response(
            data,
            requested_id=model_id,
            endpoint_type='model'
        )

        if not validation['valid']:
            log(f"API validation failed: {validation['error_message']}", "ERROR")
            log(f"  Requested model ID: {model_id}", "ERROR")
            log(f"  Returned model ID: {data.get('id', 'Unknown')}", "ERROR")
            return None

        log(f"  Model: {data.get('name', 'Unknown')}")
        log(f"  Type: {data.get('type', 'Unknown')}")
        log(f"  Creator: {data.get('creator', {}).get('username', 'Unknown')}")
        log(f"  Versions: {len(data.get('modelVersions', []))}")

        return data

    except Exception as e:
        log(f"Error fetching model info: {e}", "ERROR")
        if stats:
            stats.errors += 1
        return None


def get_lora_filenames(model_data: Dict) -> List[str]:
    """Extract all LoRA filenames from model versions"""
    filenames = []

    for version in model_data.get('modelVersions', []):
        for file in version.get('files', []):
            filename = file.get('name', '')
            if filename and (filename.endswith('.safetensors') or filename.endswith('.ckpt')):
                filenames.append(filename)

    return filenames


def search_workflow_models(tags: List[str], limit: int = 50,
                          stats: Optional[WorkflowFinderStats] = None) -> List[Dict]:
    """
    Search for workflow models on Civitai by tags/keywords

    Returns list of workflow model metadata
    """
    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    log(f"Searching for workflow models with tags: {tags}")

    params = {
        'types': 'Workflows',
        'tag': ','.join(tags),
        'limit': limit,
        'sort': 'Most Downloaded'
    }

    try:
        response = rate_limited_request(
            'https://civitai.com/api/v1/models',
            params=params,
            headers=headers,
            stats=stats
        )

        if response.status_code != 200:
            log(f"Workflow search failed: {response.status_code}", "ERROR")
            return []

        data = response.json()
        items = data.get('items', [])

        log(f"  Found {len(items)} workflow models")
        return items

    except Exception as e:
        log(f"Error searching workflows: {e}", "ERROR")
        if stats:
            stats.errors += 1
        return []


def get_creator_workflows(username: str, limit: int = 20,
                         stats: Optional[WorkflowFinderStats] = None) -> List[Dict]:
    """Get workflow models created by specific user"""
    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    log(f"Searching for workflows by creator: {username}")

    params = {
        'types': 'Workflows',
        'username': username,
        'limit': limit,
        'sort': 'Newest'
    }

    try:
        response = rate_limited_request(
            'https://civitai.com/api/v1/models',
            params=params,
            headers=headers,
            stats=stats
        )

        if response.status_code != 200:
            log(f"Creator search failed: {response.status_code}", "ERROR")
            return []

        data = response.json()
        items = data.get('items', [])

        log(f"  Found {len(items)} workflows by {username}")
        return items

    except Exception as e:
        log(f"Error searching creator workflows: {e}", "ERROR")
        if stats:
            stats.errors += 1
        return []


def get_images_for_model(model_id: int, version_id: Optional[int] = None,
                        limit: int = 20, stats: Optional[WorkflowFinderStats] = None) -> List[Dict]:
    """
    Fetch images from Civitai for a model

    Tries multiple endpoints to find images
    """
    api_key = get_api_key()
    headers = {'Authorization': f'Bearer {api_key}'}

    log(f"Fetching images for model {model_id}")

    # Try modelId parameter
    params = {'modelId': model_id, 'limit': limit}

    try:
        response = rate_limited_request(
            'https://civitai.com/api/v1/images',
            params=params,
            headers=headers,
            stats=stats
        )

        if response.status_code == 200:
            data = response.json()
            images = data.get('items', [])
            if images:
                log(f"  Found {len(images)} images")
                return images

        # Fallback: try version ID if provided
        if version_id:
            params = {'modelVersionId': version_id, 'limit': limit}
            response = rate_limited_request(
                'https://civitai.com/api/v1/images',
                params=params,
                headers=headers,
                stats=stats
            )

            if response.status_code == 200:
                data = response.json()
                images = data.get('items', [])
                if images:
                    log(f"  Found {len(images)} images via version")
                    return images

    except Exception as e:
        log(f"Error fetching images: {e}", "ERROR")
        if stats:
            stats.errors += 1

    return []


def download_png(url: str, dest_path: str) -> bool:
    """Download PNG image from URL"""
    try:
        response = requests.get(url, stream=True, timeout=60)

        if response.status_code != 200:
            log(f"    Download failed: {response.status_code}", "ERROR")
            return False

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True

    except Exception as e:
        log(f"    Download error: {e}", "ERROR")
        return False


def extract_workflow_from_png(png_path: str) -> Optional[Dict]:
    """
    Extract ComfyUI workflow from PNG metadata

    Returns workflow dict or None
    """
    try:
        img = Image.open(png_path)

        workflow_data = None

        if 'workflow' in img.info:
            workflow_data = img.info['workflow']
        elif 'Workflow' in img.info:
            workflow_data = img.info['Workflow']

        if workflow_data:
            if isinstance(workflow_data, str):
                workflow_data = json.loads(workflow_data)
            return workflow_data

    except Exception as e:
        log(f"      Extraction error: {e}", "ERROR")

    return None


def download_workflow_file(url: str, dest_path: str, api_key: str) -> bool:
    """Download workflow file (JSON or ZIP) from Civitai"""

    # Add API key to URL if not present
    if 'token=' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}token={api_key}"

    log(f"  Downloading: {os.path.basename(dest_path)}")

    try:
        response = requests.get(url, stream=True, timeout=60)

        if response.status_code != 200:
            log(f"    Download failed: {response.status_code}", "ERROR")
            return False

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        log(f"    Downloaded: {dest_path}")
        return True

    except Exception as e:
        log(f"    Download error: {e}", "ERROR")
        return False


def is_valid_workflow(workflow: Dict) -> bool:
    """Check if data is a valid ComfyUI workflow"""
    if not workflow or not isinstance(workflow, dict):
        return False

    has_nodes = 'nodes' in workflow
    has_links = 'links' in workflow
    has_workflow = 'workflow' in workflow

    return has_nodes or has_links or has_workflow


def search_workflow_for_lora(workflow: Dict, lora_filenames: List[str]) -> Tuple[bool, List[str]]:
    """
    Search workflow for any of the LoRA filenames

    Returns (found, matched_filenames)
    """
    if not workflow:
        return False, []

    workflow_str = json.dumps(workflow).lower()

    matched = []
    for filename in lora_filenames:
        # Check for exact filename or base name (without extension)
        base_name = filename.lower().replace('.safetensors', '').replace('.ckpt', '')

        if filename.lower() in workflow_str or base_name in workflow_str:
            matched.append(filename)

    return len(matched) > 0, matched


def extract_workflow_models(workflow: Dict) -> Dict[str, List[str]]:
    """
    Extract all model references from workflow

    Returns dict mapping model types to filenames
    """
    models = defaultdict(list)

    if not workflow:
        return models

    nodes = workflow.get('nodes', [])

    for node in nodes:
        node_type = node.get('type', '')

        # Map node types to categories
        category = None
        if 'Lora' in node_type:
            category = 'loras'
        elif 'Checkpoint' in node_type:
            category = 'checkpoints'
        elif 'VAE' in node_type:
            category = 'vae'
        elif 'ControlNet' in node_type:
            category = 'controlnet'
        elif 'Upscale' in node_type:
            category = 'upscale_models'

        if category:
            for value in node.get('widgets_values', []):
                if isinstance(value, str) and any(ext in value for ext in ['.safetensors', '.ckpt', '.pt', '.bin']):
                    models[category].append(os.path.basename(value))

    return dict(models)


def process_workflow_model(model_data: Dict, lora_filenames: List[str],
                          output_dir: str, api_key: str, stats: WorkflowFinderStats) -> List[Dict]:
    """
    Process a workflow model and extract workflows that contain the LoRA

    Returns list of workflow findings
    """
    findings = []

    model_id = model_data.get('id')
    model_name = model_data.get('name', 'Unknown')

    log(f"  Processing workflow model: {model_name} (ID: {model_id})")

    for version in model_data.get('modelVersions', []):
        version_id = version.get('id')
        version_name = version.get('name', 'unknown')

        for file in version.get('files', []):
            filename = file.get('name', '')

            if not filename.endswith('.json'):
                continue

            download_url = file.get('downloadUrl', '')
            if not download_url:
                continue

            stats.workflows_found += 1

            # Download workflow
            local_filename = f"workflow_{model_id}_{version_id}_{filename}"
            local_path = os.path.join(output_dir, local_filename)

            if download_workflow_file(download_url, local_path, api_key):
                stats.workflows_downloaded += 1

                # Load and check workflow
                try:
                    with open(local_path, 'r') as f:
                        workflow = json.load(f)

                    if is_valid_workflow(workflow):
                        found, matched = search_workflow_for_lora(workflow, lora_filenames)

                        if found:
                            stats.workflows_with_lora += 1
                            log(f"    ✅ FOUND LoRA in workflow: {matched}", "SUCCESS")

                            # Extract all models from workflow
                            all_models = extract_workflow_models(workflow)

                            findings.append({
                                'model_id': model_id,
                                'model_name': model_name,
                                'version_id': version_id,
                                'version_name': version_name,
                                'workflow_file': local_path,
                                'download_url': download_url,
                                'matched_loras': matched,
                                'all_models': all_models,
                                'source': 'workflow_model'
                            })
                        else:
                            log(f"    ⚠️ LoRA not found in workflow")

                except Exception as e:
                    log(f"    Error processing workflow: {e}", "ERROR")
                    stats.errors += 1

    return findings


def process_png_images(images: List[Dict], lora_filenames: List[str],
                       output_dir: str, stats: WorkflowFinderStats) -> List[Dict]:
    """
    Process PNG images and extract workflows

    Returns list of workflow findings from PNGs
    """
    findings = []

    for image_data in images:
        image_id = image_data.get('id', 'unknown')
        image_url = image_data.get('url', '')

        if not image_url:
            continue

        stats.png_images_checked += 1

        # Download PNG
        png_filename = f"image_{image_id}.png"
        png_path = os.path.join(output_dir, png_filename)

        if download_png(image_url, png_path):
            # Extract workflow
            workflow = extract_workflow_from_png(png_path)

            if workflow and is_valid_workflow(workflow):
                stats.png_with_workflow += 1

                found, matched = search_workflow_for_lora(workflow, lora_filenames)

                if found:
                    stats.workflows_with_lora += 1
                    log(f"    ✅ FOUND LoRA in PNG workflow: {matched}", "SUCCESS")

                    # Save extracted workflow
                    workflow_filename = f"workflow_from_png_{image_id}.json"
                    workflow_path = os.path.join(output_dir, workflow_filename)
                    with open(workflow_path, 'w') as f:
                        json.dump(workflow, f, indent=2)

                    # Extract all models
                    all_models = extract_workflow_models(workflow)

                    findings.append({
                        'image_id': image_id,
                        'image_url': image_url,
                        'workflow_file': workflow_path,
                        'matched_loras': matched,
                        'all_models': all_models,
                        'source': 'png_metadata'
                    })

                # Clean up PNG after extraction
                os.remove(png_path)

    return findings


def generate_report(lora_model_data: Dict, all_findings: List[Dict],
                   stats: WorkflowFinderStats, output_dir: str):
    """Generate comprehensive report of findings"""

    report = {
        'lora_model': {
            'id': lora_model_data.get('id'),
            'name': lora_model_data.get('name'),
            'creator': lora_model_data.get('creator', {}).get('username'),
            'type': lora_model_data.get('type'),
        },
        'statistics': stats.summary(),
        'findings': all_findings,
        'timestamp': datetime.now().isoformat()
    }

    # Save JSON report
    report_file = os.path.join(output_dir, 'workflow_finder_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Generate human-readable summary
    summary_file = os.path.join(output_dir, 'workflow_finder_summary.txt')
    with open(summary_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Batch Workflow Finder - Report Summary\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"LoRA Model: {report['lora_model']['name']} (ID: {report['lora_model']['id']})\n")
        f.write(f"Creator: {report['lora_model']['creator']}\n\n")

        f.write("Statistics:\n")
        f.write(f"  Duration: {stats.summary()['duration_seconds']:.1f} seconds\n")
        f.write(f"  API Calls: {stats.api_calls}\n")
        f.write(f"  Workflows Found: {stats.workflows_found}\n")
        f.write(f"  Workflows Downloaded: {stats.workflows_downloaded}\n")
        f.write(f"  Workflows with LoRA: {stats.workflows_with_lora}\n")
        f.write(f"  PNG Images Checked: {stats.png_images_checked}\n")
        f.write(f"  PNG with Workflow: {stats.png_with_workflow}\n")
        f.write(f"  Errors: {stats.errors}\n")
        f.write(f"  Success Rate: {stats.summary()['success_rate']:.1f}%\n\n")

        f.write("=" * 70 + "\n")
        f.write(f"Found {len(all_findings)} Workflows Containing LoRA\n")
        f.write("=" * 70 + "\n\n")

        for i, finding in enumerate(all_findings, 1):
            f.write(f"[{i}] ")

            if finding['source'] == 'workflow_model':
                f.write(f"{finding['model_name']} (v{finding['version_name']})\n")
                f.write(f"    Model ID: {finding['model_id']}\n")
            else:
                f.write(f"PNG Image (ID: {finding['image_id']})\n")
                f.write(f"    URL: {finding['image_url']}\n")

            f.write(f"    Matched LoRAs: {', '.join(finding['matched_loras'])}\n")
            f.write(f"    Workflow File: {finding['workflow_file']}\n")

            if finding['all_models']:
                f.write(f"    Other Models Used:\n")
                for model_type, filenames in finding['all_models'].items():
                    if filenames:
                        f.write(f"      {model_type}: {', '.join(filenames)}\n")

            f.write("\n")

    log(f"\n📊 Report saved to:")
    log(f"  JSON: {report_file}")
    log(f"  Summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Batch search for workflows using a specific LoRA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python batch_workflow_finder.py 1952032

  # Extended search with more strategies
  python batch_workflow_finder.py 1952032 --limit 50 --creator-workflows --download-pngs

  # Search by version ID
  python batch_workflow_finder.py 1952032 --version-id 2209481
        """
    )

    parser.add_argument('model_id', type=int, help='Civitai LoRA model ID')
    parser.add_argument('--version-id', type=int, help='Specific version ID (optional)')
    parser.add_argument('--limit', type=int, default=20,
                       help='Limit per search strategy (default: 20)')
    parser.add_argument('--creator-workflows', action='store_true',
                       help='Search for workflows by the LoRA creator')
    parser.add_argument('--download-pngs', action='store_true',
                       help='Download and extract workflows from PNG images')
    parser.add_argument('--tags', type=str,
                       help='Comma-separated tags for workflow search (e.g., "pony,sdxl")')

    args = parser.parse_args()

    stats = WorkflowFinderStats()

    log("=" * 70)
    log("Batch Workflow Finder - Starting")
    log("=" * 70)
    log(f"LoRA Model ID: {args.model_id}")
    log(f"Search limit: {args.limit}")
    log(f"Creator workflows: {args.creator_workflows}")
    log(f"PNG extraction: {args.download_pngs}")

    # Get LoRA model information
    lora_model = get_model_info(args.model_id, stats)
    if not lora_model:
        log("Failed to fetch LoRA model info", "ERROR")
        sys.exit(1)

    # Extract LoRA filenames to search for
    lora_filenames = get_lora_filenames(lora_model)
    if not lora_filenames:
        log("No LoRA files found in model", "ERROR")
        sys.exit(1)

    log(f"\nLoRA filenames to search for: {lora_filenames}")

    # Create output directory for this search
    run_dir = os.path.join(OUTPUT_DIR, f"run_{args.model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(run_dir, exist_ok=True)
    log(f"Output directory: {run_dir}\n")

    api_key = get_api_key()
    all_findings = []

    # Strategy 1: Search workflow models by tags
    if args.tags:
        log("=" * 70)
        log("Strategy 1: Search workflow models by tags")
        log("=" * 70)

        tags = [t.strip() for t in args.tags.split(',')]
        workflow_models = search_workflow_models(tags, args.limit, stats)

        for model in workflow_models:
            findings = process_workflow_model(model, lora_filenames, run_dir, api_key, stats)
            all_findings.extend(findings)

    # Strategy 2: Creator's workflow models
    if args.creator_workflows:
        log("\n" + "=" * 70)
        log("Strategy 2: Creator's workflow models")
        log("=" * 70)

        creator_username = lora_model.get('creator', {}).get('username')
        if creator_username:
            creator_workflows = get_creator_workflows(creator_username, args.limit, stats)

            for model in creator_workflows:
                findings = process_workflow_model(model, lora_filenames, run_dir, api_key, stats)
                all_findings.extend(findings)
        else:
            log("Creator username not available", "WARN")

    # Strategy 3: PNG images with workflow metadata
    if args.download_pngs:
        log("\n" + "=" * 70)
        log("Strategy 3: PNG images with workflow metadata")
        log("=" * 70)

        images = get_images_for_model(args.model_id, args.version_id, args.limit, stats)

        if images:
            findings = process_png_images(images, lora_filenames, run_dir, stats)
            all_findings.extend(findings)
        else:
            log("No images found for this model", "WARN")

    # Generate report
    log("\n" + "=" * 70)
    log("Generating Report")
    log("=" * 70)

    generate_report(lora_model, all_findings, stats, run_dir)

    # Final summary
    log("\n" + "=" * 70)
    log("Batch Workflow Finder - Complete")
    log("=" * 70)

    summary = stats.summary()
    log(f"Duration: {summary['duration_seconds']:.1f} seconds")
    log(f"API Calls: {summary['api_calls']}")
    log(f"Workflows Found: {stats.workflows_found}")
    log(f"Workflows with LoRA: {stats.workflows_with_lora}")
    log(f"Success Rate: {summary['success_rate']:.1f}%")
    log(f"\nResults saved to: {run_dir}")
    log(f"Log file: {LOG_FILE}")
    log("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if stats.workflows_with_lora > 0 else 1)


if __name__ == "__main__":
    main()
