"""
Civitai Direct ID Downloader - Python Implementation

Ported from bash/civitai_url_downloader.sh
Extracts model ID from Civitai URLs or uses direct model ID,
fetches model details via /api/v1/models/{id} endpoint,
downloads specified version (default: latest) with SHA256 verification.
"""

import hashlib
import os
import re
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DownloadStatus(str, Enum):
    """Download operation status"""
    SUCCESS = "success"
    FAILED = "failed"
    HASH_MISMATCH = "hash_mismatch"
    NOT_FOUND = "not_found"


@dataclass
class DownloadResult:
    """Result of a download operation"""
    status: DownloadStatus
    model_id: int
    model_name: str
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'status': self.status.value,
            'model_id': self.model_id,
            'model_name': self.model_name,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'expected_hash': self.expected_hash,
            'actual_hash': self.actual_hash,
            'error_message': self.error_message
        }


class CivitaiDirectDownloader:
    """
    Direct model downloader using Civitai model IDs.

    Ported from bash/civitai_url_downloader.sh
    Bypasses search API entirely for 100% success rate.
    """

    def __init__(self, download_dir: Optional[str] = None, api_key: Optional[str] = None):
        self.download_dir = Path(download_dir or './downloads')
        self.download_dir.mkdir(exist_ok=True, parents=True)

        self.api_key = api_key or os.environ.get('CIVITAI_API_KEY', '')
        self.base_url = "https://civitai.com/api/v1"

    @staticmethod
    def extract_model_id(input_string: str) -> Optional[int]:
        """
        Extract model ID from URL or validate direct ID.

        Port of extract_model_id() from bash (lines 31-45).

        Args:
            input_string: Civitai URL or numeric model ID

        Returns:
            Model ID as integer, or None if invalid

        Examples:
            >>> extract_model_id("https://civitai.com/models/1091495")
            1091495
            >>> extract_model_id("https://civitai.com/models/1091495/better-detailed")
            1091495
            >>> extract_model_id("1091495")
            1091495
        """
        # Match: https://civitai.com/models/{id} or https://civitai.com/models/{id}/{name}
        url_pattern = r'https://civitai\.com/models/(\d+)(?:/.*)?'
        match = re.match(url_pattern, input_string)

        if match:
            return int(match.group(1))

        # Check if input is already a numeric ID
        if input_string.isdigit():
            return int(input_string)

        return None

    def fetch_model_details(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch model details from Civitai API.

        Port of fetch_model_details() from bash (lines 48-73).

        Args:
            model_id: Civitai model ID

        Returns:
            Model data dict, or None if failed
        """
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(
                f"{self.base_url}/models/{model_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                print(f"✗ Failed to fetch model details: HTTP {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            print(f"✗ Error fetching model details: {e}")
            return None

    def get_download_info(self, model_data: Dict[str, Any],
                         version_id: Optional[int] = None) -> Optional[Tuple[Dict, Dict]]:
        """
        Get download information from model data.

        Port of get_download_url() and get_file_info() from bash (lines 76-197).

        Args:
            model_data: Model JSON from API
            version_id: Specific version ID, or None for latest

        Returns:
            Tuple of (version_dict, file_dict), or None if not found
        """
        versions = model_data.get('modelVersions', [])
        if not versions:
            print("✗ No versions found for this model")
            return None

        # Find target version
        target_version = None
        if version_id:
            for version in versions:
                if version.get('id') == version_id:
                    target_version = version
                    break
            if not target_version:
                print(f"✗ Version {version_id} not found")
                return None
        else:
            # Use latest (first in list)
            target_version = versions[0]

        # Find primary file or largest file
        files = target_version.get('files', [])
        if not files:
            print("✗ No files found in this version")
            return None

        # Prefer primary file
        primary_file = next((f for f in files if f.get('primary')), None)

        if not primary_file:
            # Fall back to largest file
            primary_file = max(files, key=lambda f: f.get('sizeKB', 0))

        return target_version, primary_file

    def download_file(self, url: str, filepath: Path, expected_hash: Optional[str] = None,
                     show_progress: bool = True) -> DownloadResult:
        """
        Download file with progress tracking and optional hash verification.

        Port of download_file() and verify_file() from bash (lines 119-173).

        Args:
            url: Download URL
            filepath: Target file path
            expected_hash: Expected SHA256 hash (optional)
            show_progress: Show download progress

        Returns:
            DownloadResult object
        """
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            print(f"⬇ Downloading to: {filepath}")

            # Stream download with progress
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if show_progress and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

            if show_progress:
                print()  # New line after progress

            file_size = filepath.stat().st_size
            print(f"✓ Download completed: {file_size:,} bytes")

            # Verify hash if provided
            if expected_hash:
                print("🔐 Verifying file integrity...")
                actual_hash = self.calculate_sha256(filepath)

                if actual_hash.lower() == expected_hash.lower():
                    print("✓ SHA256 verification passed")
                    return DownloadResult(
                        status=DownloadStatus.SUCCESS,
                        model_id=0,  # Will be filled by caller
                        model_name="",
                        filename=filepath.name,
                        file_path=str(filepath),
                        file_size=file_size,
                        expected_hash=expected_hash,
                        actual_hash=actual_hash
                    )
                else:
                    print(f"✗ SHA256 verification failed")
                    print(f"  Expected: {expected_hash}")
                    print(f"  Actual:   {actual_hash}")
                    filepath.unlink()  # Delete corrupted file
                    return DownloadResult(
                        status=DownloadStatus.HASH_MISMATCH,
                        model_id=0,
                        model_name="",
                        filename=filepath.name,
                        expected_hash=expected_hash,
                        actual_hash=actual_hash,
                        error_message="Hash verification failed"
                    )

            # Success without hash verification
            return DownloadResult(
                status=DownloadStatus.SUCCESS,
                model_id=0,
                model_name="",
                filename=filepath.name,
                file_path=str(filepath),
                file_size=file_size
            )

        except Exception as e:
            print(f"✗ Download failed: {e}")
            return DownloadResult(
                status=DownloadStatus.FAILED,
                model_id=0,
                model_name="",
                filename=filepath.name if filepath else "unknown",
                error_message=str(e)
            )

    @staticmethod
    def calculate_sha256(filepath: Path) -> str:
        """
        Calculate SHA256 hash of file.

        Port of calculate_sha256() from bash (lines 142-152).

        Args:
            filepath: Path to file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256_hash = hashlib.sha256()

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def download_by_id(self, model_id: int, version_id: Optional[int] = None,
                      output_filename: Optional[str] = None) -> DownloadResult:
        """
        Download model by direct ID.

        Port of main() from bash (lines 200-298).

        Args:
            model_id: Civitai model ID
            version_id: Specific version ID (optional, uses latest if not provided)
            output_filename: Override output filename (optional)

        Returns:
            DownloadResult object
        """
        print(f"🔍 Fetching model details for ID: {model_id}")

        # Fetch model details
        model_data = self.fetch_model_details(model_id)
        if not model_data:
            return DownloadResult(
                status=DownloadStatus.NOT_FOUND,
                model_id=model_id,
                model_name="Unknown",
                filename="",
                error_message="Failed to fetch model details"
            )

        model_name = model_data.get('name', f'Model {model_id}')
        print(f"📦 Model: {model_name}")

        # Get download info
        download_info = self.get_download_info(model_data, version_id)
        if not download_info:
            return DownloadResult(
                status=DownloadStatus.NOT_FOUND,
                model_id=model_id,
                model_name=model_name,
                filename="",
                error_message="No downloadable files found"
            )

        version, file_info = download_info

        filename = output_filename or file_info.get('name', f'model_{model_id}.safetensors')
        file_size_kb = file_info.get('sizeKB', 0)
        expected_hash = file_info.get('hashes', {}).get('SHA256')

        print(f"📄 File: {filename}")
        if file_size_kb > 0:
            print(f"📊 Size: {file_size_kb / 1024:.1f} MB")

        # Construct download URL
        version_id_actual = version.get('id')
        download_url = f"https://civitai.com/api/download/models/{version_id_actual}"

        # Download and verify
        filepath = self.download_dir / filename
        result = self.download_file(download_url, filepath, expected_hash)

        # Update result with model info
        result.model_id = model_id
        result.model_name = model_name

        if result.status == DownloadStatus.SUCCESS:
            print(f"✅ Download successful: {filepath}")
        else:
            print(f"❌ Download failed: {result.error_message}")

        return result

    def download_by_url(self, url: str, version_id: Optional[int] = None) -> DownloadResult:
        """
        Download model by Civitai URL.

        Convenience method that extracts ID and calls download_by_id().

        Args:
            url: Civitai model URL
            version_id: Specific version ID (optional)

        Returns:
            DownloadResult object
        """
        model_id = self.extract_model_id(url)
        if not model_id:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                model_id=0,
                model_name="",
                filename="",
                error_message="Invalid URL or model ID"
            )

        return self.download_by_id(model_id, version_id)


def main():
    """CLI interface for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Direct Civitai model downloader with hash verification'
    )
    parser.add_argument('model_id_or_url', help='Civitai model ID or URL')
    parser.add_argument('--version-id', type=int, help='Specific version ID (optional)')
    parser.add_argument('--output-dir', help='Download directory (default: ./downloads)')
    parser.add_argument('--output-name', help='Override output filename')

    args = parser.parse_args()

    downloader = CivitaiDirectDownloader(download_dir=args.output_dir)

    # Check if input is URL or ID
    if args.model_id_or_url.startswith('http'):
        result = downloader.download_by_url(args.model_id_or_url, args.version_id)
    else:
        model_id = int(args.model_id_or_url)
        result = downloader.download_by_id(model_id, args.version_id, args.output_name)

    # Exit with appropriate status code
    exit(0 if result.status == DownloadStatus.SUCCESS else 1)


if __name__ == '__main__':
    main()
