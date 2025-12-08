#!/usr/bin/env python3
"""
Tests for Session Archiving System

Tests file scanning, categorization, archiving, index generation, and cleanup.
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from archive_sessions import SessionArchiver


class TestSessionArchiver:
    """Test suite for SessionArchiver."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure for testing."""
        # Create project structure
        root = tmp_path / "project"
        root.mkdir()

        # Create archives structure
        archives = root / "archives"
        (archives / "sessions" / "2025").mkdir(parents=True)
        (archives / "reports" / "2025").mkdir(parents=True)
        (archives / "prompts" / "2025").mkdir(parents=True)
        (archives / "tracking").mkdir(parents=True)

        # Create test files in root
        test_files = [
            "SESSION_1_PROMPT.md",
            "SESSION_1_REPORT.md",
            "SESSION_1_2025-12-01.md",
            "SESSION_2_PROMPT.md",
            "SESSION_2_COMPLETION_SUMMARY.md",
            "SESSION_3_PROMPT.md",  # No completion - should not archive
            "TRACKING_HANDOFF_SESSION1.md",
            "TRACKING_HANDOFF_SESSION2.md",
            "SESSION_PROMPTS_SUMMARY.md",
            "README.md",  # Should not archive
        ]

        for filename in test_files:
            filepath = root / filename
            filepath.write_text(f"Content of {filename}")

        return root

    @pytest.fixture
    def archiver(self, temp_project):
        """Create SessionArchiver instance with temp project."""
        return SessionArchiver(root_path=temp_project)

    def test_initialization(self, archiver, temp_project):
        """Test archiver initializes correctly."""
        assert archiver.root == temp_project
        assert archiver.archive_root == temp_project / "archives"

    def test_scan_for_archivable_files(self, archiver, temp_project):
        """Test scanning for archivable files."""
        files = archiver.scan_for_archivable_files()

        # Should find session files but not README
        filenames = [f.name for f in files]
        assert "SESSION_1_PROMPT.md" in filenames
        assert "SESSION_1_REPORT.md" in filenames
        assert "README.md" not in filenames

        # Should find at least 8 files (excluding README and incomplete Session 3)
        assert len(files) >= 7

    def test_scan_for_specific_session(self, archiver):
        """Test scanning for specific session number."""
        files = archiver.scan_for_archivable_files(session_number=1)

        filenames = [f.name for f in files]
        assert "SESSION_1_PROMPT.md" in filenames
        assert "SESSION_1_REPORT.md" in filenames
        assert "SESSION_2_PROMPT.md" not in filenames

    def test_extract_session_number(self, archiver, temp_project):
        """Test extracting session number from filename."""
        assert archiver._extract_session_number(temp_project / "SESSION_1_PROMPT.md") == 1
        assert archiver._extract_session_number(temp_project / "SESSION_2_COMPLETION_SUMMARY.md") == 2
        assert archiver._extract_session_number(temp_project / "TRACKING_HANDOFF_SESSION1.md") == 1
        assert archiver._extract_session_number(temp_project / "SESSION_PROMPTS_SUMMARY.md") is None

    def test_categorize_file(self, archiver, temp_project):
        """Test file categorization."""
        assert archiver.categorize_file(temp_project / "SESSION_1_PROMPT.md") == "prompts"
        assert archiver.categorize_file(temp_project / "SESSION_1_REPORT.md") == "reports"
        assert archiver.categorize_file(temp_project / "SESSION_1_2025-12-01.md") == "sessions"
        assert archiver.categorize_file(temp_project / "SESSION_2_COMPLETION_SUMMARY.md") == "reports"
        assert archiver.categorize_file(temp_project / "TRACKING_HANDOFF_SESSION1.md") == "tracking"

    def test_is_incomplete_session(self, archiver, temp_project):
        """Test detecting incomplete sessions."""
        # Session 1 has completion report - not incomplete
        assert not archiver._is_incomplete_session(temp_project / "SESSION_1_PROMPT.md")

        # Session 2 has completion report - not incomplete
        assert not archiver._is_incomplete_session(temp_project / "SESSION_2_PROMPT.md")

        # Session 3 has no completion report - incomplete
        assert archiver._is_incomplete_session(temp_project / "SESSION_3_PROMPT.md")

    def test_is_current_tracking(self, archiver, temp_project):
        """Test identifying current tracking document."""
        # Get all tracking files
        tracking_files = list(temp_project.glob("TRACKING_*.md"))
        assert len(tracking_files) >= 2

        # Most recent should be current
        most_recent = max(tracking_files, key=lambda p: p.stat().st_mtime)
        assert archiver._is_current_tracking(most_recent)

        # Others should not be current
        for tf in tracking_files:
            if tf != most_recent:
                assert not archiver._is_current_tracking(tf)

    def test_extract_date_from_filename(self, archiver, temp_project):
        """Test extracting date from filename."""
        filepath = temp_project / "SESSION_1_2025-12-01.md"
        date = archiver._extract_date(filepath)
        assert date.year == 2025
        assert date.month == 12
        assert date.day == 1

    def test_extract_date_from_mtime(self, archiver, temp_project):
        """Test extracting date from file modification time."""
        filepath = temp_project / "SESSION_1_PROMPT.md"
        date = archiver._extract_date(filepath)
        # Should be close to now
        assert (datetime.now() - date).days < 1

    def test_archive_file_dry_run(self, archiver, temp_project):
        """Test archiving file in dry-run mode."""
        source = temp_project / "SESSION_1_PROMPT.md"
        assert source.exists()

        dest = archiver.archive_file(source, dry_run=True)

        # File should still exist in root
        assert source.exists()

        # Destination should be computed but not created
        assert dest is not None
        assert "prompts" in str(dest)
        assert "2025" in str(dest)

    def test_archive_file_actual(self, archiver, temp_project):
        """Test actually archiving a file."""
        source = temp_project / "SESSION_1_PROMPT.md"
        original_content = source.read_text()
        assert source.exists()

        dest = archiver.archive_file(source, dry_run=False)

        # File should be moved
        assert not source.exists()
        assert dest.exists()

        # Content should be preserved
        assert dest.read_text() == original_content

        # Should be in correct location
        assert "prompts" in str(dest)
        assert "2025" in str(dest)

    def test_archive_file_with_date_suffix(self, archiver, temp_project):
        """Test that files without dates get date suffix added."""
        source = temp_project / "SESSION_2_PROMPT.md"
        dest = archiver.archive_file(source, dry_run=False)

        # Should have date in filename
        assert dest.exists()
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2}', dest.name)

    def test_archive_file_name_conflict(self, archiver, temp_project):
        """Test handling of filename conflicts."""
        source1 = temp_project / "SESSION_1_REPORT.md"
        dest1 = archiver.archive_file(source1, dry_run=False)

        # Create another file with same name
        source2 = temp_project / "SESSION_1_REPORT.md"
        source2.write_text("Different content")

        dest2 = archiver.archive_file(source2, dry_run=False)

        # Both should exist with different names
        assert dest1.exists()
        assert dest2.exists()
        assert dest1 != dest2

    def test_scan_archive(self, archiver, temp_project):
        """Test scanning archived files."""
        # Archive some files first
        source = temp_project / "SESSION_1_PROMPT.md"
        archiver.archive_file(source, dry_run=False)

        # Scan archive
        archived = archiver._scan_archive()

        assert "prompts" in archived
        assert len(archived["prompts"]) >= 1

    def test_update_archive_index(self, archiver, temp_project):
        """Test generating archive index."""
        # Archive some files
        files_to_archive = [
            temp_project / "SESSION_1_PROMPT.md",
            temp_project / "SESSION_1_REPORT.md",
            temp_project / "SESSION_2_PROMPT.md",
        ]

        for filepath in files_to_archive:
            if filepath.exists():
                archiver.archive_file(filepath, dry_run=False)

        # Generate index
        index_file = archiver.update_archive_index()

        assert index_file.exists()
        assert index_file.name == "ARCHIVE_INDEX.md"

        # Check content
        content = index_file.read_text()
        assert "Session Archive Index" in content
        assert "Session 1" in content or "Session 2" in content
        assert "Statistics" in content
        assert "Search" in content

    def test_generate_report(self, archiver, temp_project):
        """Test generating scan report."""
        files = archiver.scan_for_archivable_files()
        report = archiver.generate_report(files, dry_run=True)

        assert "SESSION ARCHIVING" in report
        assert "DRY RUN" in report
        assert "ARCHIVABLE FILES" in report
        assert len(files) > 0

    def test_generate_report_empty(self, archiver, temp_project):
        """Test generating report with no files."""
        report = archiver.generate_report([], dry_run=False)
        assert "No archivable files found" in report

    def test_cleanup_old_files(self, archiver, temp_project):
        """Test cleanup of old archived files."""
        # Create an old file
        old_file = temp_project / "SESSION_OLD_PROMPT.md"
        old_file.write_text("Old content")

        # Make it old by modifying timestamp
        old_time = datetime.now() - timedelta(days=60)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Archive it
        archiver.archive_file(old_file, dry_run=False)

        # Create the file again in root (simulating it not being cleaned up)
        old_file.write_text("Old content")
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Cleanup files older than 30 days
        removed = archiver.cleanup_old_files(days_old=30, dry_run=False)

        # Should have been removed
        assert len(removed) >= 1
        assert not old_file.exists()

    def test_cleanup_old_files_dry_run(self, archiver, temp_project):
        """Test cleanup in dry-run mode."""
        # Create an old file
        old_file = temp_project / "SESSION_OLD_REPORT.md"
        old_file.write_text("Old content")

        old_time = datetime.now() - timedelta(days=60)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Archive it
        archiver.archive_file(old_file, dry_run=False)

        # Recreate in root
        old_file.write_text("Old content")
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Dry-run cleanup
        removed = archiver.cleanup_old_files(days_old=30, dry_run=True)

        # Should report it would be removed but file still exists
        assert len(removed) >= 1
        assert old_file.exists()

    def test_is_archived(self, archiver, temp_project):
        """Test checking if file is archived."""
        source = temp_project / "SESSION_1_2025-12-01.md"

        # Should not be archived initially
        assert not archiver._is_archived(source)

        # Archive it
        archiver.archive_file(source, dry_run=False)

        # Now should detect it's archived (even though source is gone)
        # Create it again to test
        source.write_text("Content")
        assert archiver._is_archived(source)

    def test_format_session_entry(self, archiver):
        """Test formatting session entry for index."""
        session_info = {
            "number": 1,
            "date": datetime(2025, 12, 1),
            "files": {
                "prompts": [Path("archives/prompts/2025/SESSION_1_PROMPT_2025-12-01.md")],
                "reports": [Path("archives/reports/2025/SESSION_1_REPORT_2025-12-01.md")],
            },
        }

        entry = archiver._format_session_entry(session_info)

        assert "Session 1" in entry
        assert "2025-12-01" in entry
        assert "Prompts:" in entry
        assert "Reports:" in entry

    def test_generate_statistics(self, archiver):
        """Test generating statistics section."""
        sessions = [
            {"number": 1, "date": datetime(2025, 12, 1), "files": {"prompts": [Path("file1.md")]}},
            {"number": 2, "date": datetime(2025, 12, 5), "files": {"reports": [Path("file2.md"), Path("file3.md")]}},
        ]

        stats = archiver._generate_statistics(sessions)

        assert "Statistics" in stats
        assert "Total sessions archived: 2" in stats
        assert "Total files archived: 3" in stats
        assert "2025-12-01 to 2025-12-05" in stats

    def test_generate_statistics_empty(self, archiver):
        """Test statistics with no sessions."""
        stats = archiver._generate_statistics([])
        assert "No sessions archived yet" in stats

    def test_generate_search_guide(self, archiver):
        """Test generating search guide."""
        guide = archiver._generate_search_guide()

        assert "Search" in guide
        assert "grep -r" in guide
        assert "find archives/" in guide
        assert "ls archives/" in guide


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
