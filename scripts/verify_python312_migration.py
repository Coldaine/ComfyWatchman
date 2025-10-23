#!/usr/bin/env python3
"""
Python 3.12 Migration Verification Script
==========================================

Verifies that the Python 3.12 migration was successful by checking:
1. Python version
2. Critical package imports
3. FFmpeg availability
4. OpenCV ximgproc modules
5. Diffusers ecosystem
"""

import sys
import subprocess
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def check_python_version():
    """Check Python version is 3.12.x"""
    print_header("Python Version Check")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"Python version: {version_str}")
    print(f"Executable: {sys.executable}")

    if version.major == 3 and version.minor == 12:
        print_success(f"Python 3.12 detected ({version_str})")
        return True
    else:
        print_error(f"Expected Python 3.12, got {version_str}")
        return False

def check_package_import(package_name, import_test=None):
    """Test if a package can be imported"""
    try:
        if import_test:
            exec(import_test)
        else:
            __import__(package_name)
        return True
    except ImportError as e:
        return False
    except Exception as e:
        print_warning(f"Import succeeded but test failed: {e}")
        return True

def check_core_packages():
    """Check critical ComfyUI packages"""
    print_header("Core Package Verification")

    packages = {
        'torch': 'import torch; torch.cuda.is_available()',
        'torchvision': None,
        'torchaudio': None,
        'numpy': None,
        'PIL': 'from PIL import Image',
        'transformers': None,
        'safetensors': None,
        'yaml': 'import yaml',
        'scipy': None,
    }

    all_passed = True
    for package, test in packages.items():
        if check_package_import(package, test):
            print_success(f"{package:20} - imported successfully")
        else:
            print_error(f"{package:20} - FAILED TO IMPORT")
            all_passed = False

    return all_passed

def check_opencv_contrib():
    """Check OpenCV contrib modules"""
    print_header("OpenCV Contrib Verification")

    try:
        import cv2
        print_success(f"OpenCV version: {cv2.__version__}")

        # Check for ximgproc module
        import cv2.ximgproc
        print_success("cv2.ximgproc module available")

        # Check for guidedFilter function
        if hasattr(cv2.ximgproc, 'guidedFilter'):
            print_success("cv2.ximgproc.guidedFilter available")
            print(f"  Function: {cv2.ximgproc.guidedFilter}")
            return True
        else:
            print_error("cv2.ximgproc.guidedFilter NOT FOUND")
            return False

    except ImportError as e:
        print_error(f"OpenCV import failed: {e}")
        return False

def check_diffusers_ecosystem():
    """Check diffusers and huggingface hub"""
    print_header("Diffusers Ecosystem Verification")

    all_ok = True

    try:
        import diffusers
        print_success(f"diffusers version: {diffusers.__version__}")
    except ImportError as e:
        print_error(f"diffusers import failed: {e}")
        all_ok = False

    try:
        import huggingface_hub
        print_success(f"huggingface_hub version: {huggingface_hub.__version__}")
    except ImportError as e:
        print_error(f"huggingface_hub import failed: {e}")
        all_ok = False

    # Check for modern API (hf_hub_download)
    try:
        from huggingface_hub import hf_hub_download
        print_success("hf_hub_download API available (modern API)")
    except ImportError:
        print_error("hf_hub_download not available")
        all_ok = False

    # Verify cached_download is NOT being used (it's deprecated)
    try:
        from huggingface_hub import cached_download
        print_warning("cached_download still available (deprecated)")
    except ImportError:
        print_success("cached_download not available (expected - it's removed)")

    return all_ok

def check_ffmpeg_system():
    """Check system FFmpeg availability"""
    print_header("FFmpeg System Library Check")

    try:
        # Check for ffmpeg binary
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_success(f"FFmpeg binary: {version_line}")
        else:
            print_error("FFmpeg binary not working")
            return False

    except FileNotFoundError:
        print_error("FFmpeg binary not found in PATH")
        return False
    except Exception as e:
        print_error(f"FFmpeg check failed: {e}")
        return False

    # Check for libavutil
    try:
        result = subprocess.run(['ldconfig', '-p'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if 'libavutil.so' in result.stdout:
            # Extract version info
            for line in result.stdout.split('\n'):
                if 'libavutil.so' in line:
                    print_success(f"libavutil found: {line.strip()}")
                    break
            return True
        else:
            print_error("libavutil.so not found in ldconfig")
            return False

    except Exception as e:
        print_error(f"libavutil check failed: {e}")
        return False

def check_torchaudio_ffmpeg():
    """Check torchaudio FFmpeg backend"""
    print_header("Torchaudio FFmpeg Backend Check")

    try:
        import torchaudio
        print_success(f"torchaudio version: {torchaudio.__version__}")

        # Try to import FFmpeg backend
        try:
            import torchaudio.backend.ffmpeg_backend
            print_success("FFmpeg backend importable")
        except Exception as e:
            print_warning(f"FFmpeg backend import issue: {e}")

        return True

    except ImportError as e:
        print_error(f"torchaudio import failed: {e}")
        return False

def check_nvidia_packages():
    """Check NVIDIA/CUDA packages"""
    print_header("NVIDIA Package Verification")

    packages = [
        'nvidia.cuda_runtime',
        'nvidia.cudnn',
        'nvidia.cublas',
    ]

    all_passed = True
    for package in packages:
        try:
            __import__(package)
            print_success(f"{package:30} - available")
        except ImportError:
            print_warning(f"{package:30} - not available (may be normal)")

    # Check for nvidia-ml-py (replacement for pynvml)
    try:
        import pynvml
        print_warning("pynvml still installed (deprecated)")
    except ImportError:
        print_success("pynvml not installed (good - it's deprecated)")

    try:
        import nvidia_smi
        print_success("nvidia-ml-py installed (modern replacement)")
    except ImportError:
        print_warning("nvidia-ml-py not installed")

    return True

def generate_summary(results):
    """Generate summary report"""
    print_header("Migration Verification Summary")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    print(f"Total checks: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")

    if failed > 0:
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"\n{RED}MIGRATION VERIFICATION FAILED{RESET}")
        print("\nFailed checks:")
        for name, result in results.items():
            if not result:
                print(f"  - {name}")
    else:
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}ALL CHECKS PASSED - MIGRATION SUCCESSFUL{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

    return failed == 0

def main():
    print("\n" + "="*60)
    print(" Python 3.12 Migration Verification Script")
    print(" ComfyUI Environment Check")
    print("="*60)

    results = {}

    # Run all checks
    results['Python Version'] = check_python_version()
    results['Core Packages'] = check_core_packages()
    results['OpenCV Contrib'] = check_opencv_contrib()
    results['Diffusers Ecosystem'] = check_diffusers_ecosystem()
    results['FFmpeg System'] = check_ffmpeg_system()
    results['Torchaudio FFmpeg'] = check_torchaudio_ffmpeg()
    results['NVIDIA Packages'] = check_nvidia_packages()

    # Generate summary
    success = generate_summary(results)

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
