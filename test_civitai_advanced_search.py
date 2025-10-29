#!/usr/bin/env python3
"""
Test script to demonstrate the Civitai Advanced Search functionality.

This script tests the complete workflow for finding and downloading the two
previously problematic models that failed with standard Civitai API search.
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, 'src')

# Set the API key from environment
os.environ['CIVITAI_API_KEY'] = os.environ.get('CIVITAI_API_KEY', '')

from comfyfixersmart.search import CivitaiSearch
from comfyfixersmart.civitai_tools.direct_id_backend import DirectIDBackend


def test_problematic_models():
    """Test the two previously problematic models."""
    print("=" * 60)
    print("CIVITAI ADVANCED SEARCH - FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Initialize the search components
    civitai_search = CivitaiSearch()
    direct_backend = DirectIDBackend()
    
    print(f"Loaded {len(direct_backend.known_models)} known models from mapping")
    print()
    
    # Test the two problematic models
    problematic_models = [
        {
            "name": "Better detailed pussy and anus v3.0",
            "id": 1091495,
            "search_term": "better detailed pussy and anus"
        },
        {
            "name": "Eyes High Definition V1", 
            "id": 670378,
            "search_term": "eyes high definition"
        }
    ]
    
    all_tests_passed = True
    
    for model in problematic_models:
        print(f"Testing: {model['name']} (ID: {model['id']})")
        print("-" * 40)
        
        # Test 1: Direct ID lookup
        print("1. Direct ID lookup...")
        result = civitai_search.search_by_id(model['id'])
        if result and result.status == 'FOUND':
            print(f"   ✅ SUCCESS: Found via direct ID")
            print(f"   Model ID: {result.civitai_id}")
            print(f"   Model Name: {result.civitai_name}")
            print(f"   Download URL: {result.download_url}")
            print(f"   Confidence: {result.confidence}")
        else:
            print("   ❌ FAILED: Direct ID lookup")
            all_tests_passed = False
            continue
            
        # Test 2: Known models lookup
        print("2. Known models lookup...")
        known_result = direct_backend.lookup_by_name(model['search_term'])
        if known_result:
            print(f"   ✅ SUCCESS: Found via known models mapping")
            print(f"   Model ID: {known_result.civitai_id}")
            print(f"   Model Name: {known_result.civitai_name}")
        else:
            print("   ❌ FAILED: Known models lookup")
            all_tests_passed = False
            
        # Test 3: Multi-strategy search
        print("3. Multi-strategy search...")
        model_ref = {
            'filename': f"{model['search_term'].replace(' ', '_')}_v3.0.safetensors",
            'type': 'loras'
        }
        multi_results = civitai_search.search_multi_strategy(model_ref)
        if multi_results:
            print(f"   ✅ SUCCESS: Found via multi-strategy search")
            print(f"   Top candidate: {multi_results[0].civitai_name} (ID: {multi_results[0].civitai_id})")
        else:
            print("   ❌ FAILED: Multi-strategy search")
            all_tests_passed = False
            
        print()
    
    # Summary
    print("=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The Civitai Advanced Search implementation successfully resolves")
        print("the two previously problematic models that failed with standard")
        print("Civitai API search.")
    else:
        print("❌ SOME TESTS FAILED")
        print("There are issues with the implementation that need to be addressed.")
    print("=" * 60)
    
    return all_tests_passed


if __name__ == "__main__":
    success = test_problematic_models()
    sys.exit(0 if success else 1)