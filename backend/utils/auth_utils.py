# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

"""
Authentication utilities for ComfyUI Copilot
"""

from typing import Optional
from .globals import (
    clear_comfyui_copilot_api_key,
    get_comfyui_copilot_api_key,
    set_comfyui_copilot_api_key,
)
from .logger import log

def extract_and_store_api_key(request) -> Optional[str]:
    """
    Extract Bearer token from Authorization header and store it for this async request.
    
    Args:
        request: The aiohttp request object
        
    Returns:
        The extracted API key if successful, None otherwise
    """
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            set_comfyui_copilot_api_key(api_key)
            log.info("ComfyUI Copilot API key extracted for current request")
            
            # Verify it's stored correctly
            stored_key = get_comfyui_copilot_api_key()
            if stored_key == api_key:
                log.info("API key verification: Successfully stored in request context")
            else:
                log.error("API key verification: Storage failed")
                
            return api_key
        else:
            clear_comfyui_copilot_api_key()
            log.error("No valid Authorization header found")
            return None
    except Exception as e:
        log.error(f"Error extracting API key: {str(e)}")
        return None
