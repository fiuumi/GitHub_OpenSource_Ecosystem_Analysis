"""
GitHub Crawler - Storage Module

Handles data persistence with:
- JSON report generation (crawl_report.json)
- Incremental saving (records appended as crawled)
- CSV export for analysis compatibility
- Atomic writes (temp file + rename)
- Backup of existing files

Design Document Reference: Section 2.3 - Data Field Mapping
"""

import os
import json
import csv
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from ..models.repository import RepositoryData, CrawlReport
    from ..utils.logger import get_logger
    from ..utils.helpers import ensure_dir
except ImportError:
    import sys
    import os as os2
    sys.path.insert(0, os2.path.join(os2.path.dirname(__file__), '..'))
    from models.repository import RepositoryData, CrawlReport
    from utils.logger import get_logger
    from utils.helpers import ensure_dir


class Storage:
    """
    Manages persistence of crawl results to disk.
    """

    def __init__(self, output_dir: str, target_name: str = ""):
        """
        Initialize storage.

        Args:
            output_dir: Base output directory path
            target_name: Target identifier for subdirectory
        """
        self.output_dir = Path(output_dir)
        self.target_name = target_name
        self.logger = get_logger(__name__)

        # Create target subdirectory
        if target_name:
            self.target_dir = self.output_dir / target_name
        else:
            self.target_dir = self.output_dir

        ensure_dir(str(self.target_dir))

        # Incremental records buffer
        self._records: List[RepositoryData] = []
        self._flush_threshold: int = 10  # Auto-flush after N records

    def _get_report_path(self) -> Path:
        """Get path for crawl_report.json."""
        return self.target_dir / 'crawl_report.json'

    def _get_csv_path(self) -> Path:
        """Get path for CSV export."""
        return self.target_dir / 'crawl_report.csv'

    def _atomic_write(self, filepath: Path, content: str) -> None:
        """
        Write file atomically using temp file + rename.
        """
        temp_path = filepath.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # Atomic rename
            temp_path.replace(filepath)
        except Exception as e:
            self.logger.error(f"Failed to write {filepath}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def backup_existing(self) -> None:
        """Backup existing crawl_report.json if present."""
        report_path = self._get_report_path()
        if report_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = report_path.with_suffix(f'.{timestamp}.json.bak')
            shutil.copy2(str(report_path), str(backup_path))
            self.logger.info(f"Backed up existing report to {backup_path.name}")

    def save_record(self, record: RepositoryData) -> None:
        """
        Add a record to buffer. Auto-flushes when threshold reached.
        """
        self._records.append(record)

        if len(self._records) >= self._flush_threshold:
            self.flush()

    def flush(self) -> None:
        """
        Write all buffered records to disk.
        """
        if not self._records:
            return

        report_path = self._get_report_path()

        # Load existing report if present
        report = self._load_existing_report()

        # Add new records
        for record in self._records:
            report.add_record(record)

        report.total_pages_crawled += len(self._records)

        # Write updated report
        try:
            self._atomic_write(report_path, report.to_json())
            self.logger.debug(f"Flushed {len(self._records)} records (total: {len(report.records)})")
        except Exception as e:
            self.logger.error(f"Flush failed: {e}")

        # Clear buffer
        self._records = []

    def _load_existing_report(self) -> CrawlReport:
        """Load existing report or create new one."""
        report_path = self._get_report_path()
        if report_path.exists():
            try:
                return CrawlReport.load(str(report_path))
            except Exception as e:
                self.logger.warning(f"Failed to load existing report: {e}")

        return CrawlReport(
            target_name=self.target_name,
            target_url="",
        )

    def finalize_report(
        self,
        target_url: str = "",
        errors: Optional[List[str]] = None,
    ) -> CrawlReport:
        """
        Finalize and save the complete crawl report.

        Args:
            target_url: The seed URL that was crawled
            errors: List of error messages

        Returns:
            Completed CrawlReport
        """
        # Flush remaining records
        self.flush()

        # Load and finalize
        report = self._load_existing_report()
        report.target_url = target_url
        report.finalize()

        if errors:
            for err in errors:
                report.add_error(err)

        # Write final report
        report_path = self._get_report_path()
        try:
            self._atomic_write(report_path, report.to_json())
            self.logger.info(f"Report saved: {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to save final report: {e}")

        # Export CSV
        self._export_csv(report)

        return report

    def _export_csv(self, report: CrawlReport) -> None:
        """
        Export report records to CSV for easy analysis.
        """
        if not report.records:
            return

        csv_path = self._get_csv_path()

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                if not report.records:
                    return

                # Get field names from first record
                sample = report.records[0].to_dict()
                # Flatten keywords dict for CSV
                fieldnames = [k for k in sample.keys() if k != 'keywords']
                fieldnames.append('keywords_json')

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for record in report.records:
                    row = record.to_dict()
                    # Serialize keywords as JSON string
                    row['keywords_json'] = json.dumps(row.pop('keywords', {}))
                    writer.writerow(row)

            self.logger.info(f"CSV exported: {csv_path}")

        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Save crawl metadata to a separate file.
        """
        meta_path = self.target_dir / 'crawl_metadata.json'
        try:
            self._atomic_write(meta_path, json.dumps(metadata, indent=2, ensure_ascii=False))
        except Exception as e:
            self.logger.error(f"Metadata save failed: {e}")

    @property
    def record_count(self) -> int:
        """Total records saved (including buffered)."""
        existing = 0
        report_path = self._get_report_path()
        if report_path.exists():
            try:
                report = CrawlReport.load(str(report_path))
                existing = len(report.records)
            except Exception:
                pass
        return existing + len(self._records)

    def __repr__(self) -> str:
        return f"Storage(dir={self.target_dir}, records={self.record_count})"
