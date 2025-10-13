# ComfyFixerSmart - Right-Sized Implementation Plan

**Purpose:** Scan workflows, find missing models/nodes, search and download from Civitai/HuggingFace

**Date:** 2025-10-12

---

## Exact Requirements

Based on your clarified request:

1. ✅ **Scan all workflows** - Find all .json workflow files
2. ✅ **Determine missing models and nodes** - Compare against local inventory
3. ✅ **Search for them** - Query Civitai API and HuggingFace
4. ✅ **Download them** - Use Civitai API or `hf download` CLI
5. ✅ **Log all actions** - Structured logs to `/log` folder
6. ✅ **Status reporting** - Live status file for agents to query
7. ✅ **Agent instructions** - Clear documentation for agent usage

---

## Architecture (Right-Sized)

### Module Structure

```
ComfyFixerSmart/
├── comfy_fixer.py              # Main CLI entry point (orchestrator)
├── workflow_scanner.py         # Scan workflows, extract model references
├── inventory.py                # Check what models/nodes exist locally
├── resolver.py                 # Search Civitai + HuggingFace APIs
├── downloader.py               # Download from both sources
├── logger_setup.py             # Logging configuration
│
├── status.json                 # Live status (updated in real-time)
├── config.json                 # Configuration (paths, API keys)
│
├── log/                        # All execution logs
│   ├── scan_YYYYMMDD_HHMMSS.log
│   ├── resolve_YYYYMMDD_HHMMSS.log
│   └── download_YYYYMMDD_HHMMSS.log
│
├── output/                     # Generated reports
│   ├── missing_models.json
│   ├── missing_nodes.json
│   └── summary_report.md
│
├── AGENT_GUIDE.md             # Instructions for agents
└── README.md                  # User documentation
```

**4 core modules + orchestrator + logging = Right balance**

---

## Module Details

### 1. Main Orchestrator (`comfy_fixer.py`)

**Purpose:** CLI entry point, coordinates all operations

**Commands:**
```bash
# Full workflow (scan → resolve → download)
python comfy_fixer.py --auto

# Individual steps
python comfy_fixer.py --scan
python comfy_fixer.py --resolve
python comfy_fixer.py --download

# Status query (for agents)
python comfy_fixer.py --status

# Resume from last run
python comfy_fixer.py --resume
```

**Key Functions:**
```python
def main():
    """Main orchestrator"""
    parser = argparse.ArgumentParser(description="ComfyUI Workflow Dependency Resolver")
    parser.add_argument('--auto', action='store_true', help='Run full pipeline')
    parser.add_argument('--scan', action='store_true', help='Scan workflows only')
    parser.add_argument('--resolve', action='store_true', help='Resolve missing items')
    parser.add_argument('--download', action='store_true', help='Download resolved items')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--resume', action='store_true', help='Resume from last state')
    args = parser.parse_args()

    # Update status: started
    update_status("started", "Initializing ComfyFixerSmart")

    if args.scan or args.auto:
        scan_phase()

    if args.resolve or args.auto:
        resolve_phase()

    if args.download or args.auto:
        download_phase()

    if args.status:
        show_status()

def scan_phase():
    """Phase 1: Scan workflows and inventory"""
    logger.info("=== SCAN PHASE ===")
    update_status("scanning", "Scanning workflows and local inventory")

    # Scan workflows
    from workflow_scanner import scan_all_workflows
    workflow_results = scan_all_workflows(config['workflow_directories'])
    logger.info(f"Found {len(workflow_results)} workflows")

    # Build inventory
    from inventory import build_inventory
    local_inventory = build_inventory(config['comfyui_root'])
    logger.info(f"Indexed {len(local_inventory['models'])} local models")

    # Identify missing
    missing_models = identify_missing_models(workflow_results, local_inventory)
    missing_nodes = identify_missing_nodes(workflow_results, local_inventory)

    # Save results
    save_json('output/missing_models.json', missing_models)
    save_json('output/missing_nodes.json', missing_nodes)

    logger.info(f"Missing models: {len(missing_models)}")
    logger.info(f"Missing custom nodes: {len(missing_nodes)}")

    update_status("scan_complete", {
        "workflows_scanned": len(workflow_results),
        "missing_models": len(missing_models),
        "missing_nodes": len(missing_nodes)
    })

def resolve_phase():
    """Phase 2: Search Civitai and HuggingFace"""
    logger.info("=== RESOLVE PHASE ===")
    update_status("resolving", "Searching Civitai and HuggingFace")

    from resolver import resolve_missing_items

    missing_models = load_json('output/missing_models.json')
    resolutions = resolve_missing_items(missing_models)

    save_json('output/resolutions.json', resolutions)

    civitai_count = sum(1 for r in resolutions if r['source'] == 'civitai')
    hf_count = sum(1 for r in resolutions if r['source'] == 'huggingface')
    unresolved_count = sum(1 for r in resolutions if r['source'] == 'not_found')

    logger.info(f"Resolved on Civitai: {civitai_count}")
    logger.info(f"Resolved on HuggingFace: {hf_count}")
    logger.info(f"Unresolved: {unresolved_count}")

    update_status("resolve_complete", {
        "civitai_matches": civitai_count,
        "huggingface_matches": hf_count,
        "unresolved": unresolved_count
    })

def download_phase():
    """Phase 3: Download all resolved items"""
    logger.info("=== DOWNLOAD PHASE ===")
    update_status("downloading", "Downloading models")

    from downloader import download_all

    resolutions = load_json('output/resolutions.json')
    results = download_all(resolutions)

    success_count = sum(1 for r in results if r['success'])
    failed_count = len(results) - success_count

    logger.info(f"Downloaded: {success_count}/{len(results)}")
    logger.info(f"Failed: {failed_count}")

    update_status("complete", {
        "downloads_successful": success_count,
        "downloads_failed": failed_count
    })
```

**Status Updates:**
```python
def update_status(phase: str, data: dict):
    """Update status.json for agent monitoring"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "phase": phase,  # started, scanning, resolving, downloading, complete, error
        "data": data
    }

    with open('status.json', 'w') as f:
        json.dump(status, f, indent=2)
```

---

### 2. Workflow Scanner (`workflow_scanner.py`)

**Purpose:** Find and parse all workflows, extract model/node references

**Key Functions:**
```python
def scan_all_workflows(directories: list) -> list:
    """Scan all workflow directories for .json files"""
    logger = logging.getLogger(__name__)
    workflows = []

    for directory in directories:
        logger.info(f"Scanning directory: {directory}")

        # Find all .json files
        for json_file in Path(directory).rglob('*.json'):
            logger.debug(f"Processing: {json_file}")

            try:
                workflow_data = parse_workflow(json_file)
                workflows.append(workflow_data)
                logger.info(f"✓ Parsed: {json_file.name} ({len(workflow_data['models'])} models)")
            except Exception as e:
                logger.error(f"✗ Failed to parse {json_file}: {e}")

    return workflows


def parse_workflow(workflow_path: Path) -> dict:
    """Parse a single workflow and extract all dependencies"""
    with open(workflow_path) as f:
        data = json.load(f)

    models = extract_model_references(data)
    nodes = extract_node_types(data)

    return {
        'path': str(workflow_path),
        'name': workflow_path.name,
        'models': models,  # List of {filename, type, node_type, node_id}
        'custom_nodes': nodes  # List of node type strings
    }


def extract_model_references(workflow_data: dict) -> list:
    """Extract all model file references from workflow"""
    models = []

    for node in workflow_data.get('nodes', []):
        node_type = node.get('type')
        node_id = node.get('id')

        # Check widgets_values for model filenames
        for value in node.get('widgets_values', []):
            if isinstance(value, str) and is_model_filename(value):
                models.append({
                    'filename': os.path.basename(value),
                    'expected_type': node_type_to_model_type(node_type),
                    'node_type': node_type,
                    'node_id': node_id
                })

    return models


def is_model_filename(value: str) -> bool:
    """Check if string looks like a model filename"""
    extensions = ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']
    return any(value.endswith(ext) for ext in extensions)


def node_type_to_model_type(node_type: str) -> str:
    """Map ComfyUI node type to model type"""
    mapping = {
        'CheckpointLoaderSimple': 'checkpoint',
        'CheckpointLoader': 'checkpoint',
        'LoraLoader': 'lora',
        'LoraLoaderModelOnly': 'lora',
        'VAELoader': 'vae',
        'ControlNetLoader': 'controlnet',
        'UpscaleModelLoader': 'upscale_models',
        'CLIPVisionLoader': 'clip_vision',
        'CLIPLoader': 'clip',
        'DualCLIPLoader': 'clip',
        'UNETLoader': 'unet',
    }
    return mapping.get(node_type, 'unknown')


def extract_node_types(workflow_data: dict) -> list:
    """Extract all unique custom node types"""
    node_types = set()

    for node in workflow_data.get('nodes', []):
        node_type = node.get('type')
        if node_type:
            node_types.add(node_type)

    return list(node_types)
```

**Reuses:** Patterns from your `ScanTool/workflow_validator.py`

---

### 3. Inventory Builder (`inventory.py`)

**Purpose:** Scan local ComfyUI installation, track what exists

**Key Functions:**
```python
def build_inventory(comfyui_root: str) -> dict:
    """Build complete inventory of local models and nodes"""
    logger = logging.getLogger(__name__)
    logger.info("Building local inventory")

    inventory = {
        'models': {},  # filename -> {path, type, size}
        'custom_nodes': set(),  # installed node types
        'scan_time': datetime.now().isoformat()
    }

    # Scan models directory
    models_dir = Path(comfyui_root) / 'models'
    inventory['models'] = scan_models_directory(models_dir)

    # Scan custom_nodes directory
    nodes_dir = Path(comfyui_root) / 'custom_nodes'
    inventory['custom_nodes'] = scan_custom_nodes(nodes_dir)

    logger.info(f"Inventory complete: {len(inventory['models'])} models, {len(inventory['custom_nodes'])} node types")

    return inventory


def scan_models_directory(models_dir: Path) -> dict:
    """Recursively scan models directory"""
    logger = logging.getLogger(__name__)
    models = {}

    for model_file in models_dir.rglob('*'):
        if model_file.is_file() and is_model_file(model_file):
            filename = model_file.name

            # Get relative path to determine type
            rel_path = model_file.relative_to(models_dir)
            model_type = rel_path.parts[0] if rel_path.parts else 'unknown'

            models[filename] = {
                'path': str(model_file),
                'type': model_type,
                'size_mb': model_file.stat().st_size / (1024 * 1024)
            }

            logger.debug(f"Found: {filename} ({model_type})")

    return models


def is_model_file(path: Path) -> bool:
    """Check if file is a model file"""
    extensions = {'.safetensors', '.ckpt', '.pt', '.bin', '.pth'}
    return path.suffix in extensions


def scan_custom_nodes(nodes_dir: Path) -> set:
    """Scan installed custom nodes and extract node types"""
    logger = logging.getLogger(__name__)
    node_types = set()

    # Look for __init__.py or similar in each custom node directory
    for node_pkg in nodes_dir.iterdir():
        if node_pkg.is_dir() and not node_pkg.name.startswith('.'):
            # Try to find NODE_CLASS_MAPPINGS
            init_file = node_pkg / '__init__.py'
            if init_file.exists():
                try:
                    # Extract node type names (simple regex approach)
                    content = init_file.read_text()
                    if 'NODE_CLASS_MAPPINGS' in content:
                        # This package provides custom nodes
                        # Parse the mapping to get node types
                        types = extract_node_types_from_init(content)
                        node_types.update(types)
                        logger.debug(f"Package {node_pkg.name}: {len(types)} node types")
                except Exception as e:
                    logger.warning(f"Could not parse {init_file}: {e}")

    return node_types


def extract_node_types_from_init(content: str) -> list:
    """Extract node class names from NODE_CLASS_MAPPINGS"""
    # Simple regex to find dictionary keys in NODE_CLASS_MAPPINGS
    import re
    pattern = r'NODE_CLASS_MAPPINGS\s*=\s*\{([^}]+)\}'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        mapping_content = match.group(1)
        # Extract quoted strings (node type names)
        keys = re.findall(r'["\']([^"\']+)["\']', mapping_content)
        return keys

    return []


def identify_missing_models(workflows: list, inventory: dict) -> list:
    """Find models referenced in workflows but not in inventory"""
    logger = logging.getLogger(__name__)
    missing = []

    local_models = set(inventory['models'].keys())

    for workflow in workflows:
        for model in workflow['models']:
            filename = model['filename']

            if filename not in local_models:
                missing.append({
                    'filename': filename,
                    'expected_type': model['expected_type'],
                    'workflow': workflow['name'],
                    'node_type': model['node_type'],
                    'node_id': model['node_id']
                })
                logger.info(f"Missing: {filename} (from {workflow['name']})")

    # Deduplicate by filename
    seen = set()
    unique_missing = []
    for item in missing:
        if item['filename'] not in seen:
            unique_missing.append(item)
            seen.add(item['filename'])

    return unique_missing


def identify_missing_nodes(workflows: list, inventory: dict) -> list:
    """Find custom nodes used in workflows but not installed"""
    logger = logging.getLogger(__name__)
    missing = []

    installed_nodes = inventory['custom_nodes']

    all_used_nodes = set()
    for workflow in workflows:
        all_used_nodes.update(workflow['custom_nodes'])

    for node_type in all_used_nodes:
        if node_type not in installed_nodes:
            # Skip built-in ComfyUI nodes
            if not is_builtin_node(node_type):
                missing.append({
                    'node_type': node_type,
                    'workflows': [w['name'] for w in workflows if node_type in w['custom_nodes']]
                })
                logger.info(f"Missing custom node: {node_type}")

    return missing


def is_builtin_node(node_type: str) -> bool:
    """Check if node type is built-in to ComfyUI"""
    builtins = {
        'KSampler', 'CLIPTextEncode', 'VAEDecode', 'VAEEncode',
        'CheckpointLoaderSimple', 'LoraLoader', 'VAELoader',
        'EmptyLatentImage', 'SaveImage', 'LoadImage', 'PreviewImage',
        'ControlNetLoader', 'ControlNetApply',
        # Add more as needed
    }
    return node_type in builtins
```

**Reuses:** Your `ScanTool/comfyui_model_scanner.py` patterns

---

### 4. Resolver (`resolver.py`)

**Purpose:** Search Civitai and HuggingFace for missing items

**Key Functions:**
```python
def resolve_missing_items(missing_models: list) -> list:
    """Search for each missing model on Civitai and HuggingFace"""
    logger = logging.getLogger(__name__)
    resolutions = []

    for missing in missing_models:
        logger.info(f"Resolving: {missing['filename']}")

        # Try Civitai first
        civitai_result = search_civitai(missing)
        if civitai_result:
            resolutions.append(civitai_result)
            logger.info(f"  ✓ Found on Civitai: {civitai_result['model_id']}")
            continue

        # Try HuggingFace
        hf_result = search_huggingface(missing)
        if hf_result:
            resolutions.append(hf_result)
            logger.info(f"  ✓ Found on HuggingFace: {hf_result['repo_id']}")
            continue

        # Not found
        resolutions.append({
            'filename': missing['filename'],
            'source': 'not_found',
            'missing_data': missing
        })
        logger.warning(f"  ✗ Not found: {missing['filename']}")

    return resolutions


def search_civitai(missing: dict) -> dict:
    """Search Civitai API for a model"""
    logger = logging.getLogger(__name__)

    # Clean filename for search
    query = clean_filename_for_search(missing['filename'])
    model_type = missing['expected_type']

    # Map to Civitai types
    civitai_type = {
        'checkpoint': 'Checkpoint',
        'lora': 'LORA',
        'vae': 'VAE',
        'controlnet': 'Controlnet',
        'upscale_models': 'Upscaler',
    }.get(model_type, 'Checkpoint')

    try:
        # Call Civitai API
        response = requests.get(
            'https://civitai.com/api/v1/models',
            params={
                'query': query,
                'types': civitai_type,
                'limit': 5,
                'sort': 'Highest Rated'
            },
            headers={'Authorization': f'Bearer {os.getenv("CIVITAI_API_KEY")}'},
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Civitai API error: {response.status_code}")
            return None

        results = response.json().get('items', [])
        if not results:
            return None

        # Find best match using fuzzy matching
        best_match = find_best_match(missing['filename'], results)
        if not best_match:
            return None

        # Get download info
        version = best_match['modelVersions'][0]  # Latest version

        return {
            'filename': missing['filename'],
            'source': 'civitai',
            'model_id': best_match['id'],
            'model_name': best_match['name'],
            'version_id': version['id'],
            'version_name': version['name'],
            'download_url': f"https://civitai.com/api/download/models/{version['id']}",
            'expected_type': missing['expected_type']
        }

    except Exception as e:
        logger.error(f"Error searching Civitai: {e}")
        return None


def search_huggingface(missing: dict) -> dict:
    """Search HuggingFace for a model"""
    logger = logging.getLogger(__name__)

    query = clean_filename_for_search(missing['filename'])

    try:
        # Use HuggingFace Hub API
        from huggingface_hub import HfApi
        api = HfApi()

        # Search for models
        models = api.list_models(
            search=query,
            limit=10,
            sort="downloads",
            direction=-1
        )

        models_list = list(models)
        if not models_list:
            return None

        # Find best match
        best_match = None
        for model in models_list:
            if fuzzy_match_score(query, model.modelId) > 0.7:
                best_match = model
                break

        if not best_match:
            best_match = models_list[0]  # Take most popular

        return {
            'filename': missing['filename'],
            'source': 'huggingface',
            'repo_id': best_match.modelId,
            'expected_type': missing['expected_type']
        }

    except Exception as e:
        logger.error(f"Error searching HuggingFace: {e}")
        return None


def clean_filename_for_search(filename: str) -> str:
    """Clean filename for better search results"""
    # Remove extension
    query = filename.replace('.safetensors', '').replace('.ckpt', '').replace('.pt', '')

    # Replace underscores with spaces
    query = query.replace('_', ' ')

    # Remove version numbers
    import re
    query = re.sub(r'[vV]\d+', '', query)
    query = re.sub(r'\d+\.\d+', '', query)

    return query.strip()


def find_best_match(filename: str, results: list) -> dict:
    """Find best matching result using fuzzy matching"""
    from fuzzywuzzy import fuzz

    best_score = 0
    best_result = None

    for result in results:
        # Compare against model name
        score = fuzz.token_sort_ratio(filename.lower(), result['name'].lower())

        if score > best_score:
            best_score = score
            best_result = result

    # Only return if confidence is reasonable
    if best_score > 60:
        return best_result

    return None


def fuzzy_match_score(query: str, target: str) -> float:
    """Calculate fuzzy match score (0-1)"""
    from fuzzywuzzy import fuzz
    return fuzz.token_sort_ratio(query.lower(), target.lower()) / 100.0
```

**Dependencies:**
- `requests` - for Civitai API
- `huggingface_hub` - for HuggingFace API
- `fuzzywuzzy` - for fuzzy matching

**Reuses:** Your Civitai API patterns from `civitai_api_research.md` and `civitai-toolkit`

---

### 5. Downloader (`downloader.py`)

**Purpose:** Download models from Civitai or HuggingFace

**Key Functions:**
```python
def download_all(resolutions: list) -> list:
    """Download all resolved models"""
    logger = logging.getLogger(__name__)
    results = []

    for resolution in resolutions:
        if resolution['source'] == 'not_found':
            logger.warning(f"Skipping {resolution['filename']}: not found")
            continue

        logger.info(f"Downloading: {resolution['filename']}")

        try:
            if resolution['source'] == 'civitai':
                success = download_from_civitai(resolution)
            elif resolution['source'] == 'huggingface':
                success = download_from_huggingface(resolution)
            else:
                success = False

            results.append({
                'filename': resolution['filename'],
                'source': resolution['source'],
                'success': success
            })

        except Exception as e:
            logger.error(f"Download failed for {resolution['filename']}: {e}")
            results.append({
                'filename': resolution['filename'],
                'source': resolution['source'],
                'success': False,
                'error': str(e)
            })

    return results


def download_from_civitai(resolution: dict) -> bool:
    """Download model from Civitai using existing downloader"""
    logger = logging.getLogger(__name__)

    # Determine save location
    save_path = determine_save_path(resolution['filename'], resolution['expected_type'])

    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Build download URL
    url = f"{resolution['download_url']}?token={os.getenv('CIVITAI_API_KEY')}"

    logger.info(f"  Downloading from: {resolution['model_name']}")
    logger.info(f"  Save to: {save_path}")

    try:
        # Use existing lora-manager downloader
        import asyncio
        from comfyui_lora_manager.py.services.downloader import get_downloader

        async def download():
            downloader = await get_downloader()
            success, result = await downloader.download_file(
                url=url,
                save_path=save_path,
                progress_callback=log_progress,
                use_auth=True,
                allow_resume=True
            )
            return success

        # Run async download
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(download())

        if success:
            logger.info(f"  ✓ Downloaded: {resolution['filename']}")
            return True
        else:
            logger.error(f"  ✗ Failed: {resolution['filename']}")
            return False

    except ImportError:
        # Fallback to simple wget if lora-manager not available
        logger.info("  Using fallback wget download")
        return download_with_wget(url, save_path)


def download_from_huggingface(resolution: dict) -> bool:
    """Download model from HuggingFace using hf CLI"""
    logger = logging.getLogger(__name__)

    save_path = determine_save_path(resolution['filename'], resolution['expected_type'])
    save_dir = os.path.dirname(save_path)

    # Ensure directory exists
    os.makedirs(save_dir, exist_ok=True)

    logger.info(f"  Downloading from: {resolution['repo_id']}")
    logger.info(f"  Save to: {save_dir}")

    # Use hf download CLI
    cmd = [
        'hf', 'download',
        resolution['repo_id'],
        '--local-dir', save_dir,
        '--quiet'
    ]

    # Add token if available
    hf_token = os.getenv('HF_TOKEN')
    if hf_token:
        cmd.extend(['--token', hf_token])

    logger.debug(f"  Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"  ✓ Downloaded: {resolution['filename']}")
            return True
        else:
            logger.error(f"  ✗ Failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"  ✗ Timeout downloading {resolution['filename']}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        return False


def determine_save_path(filename: str, model_type: str) -> str:
    """Determine where to save the model"""
    config = load_config()
    comfyui_root = config['comfyui_root']

    type_to_dir = {
        'checkpoint': 'checkpoints',
        'lora': 'loras',
        'vae': 'vae',
        'controlnet': 'controlnet',
        'upscale_models': 'upscale_models',
        'clip_vision': 'clip_vision',
        'clip': 'clip',
        'unet': 'unet',
        'diffusion_models': 'diffusion_models',
        'text_encoders': 'text_encoders',
    }

    model_dir = type_to_dir.get(model_type, 'checkpoints')
    return os.path.join(comfyui_root, 'models', model_dir, filename)


def download_with_wget(url: str, save_path: str) -> bool:
    """Fallback download using wget"""
    logger = logging.getLogger(__name__)

    cmd = [
        'wget',
        '-c',  # Resume
        '--content-disposition',
        '--timeout=30',
        '--tries=5',
        '--retry-connrefused',
        '-O', save_path,
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"wget failed: {e}")
        return False


def log_progress(progress: float):
    """Log download progress"""
    logger = logging.getLogger(__name__)
    logger.debug(f"  Progress: {progress:.1f}%")
```

**Reuses:**
- Your `comfyui-lora-manager/downloader.py` for Civitai
- `hf` CLI for HuggingFace (via subprocess)
- wget as fallback

---

### 6. Logging System (`logger_setup.py`)

**Purpose:** Structured logging to /log directory

**Implementation:**
```python
import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: str = 'log', phase: str = 'run') -> logging.Logger:
    """Setup structured logging to file and console"""

    # Create log directory
    Path(log_dir).mkdir(exist_ok=True)

    # Generate log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'{phase}_{timestamp}.log')

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger('ComfyFixerSmart')
    logger.info(f"Logging initialized: {log_file}")

    return logger


def log_action(action: str, details: dict):
    """Log a structured action for agent parsing"""
    logger = logging.getLogger('ComfyFixerSmart')

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details
    }

    # Log as JSON for easy parsing
    import json
    logger.info(f"ACTION: {json.dumps(log_entry)}")
```

**Log Format:**
```
2025-10-12 14:30:00 [INFO] ComfyFixerSmart: Logging initialized: log/scan_20251012_143000.log
2025-10-12 14:30:01 [INFO] workflow_scanner: Scanning directory: /path/to/workflows
2025-10-12 14:30:02 [INFO] workflow_scanner: ✓ Parsed: workflow1.json (8 models)
2025-10-12 14:30:03 [INFO] inventory: Building local inventory
2025-10-12 14:30:05 [INFO] inventory: Inventory complete: 234 models, 45 node types
2025-10-12 14:30:06 [INFO] inventory: Missing: hunyuan_lora.safetensors (from workflow1.json)
2025-10-12 14:30:07 [INFO] resolver: Resolving: hunyuan_lora.safetensors
2025-10-12 14:30:09 [INFO] resolver:   ✓ Found on Civitai: 1186768
2025-10-12 14:30:10 [INFO] downloader: Downloading: hunyuan_lora.safetensors
2025-10-12 14:30:12 [INFO] downloader:   Downloading from: Move Enhancer
2025-10-12 14:30:13 [INFO] downloader:   Save to: /models/loras/hunyuan_lora.safetensors
2025-10-12 14:32:45 [INFO] downloader:   ✓ Downloaded: hunyuan_lora.safetensors
```

---

### 7. Status Tracking (`status.json`)

**Purpose:** Real-time status file for agents to query

**Schema:**
```json
{
  "timestamp": "2025-10-12T14:30:00",
  "phase": "downloading",
  "progress": {
    "current": 2,
    "total": 5,
    "percent": 40
  },
  "data": {
    "workflows_scanned": 15,
    "missing_models": 5,
    "missing_nodes": 2,
    "civitai_matches": 4,
    "huggingface_matches": 1,
    "downloads_successful": 2,
    "downloads_failed": 0,
    "current_download": "model_name.safetensors"
  },
  "errors": []
}
```

**Phases:**
- `idle` - Not running
- `scanning` - Scanning workflows and inventory
- `resolving` - Searching Civitai/HuggingFace
- `downloading` - Downloading models
- `complete` - Finished successfully
- `error` - Error occurred

**Agent can query:**
```python
import json

with open('status.json') as f:
    status = json.load(f)

if status['phase'] == 'downloading':
    print(f"Progress: {status['progress']['percent']}%")
    print(f"Current: {status['data']['current_download']}")
```

---

## Configuration (`config.json`)

```json
{
  "comfyui_root": "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable",
  "workflow_directories": [
    "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable/user/default/workflows",
    "/home/coldaine/StableDiffusionWorkflow"
  ],
  "api_keys": {
    "civitai": "${CIVITAI_API_KEY}",
    "huggingface": "${HF_TOKEN}"
  },
  "download": {
    "max_concurrent": 3,
    "timeout_seconds": 600,
    "verify_hashes": true
  },
  "search": {
    "fuzzy_threshold": 0.7,
    "max_results": 5
  }
}
```

---

## Dependencies

**New dependencies needed:**
```txt
# Required
requests>=2.31.0
huggingface_hub>=0.19.0
fuzzywuzzy>=0.18.0
python-Levenshtein>=0.21.0

# Optional (already have)
aiohttp>=3.9.0
```

**Install:**
```bash
cd ComfyFixerSmart
pip install -r requirements.txt
```

---

## Usage Examples

### For Humans

**Full auto mode:**
```bash
python comfy_fixer.py --auto
```

**Step by step:**
```bash
# Step 1: Scan
python comfy_fixer.py --scan

# Step 2: Review output/missing_models.json

# Step 3: Resolve
python comfy_fixer.py --resolve

# Step 4: Review output/resolutions.json

# Step 5: Download
python comfy_fixer.py --download
```

**Check status:**
```bash
python comfy_fixer.py --status
```

**Resume interrupted run:**
```bash
python comfy_fixer.py --resume
```

### For Agents

**Agent workflow:**
```python
import subprocess
import json
import time

# 1. Start the process
subprocess.Popen(['python', 'comfy_fixer.py', '--auto'])

# 2. Monitor status
while True:
    with open('status.json') as f:
        status = json.load(f)

    print(f"Phase: {status['phase']}")

    if status['phase'] == 'complete':
        print("✓ All done!")
        break
    elif status['phase'] == 'error':
        print("✗ Error occurred")
        print(status['errors'])
        break

    time.sleep(5)

# 3. Read results
with open('output/missing_models.json') as f:
    missing = json.load(f)
    print(f"Found {len(missing)} missing models")
```

---

## Agent Guide (`AGENT_GUIDE.md`)

Will contain:

1. **Quick Start** - How to run the tool
2. **Status Monitoring** - How to read status.json
3. **Output Files** - What each file contains
4. **Error Handling** - Common errors and solutions
5. **Log Parsing** - How to parse structured logs
6. **Resume Logic** - How to resume interrupted runs

---

## Implementation Timeline

**Phase 1: Core (2-3 days)**
- Setup project structure
- Implement workflow_scanner.py
- Implement inventory.py
- Basic logging

**Phase 2: Resolution (2-3 days)**
- Implement resolver.py (Civitai + HuggingFace)
- Add fuzzy matching
- Cache integration (optional)

**Phase 3: Download (2-3 days)**
- Implement downloader.py
- Civitai download integration
- HuggingFace hf CLI integration
- Progress tracking

**Phase 4: Polish (1-2 days)**
- Status tracking
- Error handling
- Documentation (AGENT_GUIDE.md)
- Testing

**Total: ~1-2 weeks**

---

## Key Design Decisions

### Why This Size?

**Not too simple:**
- ✅ Modular (each module has one responsibility)
- ✅ Reusable components
- ✅ Proper error handling
- ✅ Structured logging

**Not too complex:**
- ✅ No database for caching (optional, can add later)
- ✅ No web UI
- ✅ No complex async orchestration
- ✅ Simple file-based status tracking

### Why These Modules?

1. **workflow_scanner** - Core requirement: "scan all workflows"
2. **inventory** - Core requirement: "what we don't have"
3. **resolver** - Core requirement: "search for them"
4. **downloader** - Core requirement: "download them"
5. **logger_setup** - Core requirement: "log all actions"

Each module is **essential** to the workflow you described.

### Why No Cache?

- Can add later if API is slow
- File-based results serve as lightweight cache
- Reduces complexity for v1
- Easy to add in Phase 2 if needed

---

## Next Steps

1. **Review this plan** - Make sure it matches your needs
2. **Clarify questions:**
   - Should we handle custom node downloads? (GitHub repos)
   - Download confirmation before executing?
   - Specific logging format preferences?
3. **Start implementation** - Begin with Phase 1

---

**This is the "right size" - not minimal, not over-engineered, just appropriate for the task.**
