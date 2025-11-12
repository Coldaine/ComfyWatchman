#!/usr/bin/env python3
"""
Test script for smart pattern recognition in QwenSearch.
Tests the HF model pattern detection and early termination logic.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from comfywatchman.search import QwenSearch

def test_pattern_recognition():
    """Test the pattern recognition functionality."""
    
    # Create QwenSearch instance
    search = QwenSearch()
    
    # Test cases: (filename, model_type, expected_skip_civitai, expected_reason_contains)
    test_cases = [
        # SAM models - should be recognized as HF
        ("sam_vit_b_01ec64.pth", "checkpoints", True, "Pattern match"),
        ("facebook_sam_b.pth", "checkpoints", True, "hf_prefix_match"),
        ("segment_anything_vit_h.pth", "checkpoints", True, "Pattern match"),
        
        # RIFE models - should be recognized as HF
        ("rife49.pth", "checkpoints", True, "Pattern match"),
        ("rife_v2_4.pth", "checkpoints", True, "Pattern match"),
        ("rife.pth", "checkpoints", True, "Pattern match"),
        
        # ControlNet models - should be recognized as HF
        ("control_canny_v11p.pth", "controlnet", True, "Pattern match"),
        ("control_openpose_v11p.pth", "controlnet", True, "Pattern match"),
        
        # Upscaling models - should be recognized as HF
        ("4xNMKDSuperscale_SP_178000_G.pth", "upscale_models", True, "Pattern match"),
        ("RealESRGAN_x2plus.pth", "upscale_models", True, "Pattern match"),
        
        # CLIP models - should be recognized as HF
        ("clip-vit-base-patch32.pth", "clip", True, "Pattern match"),
        ("text_encoder.pth", "clip", True, "Pattern match"),
        
        # Common HF prefixes - should be recognized as HF
        ("stabilityai_sd-v1-5.ckpt", "checkpoints", True, "hf_prefix_match"),
        ("microsoft_resnet50.pth", "checkpoints", True, "hf_prefix_match"),
        ("openai_clip_vit-base-patch32.pth", "clip", True, "hf_prefix_match"),
        
        # Regular Civitai models - should NOT be recognized as HF
        ("animaide_1.0.safetensors", "checkpoints", False, "No HF patterns"),
        ("anime_style_lora_v15.safetensors", "loras", False, "No HF patterns"),
        ("korean_doll_likeness_v15.safetensors", "loras", False, "No HF patterns"),
    ]
    
    print("Testing Smart Pattern Recognition for HuggingFace Models")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for filename, model_type, expected_skip, expected_reason_fragment in test_cases:
        try:
            should_skip, reason = search._should_skip_civitai(filename, model_type)
            
            if should_skip == expected_skip:
                if expected_reason_fragment.lower() in reason.lower():
                    print(f"✅ PASS: {filename}")
                    print(f"   Skip Civitai: {should_skip} (expected: {expected_skip})")
                    print(f"   Reason: {reason}")
                    passed += 1
                else:
                    print(f"❌ FAIL: {filename}")
                    print(f"   Expected reason to contain: {expected_reason_fragment}")
                    print(f"   Actual reason: {reason}")
                    failed += 1
            else:
                print(f"❌ FAIL: {filename}")
                print(f"   Expected skip: {expected_skip}, got: {should_skip}")
                print(f"   Reason: {reason}")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {filename} - {e}")
            failed += 1
            
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Pattern recognition is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

def test_hf_pattern_lists():
    """Test that HF pattern lists are properly initialized."""
    search = QwenSearch()
    
    print("Testing HF Pattern Lists Initialization")
    print("=" * 40)
    
    patterns = search.hf_model_patterns
    
    expected_categories = [
        "sam_patterns",
        "rife_patterns", 
        "controlnet_patterns",
        "upscaler_patterns",
        "clip_patterns",
        "vae_patterns",
        "hf_prefixes",
        "research_patterns"
    ]
    
    all_good = True
    for category in expected_categories:
        if category in patterns:
            print(f"✅ {category}: {len(patterns[category])} patterns")
        else:
            print(f"❌ Missing category: {category}")
            all_good = False
    
    print("=" * 40)
    if all_good:
        print("🎉 All pattern categories are properly initialized.")
        return True
    else:
        print("❌ Some pattern categories are missing.")
        return False

if __name__ == "__main__":
    print("Smart Pattern Recognition Test Suite")
    print("=" * 60)
    
    # Test pattern list initialization
    patterns_ok = test_hf_pattern_lists()
    print()
    
    # Test pattern recognition functionality  
    recognition_ok = test_pattern_recognition()
    
    print("\n" + "=" * 60)
    if patterns_ok and recognition_ok:
        print("🎉 ALL TESTS PASSED! Smart pattern recognition is working correctly.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        sys.exit(1)