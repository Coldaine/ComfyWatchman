#!/usr/bin/env python3
"""
Workflow Downloader for ComfyFixerSmart
Downloads workflows from Civitai, extracts them, and optionally scans for missing models

Usage:
  python download_workflow.py https://civitai.com/models/1772470?modelVersionId=2186422
  python download_workflow.py --no-scan https://civitai.com/models/1772470
  python download_workflow.py --auto-download https://civitai.com/models/1772470

Requirements:
- CIVITAI_API_KEY in ~/.secrets
- requests library: pip install requests
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

# Add ComfyFixerSmart source to path for validation utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from comfyfixersmart.utils import validate_civitai_response

# Configuration
COMFYUI_ROOT = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
WORKFLOW_DIR = f"{COMFYUI_ROOT}/user/default/workflows"
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = f"{LOG_DIR}/download_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


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


def parse_civitai_url(url):
    """
    Parse Civitai URL to extract model ID and optional version ID

    Supported formats:
    - https://civitai.com/models/1772470?modelVersionId=2186422
    - https://civitai.com/models/1772470
    - https://civitai.com/api/v1/models/1772470
    """
    log(f"Parsing URL: {url}")

    # Extract model ID from path
    model_match = re.search(r'/models/(\d+)', url)
    if not model_match:
        log("ERROR: Could not extract model ID from URL", "ERROR")
        return None, None

    model_id = model_match.group(1)

    # Extract version ID from query params
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    version_id = query_params.get('modelVersionId', [None])[0]

    log(f"  Model ID: {model_id}")
    log(f"  Version ID: {version_id if version_id else 'Latest'}")

    return model_id, version_id


def get_model_info(model_id):
    """Fetch model information from Civitai API with validation"""
    api_key = get_api_key()

    log(f"Fetching model info for ID: {model_id}")

    try:
        response = requests.get(
            f'https://civitai.com/api/v1/models/{model_id}',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=30
        )

        if response.status_code != 200:
            log(f"API error: {response.status_code}", "ERROR")
            return None

        data = response.json()

        # CRITICAL: Validate that API returned the correct model
        # See: docs/reports/civitai-api-wrong-metadata-incident.md
        validation = validate_civitai_response(
            data,
            requested_id=int(model_id),
            endpoint_type='model'
        )

        if not validation['valid']:
            log(f"API validation failed: {validation['error_message']}", "ERROR")
            log(f"  Requested model ID: {model_id}", "ERROR")
            log(f"  Returned model ID: {data.get('id', 'Unknown')}", "ERROR")
            log("This model may have been deleted or is restricted", "ERROR")
            return None

        log(f"  Model: {data.get('name', 'Unknown')}")
        log(f"  Type: {data.get('type', 'Unknown')}")
        log(f"  Versions: {len(data.get('modelVersions', []))}")

        return data

    except Exception as e:
        log(f"Error fetching model info: {e}", "ERROR")
        return None


def find_workflow_files(model_data, version_id=None):
    """
    Find workflow files in model data
    Returns list of (filename, download_url, version_name) tuples
    """
    log("Searching for workflow files...")

    workflows = []
    versions = model_data.get('modelVersions', [])

    # If version_id specified, filter to that version
    if version_id:
        versions = [v for v in versions if str(v['id']) == str(version_id)]
        if not versions:
            log(f"Version ID {version_id} not found", "ERROR")
            return []

    # Search through version files
    for version in versions:
        version_name = version.get('name', 'unknown')
        files = version.get('files', [])

        log(f"  Checking version: {version_name} ({len(files)} files)")

        for file in files:
            filename = file.get('name', '')
            file_type = file.get('type', '')

            # Look for JSON workflow files or ZIPs that might contain workflows
            if filename.endswith('.json') or filename.endswith('.zip'):
                download_url = file.get('downloadUrl', '')

                if download_url:
                    log(f"    Found: {filename} ({file_type})")
                    workflows.append((filename, download_url, version_name))

    log(f"Total workflow files found: {len(workflows)}")
    return workflows


def download_file(url, dest_path):
    """Download file from URL to destination path"""
    api_key = get_api_key()

    # Add API key to URL if not already present
    if 'token=' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}token={api_key}"

    log(f"Downloading: {os.path.basename(dest_path)}")

    try:
        response = requests.get(url, stream=True, timeout=60)

        if response.status_code != 200:
            log(f"Download failed: {response.status_code}", "ERROR")
            return False

        total_size = int(response.headers.get('content-length', 0))
        log(f"  Size: {total_size / (1024*1024):.2f} MB")

        with open(dest_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Progress update every 10MB
                    if downloaded % (10 * 1024 * 1024) < 8192:
                        progress = (downloaded / total_size * 100) if total_size else 0
                        log(f"  Progress: {progress:.1f}%")

        log(f"  Downloaded: {dest_path}")
        return True

    except Exception as e:
        log(f"Download error: {e}", "ERROR")
        return False


def is_valid_workflow(json_path):
    """Check if JSON file is a valid ComfyUI workflow"""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # ComfyUI workflows have 'nodes' and/or 'links' keys
        has_nodes = 'nodes' in data
        has_links = 'links' in data
        has_workflow = 'workflow' in data

        return has_nodes or has_links or has_workflow

    except Exception as e:
        log(f"  Invalid JSON: {e}", "ERROR")
        return False


def extract_workflows_from_zip(zip_path, extract_dir):
    """
    Extract ZIP file and return list of workflow JSON files
    """
    log(f"Extracting ZIP: {os.path.basename(zip_path)}")

    workflows = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            log(f"  Extracted to: {extract_dir}")

            # Find all JSON files
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.json'):
                        json_path = os.path.join(root, file)

                        # Validate it's a workflow
                        if is_valid_workflow(json_path):
                            log(f"    Found workflow: {file}")
                            workflows.append(json_path)

        return workflows

    except Exception as e:
        log(f"ZIP extraction error: {e}", "ERROR")
        return []


def install_workflow(workflow_path, version_name):
    """
    Copy workflow to ComfyUI workflows directory with unique name
    Returns the installed path
    """
    os.makedirs(WORKFLOW_DIR, exist_ok=True)

    # Generate unique filename
    original_name = Path(workflow_path).stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Sanitize version name
    safe_version = re.sub(r'[^\w\s-]', '', version_name).strip()
    safe_version = re.sub(r'[-\s]+', '_', safe_version)

    new_filename = f"{original_name}_{safe_version}_{timestamp}.json"
    dest_path = os.path.join(WORKFLOW_DIR, new_filename)

    log(f"Installing workflow: {new_filename}")

    try:
        shutil.copy2(workflow_path, dest_path)
        log(f"  Installed to: {dest_path}")
        return dest_path

    except Exception as e:
        log(f"Installation error: {e}", "ERROR")
        return None


def scan_workflow_for_missing_models(workflow_path):
    """
    Run comfy_fixer.py to scan for missing models
    """
    log(f"Scanning workflow for missing models...")

    try:
        # Run comfy_fixer.py
        result = subprocess.run(
            ['python3', 'comfy_fixer.py'],
            capture_output=True,
            text=True,
            timeout=300
        )

        log(f"Scanner output:")
        for line in result.stdout.split('\n'):
            if line.strip():
                log(f"  {line}")

        if result.returncode != 0:
            log(f"Scanner errors:", "ERROR")
            for line in result.stderr.split('\n'):
                if line.strip():
                    log(f"  {line}", "ERROR")

        return result.returncode == 0

    except Exception as e:
        log(f"Scanner error: {e}", "ERROR")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Download ComfyUI workflows from Civitai and scan for missing models'
    )
    parser.add_argument('url', help='Civitai model URL')
    parser.add_argument('--no-scan', action='store_true',
                        help='Skip scanning for missing models')
    parser.add_argument('--auto-download', action='store_true',
                        help='Automatically run download script for missing models')

    args = parser.parse_args()

    log("=" * 70)
    log("Workflow Downloader - Starting")
    log("=" * 70)

    # Parse URL
    model_id, version_id = parse_civitai_url(args.url)
    if not model_id:
        log("Failed to parse URL", "ERROR")
        sys.exit(1)

    # Get model info
    model_data = get_model_info(model_id)
    if not model_data:
        log("Failed to fetch model info", "ERROR")
        sys.exit(1)

    # Find workflow files
    workflow_files = find_workflow_files(model_data, version_id)
    if not workflow_files:
        log("No workflow files found in this model", "ERROR")
        log("This model may not contain workflows", "ERROR")
        sys.exit(1)

    # Download and install workflows
    installed_workflows = []

    with tempfile.TemporaryDirectory() as temp_dir:
        for filename, download_url, version_name in workflow_files:
            temp_path = os.path.join(temp_dir, filename)

            # Download
            if not download_file(download_url, temp_path):
                log(f"Skipping {filename} due to download error", "ERROR")
                continue

            # Handle based on file type
            if filename.endswith('.json'):
                # Direct JSON workflow
                if is_valid_workflow(temp_path):
                    installed = install_workflow(temp_path, version_name)
                    if installed:
                        installed_workflows.append(installed)
                else:
                    log(f"File {filename} is not a valid workflow", "ERROR")

            elif filename.endswith('.zip'):
                # Extract and find workflows
                extract_dir = os.path.join(temp_dir, 'extracted')
                os.makedirs(extract_dir, exist_ok=True)

                workflows = extract_workflows_from_zip(temp_path, extract_dir)
                for workflow_path in workflows:
                    installed = install_workflow(workflow_path, version_name)
                    if installed:
                        installed_workflows.append(installed)

    # Summary
    log("=" * 70)
    log("Download Complete")
    log("=" * 70)
    log(f"Installed workflows: {len(installed_workflows)}")
    for wf in installed_workflows:
        log(f"  - {os.path.basename(wf)}")

    # Scan for missing models
    if not args.no_scan and installed_workflows:
        log("")
        log("=" * 70)
        log("Scanning for Missing Models")
        log("=" * 70)

        scan_workflow_for_missing_models(installed_workflows[0])

        if args.auto_download:
            log("")
            log("Running auto-download...")

            download_script = "output/download_missing.sh"
            if os.path.exists(download_script):
                result = subprocess.run(['bash', download_script])
                if result.returncode == 0:
                    log("Auto-download complete")
                else:
                    log("Auto-download failed", "ERROR")
            else:
                log("No download script found", "ERROR")

    log("")
    log(f"Log file: {LOG_FILE}")
    log("=" * 70)


if __name__ == "__main__":
    main()
