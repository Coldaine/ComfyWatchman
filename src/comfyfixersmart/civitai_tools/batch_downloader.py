"""
Civitai Batch Downloader - Python Implementation

Ported from bash/batch_civitai_downloader.sh
Downloads multiple models from a JSON list with retry logic.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .direct_downloader import CivitaiDirectDownloader, DownloadStatus, DownloadResult


class BatchStatus(str, Enum):
    """Batch download status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BatchJob:
    """A batch download job"""
    model_id: int
    model_name: Optional[str] = None
    version_id: Optional[int] = None
    status: BatchStatus = BatchStatus.PENDING
    attempts: int = 0
    max_retries: int = 3
    result: Optional[DownloadResult] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model_id': self.model_id,
            'model_name': self.model_name,
            'version_id': self.version_id,
            'status': self.status.value,
            'attempts': self.attempts,
            'max_retries': self.max_retries,
            'result': self.result.to_dict() if self.result else None,
            'error': self.error
        }


@dataclass
class BatchSummary:
    """Summary of batch download operation"""
    total: int
    successful: int
    failed: int
    skipped: int
    jobs: List[BatchJob]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total': self.total,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'jobs': [job.to_dict() for job in self.jobs]
        }


class CivitaiBatchDownloader:
    """
    Batch model downloader with retry logic.

    Ported from bash/batch_civitai_downloader.sh
    """

    def __init__(self, download_dir: Optional[str] = None,
                 max_retries: int = 3,
                 delay_between_downloads: float = 2.0):
        """
        Initialize batch downloader.

        Args:
            download_dir: Download directory
            max_retries: Maximum retry attempts per model
            delay_between_downloads: Delay in seconds between downloads
        """
        self.downloader = CivitaiDirectDownloader(download_dir)
        self.max_retries = max_retries
        self.delay_between_downloads = delay_between_downloads

    def download_batch(self, jobs: List[BatchJob],
                      continue_on_failure: bool = True) -> BatchSummary:
        """
        Download multiple models in batch.

        Args:
            jobs: List of BatchJob objects
            continue_on_failure: Continue downloading if a model fails

        Returns:
            BatchSummary with results
        """
        print(f"🚀 Starting batch download of {len(jobs)} models")
        print(f"Max retries per model: {self.max_retries}")
        print(f"Delay between downloads: {self.delay_between_downloads}s")
        print("=" * 60)

        successful = 0
        failed = 0
        skipped = 0

        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] Processing: {job.model_name or f'Model {job.model_id}'}")

            if job.status == BatchStatus.COMPLETED:
                print("  ⏭️  Already completed, skipping")
                skipped += 1
                continue

            job.status = BatchStatus.IN_PROGRESS

            # Attempt download with retries
            while job.attempts < self.max_retries:
                job.attempts += 1
                print(f"  Attempt {job.attempts}/{self.max_retries}")

                try:
                    result = self.downloader.download_by_id(
                        job.model_id,
                        job.version_id
                    )

                    job.result = result

                    if result.status == DownloadStatus.SUCCESS:
                        job.status = BatchStatus.COMPLETED
                        successful += 1
                        print(f"  ✅ Success")
                        break
                    else:
                        job.error = result.error_message
                        print(f"  ⚠️  Failed: {result.error_message}")

                        if job.attempts < self.max_retries:
                            wait_time = job.attempts * 2  # Exponential backoff
                            print(f"  Retrying in {wait_time}s...")
                            time.sleep(wait_time)

                except Exception as e:
                    job.error = str(e)
                    print(f"  ❌ Error: {e}")

                    if job.attempts < self.max_retries:
                        wait_time = job.attempts * 2
                        print(f"  Retrying in {wait_time}s...")
                        time.sleep(wait_time)

            # Mark as failed if all retries exhausted
            if job.status != BatchStatus.COMPLETED:
                job.status = BatchStatus.FAILED
                failed += 1
                print(f"  ❌ Failed after {job.attempts} attempts")

                if not continue_on_failure:
                    print("\n⚠️  Stopping batch due to failure (continue_on_failure=False)")
                    break

            # Delay before next download (unless it's the last one)
            if i < len(jobs) and job.status == BatchStatus.COMPLETED:
                time.sleep(self.delay_between_downloads)

        # Final summary
        print("\n" + "=" * 60)
        print("📊 BATCH DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total jobs:      {len(jobs)}")
        print(f"✅ Successful:   {successful}")
        print(f"❌ Failed:       {failed}")
        print(f"⏭️  Skipped:      {skipped}")
        print("=" * 60)

        return BatchSummary(
            total=len(jobs),
            successful=successful,
            failed=failed,
            skipped=skipped,
            jobs=jobs
        )

    def download_from_json(self, json_file: str,
                          continue_on_failure: bool = True) -> BatchSummary:
        """
        Download models from a JSON file.

        Expected JSON format:
        [
            {
                "model_id": 1091495,
                "model_name": "Better detailed pussy and anus",
                "version_id": null  // optional
            },
            ...
        ]

        Args:
            json_file: Path to JSON file
            continue_on_failure: Continue on failures

        Returns:
            BatchSummary with results
        """
        print(f"📄 Loading batch file: {json_file}")

        with open(json_file, 'r') as f:
            data = json.load(f)

        jobs = []
        for item in data:
            job = BatchJob(
                model_id=item['model_id'],
                model_name=item.get('model_name'),
                version_id=item.get('version_id'),
                max_retries=self.max_retries
            )
            jobs.append(job)

        return self.download_batch(jobs, continue_on_failure)

    def export_summary(self, summary: BatchSummary, output_file: str):
        """Export batch summary to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(summary.to_dict(), f, indent=2)

        print(f"\n📄 Summary exported to: {output_file}")


def main():
    """CLI interface for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Batch Civitai model downloader with retry logic'
    )
    parser.add_argument('input_json', help='JSON file with model list')
    parser.add_argument('--output-dir', help='Download directory')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum retry attempts (default: 3)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between downloads in seconds (default: 2.0)')
    parser.add_argument('--stop-on-failure', action='store_true',
                       help='Stop batch if a download fails')
    parser.add_argument('--export-summary', help='Export summary to JSON file')

    args = parser.parse_args()

    downloader = CivitaiBatchDownloader(
        download_dir=args.output_dir,
        max_retries=args.max_retries,
        delay_between_downloads=args.delay
    )

    summary = downloader.download_from_json(
        args.input_json,
        continue_on_failure=not args.stop_on_failure
    )

    if args.export_summary:
        downloader.export_summary(summary, args.export_summary)

    # Exit with failure if any downloads failed
    exit(0 if summary.failed == 0 else 1)


if __name__ == '__main__':
    main()
