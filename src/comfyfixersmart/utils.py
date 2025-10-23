"""
Utility Functions for ComfyFixerSmart

Provides common utilities used across ComfyFixerSmart components:
- Path management and validation helpers
- File system utilities with proper error handling
- Model type mappings and validation logic
- API key management
- Common data validation functions
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Any
from urllib.parse import urlparse
import json


def get_api_key() -> str:
    """Get Civitai API key from environment variables."""
    key = os.getenv('CIVITAI_API_KEY')
    if not key:
        raise ValueError("CIVITAI_API_KEY environment variable not found. "
                        "Please set it in your ~/.secrets file or environment.")
    return key


def validate_api_key(api_key: str) -> bool:
    """Validate Civitai API key format."""
    # Civitai API keys are typically 32-character hex strings
    return bool(re.match(r'^[a-fA-F0-9]{32}$', api_key))


def determine_model_type(node_type: str, custom_mapping: Optional[Dict[str, str]] = None) -> str:
    """
    Map ComfyUI node type to model directory name.

    Args:
        node_type: The ComfyUI node class name
        custom_mapping: Optional custom mapping to override defaults

    Returns:
        Model directory name (e.g., 'checkpoints', 'loras', 'vae')
    """
    # Default mapping based on common ComfyUI node types
    default_mapping = {
        'CheckpointLoaderSimple': 'checkpoints',
        'CheckpointLoader': 'checkpoints',
        'LoraLoader': 'loras',
        'LoraLoaderModelOnly': 'loras',
        'VAELoader': 'vae',
        'CLIPLoader': 'clip',
        'DualCLIPLoader': 'clip',
        'ControlNetLoader': 'controlnet',
        'ControlNetLoaderAdvanced': 'controlnet',
        'UpscaleModelLoader': 'upscale_models',
        'CLIPVisionLoader': 'clip_vision',
        'UNETLoader': 'unet',
        'SAMLoader': 'sams',
        'GroundingDinoModelLoader': 'grounding-dino',
        'IPAdapterModelLoader': 'ipadapter',
        'GLIGENLoader': 'gligen',
        'StyleModelLoader': 'style_models',
        'CLIPVisionLoaderFromURL': 'clip_vision',
        'PhotoMakerLoader': 'photomaker',
        'InstantIDModelLoader': 'instantid',
        'PulseT5Loader': 'pulset5',
        'AestheticScoreLoader': 'aesthetic_score',
    }

    # Use custom mapping if provided, otherwise use defaults
    mapping = custom_mapping or default_mapping
    return mapping.get(node_type, 'checkpoints')


def validate_model_filename(filename: str) -> bool:
    """
    Validate that a filename looks like a valid model file.

    Args:
        filename: The filename to validate

    Returns:
        True if filename appears to be a valid model file
    """
    if not filename or not isinstance(filename, str):
        return False

    # Check for valid extensions
    valid_extensions = {'.safetensors', '.ckpt', '.pt', '.bin', '.pth', '.onnx'}
    path = Path(filename)
    if path.suffix.lower() not in valid_extensions:
        return False

    # Check for reasonable filename length
    if len(filename) < 5 or len(filename) > 255:
        return False

    # Check for suspicious characters
    suspicious_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in suspicious_chars):
        return False

    return True


def get_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculate checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5', 'sha256', etc.)

    Returns:
        Hexadecimal checksum string, or None if file doesn't exist or error
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return None

    try:
        hash_func = getattr(hashlib, algorithm)()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (OSError, AttributeError):
        return None


def validate_url(url: str) -> bool:
    """
    Validate that a string is a valid URL.

    Args:
        url: The URL string to validate

    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_civitai_response(response_data: Dict[str, Any],
                              requested_id: Optional[int] = None,
                              endpoint_type: str = 'model') -> Dict[str, Any]:
    """
    Validate Civitai API response and check for ID mismatches.

    CRITICAL: Civitai API has a quirk where /api/v1/images?ids={id} may return
    a different image if the requested ID doesn't exist, instead of returning 404.
    This function validates the response matches what was requested.

    Args:
        response_data: Parsed JSON response from Civitai API
        requested_id: The ID that was requested (model ID or image ID)
        endpoint_type: Type of endpoint ('model', 'image', 'images')

    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'error_message': Optional[str],
            'warning_message': Optional[str],
            'data': The validated data or None
        }

    Raises:
        ValueError: If validation fails critically
    """
    result = {
        'valid': True,
        'error_message': None,
        'warning_message': None,
        'data': response_data
    }

    # Check for empty response
    if not response_data:
        result['valid'] = False
        result['error_message'] = "API returned empty response"
        result['data'] = None
        return result

    # Validate based on endpoint type
    if endpoint_type == 'images':
        # /api/v1/images?ids=... returns {'items': [...]}
        items = response_data.get('items', [])

        if not items:
            result['valid'] = False
            result['error_message'] = f"Image {requested_id} not found (empty items array)"
            result['data'] = None
            return result

        # CRITICAL: Validate returned ID matches requested ID
        if requested_id is not None:
            returned_item = items[0]
            returned_id = returned_item.get('id')

            if returned_id != requested_id:
                result['valid'] = False
                result['error_message'] = (
                    f"API returned wrong image. "
                    f"Requested: {requested_id}, Got: {returned_id}. "
                    f"This image may have been deleted or is restricted."
                )
                result['data'] = None
                return result

    elif endpoint_type == 'model':
        # /api/v1/models/{id} returns model object directly
        if requested_id is not None:
            returned_id = response_data.get('id')

            if returned_id != requested_id:
                result['valid'] = False
                result['error_message'] = (
                    f"API returned wrong model. "
                    f"Requested: {requested_id}, Got: {returned_id}"
                )
                result['data'] = None
                return result

    return result


def fetch_civitai_image(image_id: int, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch image metadata from Civitai with validation.

    This function implements defensive programming against Civitai API quirks
    where requesting a non-existent image may return a different image instead
    of a 404 error.

    Args:
        image_id: Civitai image ID to fetch
        api_key: Civitai API key (uses environment if not provided)

    Returns:
        Image metadata dictionary

    Raises:
        ValueError: If image not found or API returns wrong image
        requests.RequestException: If API request fails
    """
    import requests

    if api_key is None:
        api_key = get_api_key()

    # Use /api/v1/images?ids={id} endpoint
    url = f"https://civitai.com/api/v1/images"
    params = {'ids': image_id}
    headers = {'Authorization': f'Bearer {api_key}'}

    response = requests.get(url, params=params, headers=headers, timeout=30)

    if response.status_code != 200:
        raise ValueError(
            f"Civitai API error: HTTP {response.status_code} for image {image_id}"
        )

    data = response.json()

    # Validate response
    validation = validate_civitai_response(data, requested_id=image_id, endpoint_type='images')

    if not validation['valid']:
        raise ValueError(validation['error_message'])

    # Return the first (and validated) item
    return data['items'][0]


def safe_path_join(base_path: Union[str, Path], *paths: Union[str, Path]) -> Path:
    """
    Safely join paths without allowing directory traversal.

    Args:
        base_path: Base directory path
        *paths: Additional path components

    Returns:
        Safe joined path

    Raises:
        ValueError: If path traversal is detected
    """
    base = Path(base_path).resolve()
    result = base

    for path in paths:
        path = Path(path)
        # Check for directory traversal attempts
        if '..' in path.parts or path.is_absolute():
            raise ValueError(f"Unsafe path component: {path}")
        result = result / path

    # Ensure result is still within base directory
    result = result.resolve()
    if not str(result).startswith(str(base)):
        raise ValueError(f"Path traversal detected: {result}")

    return result


def ensure_directory(path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create
        parents: Create parent directories if needed
        exist_ok: Don't raise error if directory already exists

    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=parents, exist_ok=exist_ok)
    return path


def find_files_by_pattern(directory: Union[str, Path], pattern: str = "*",
                        recursive: bool = True) -> List[Path]:
    """
    Find files matching a pattern in a directory.

    Args:
        directory: Directory to search in
        pattern: Glob pattern (e.g., "*.json", "**/*.safetensors")
        recursive: Whether to search recursively

    Returns:
        List of matching file paths
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return []

    if recursive:
        return list(dir_path.rglob(pattern))
    else:
        return list(dir_path.glob(pattern))


def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes, or None if file doesn't exist
    """
    path = Path(file_path)
    if path.exists() and path.is_file():
        return path.stat().st_size
    return None


def validate_json_file(file_path: Union[str, Path]) -> bool:
    """
    Validate that a file contains valid JSON.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if file contains valid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def load_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Load data from a JSON file with error handling.

    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json_file(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """
    Save data to a JSON file with error handling.

    Args:
        file_path: Path to save the JSON file
        data: Data to serialize
        indent: JSON indentation level

    Returns:
        True if save was successful
    """
    try:
        # Ensure parent directory exists
        ensure_directory(file_path.parent)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (OSError, TypeError):
        return False


def build_local_inventory(models_dir: Union[str, Path],
                         extensions: Optional[List[str]] = None) -> Set[str]:
    """
    Build inventory of local model files.

    Args:
        models_dir: Directory containing model files
        extensions: List of file extensions to include (default: common model extensions)

    Returns:
        Set of model filenames
    """
    if extensions is None:
        extensions = ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']

    inventory = set()
    models_path = Path(models_dir)

    if not models_path.exists():
        return inventory

    for ext in extensions:
        pattern = f"**/*{ext}"
        for model_file in models_path.glob(pattern):
            if model_file.is_file():
                inventory.add(model_file.name)

    return inventory


def extract_models_from_workflow(workflow_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Extract model references from a ComfyUI workflow JSON file.

    Args:
        workflow_path: Path to the workflow JSON file

    Returns:
        List of model dictionaries with filename, type, and node_type
    """
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        models = []
        nodes = data.get('nodes', [])

        for node in nodes:
            node_type = node.get('type', '')

            # Check widgets_values for model filenames
            for value in node.get('widgets_values', []):
                if isinstance(value, str) and _is_model_filename(value):
                    filename = os.path.basename(value)
                    model_type = determine_model_type(node_type)

                    models.append({
                        'filename': filename,
                        'type': model_type,
                        'node_type': node_type,
                        'workflow_path': str(workflow_path)
                    })

        return models

    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to parse workflow {workflow_path}: {e}")


def _is_model_filename(filename: str) -> bool:
    """Check if a filename looks like a model file."""
    if not filename or not isinstance(filename, str):
        return False

    # Check for model file extensions
    model_extensions = {'.safetensors', '.ckpt', '.pt', '.bin', '.pth'}
    path = Path(filename)

    return path.suffix.lower() in model_extensions


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)

    while size >= 1024 and size_index < len(size_names) - 1:
        size /= 1024
        size_index += 1

    if size_index == 0:
        return f"{int(size)} {size_names[size_index]}"
    else:
        return ".1f"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename

    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')

    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized


def get_relative_path(file_path: Union[str, Path], base_path: Union[str, Path]) -> Optional[str]:
    """
    Get relative path from base directory.

    Args:
        file_path: Full path to file
        base_path: Base directory path

    Returns:
        Relative path string, or None if not relative
    """
    try:
        return str(Path(file_path).relative_to(Path(base_path)))
    except ValueError:
        return None