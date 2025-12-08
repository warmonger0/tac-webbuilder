#!/usr/bin/env python3
"""
Session Archiving System

Automatically organizes completed session documentation, moves files to appropriate
archives, maintains an archive index, and keeps the project root clean.

Usage:
    python scripts/archive_sessions.py --scan                    # Scan for archivable files
    python scripts/archive_sessions.py --archive --dry-run       # Show what would be archived
    python scripts/archive_sessions.py --archive                 # Archive files
    python scripts/archive_sessions.py --session 7 --archive     # Archive specific session
    python scripts/archive_sessions.py --update-index            # Update ARCHIVE_INDEX.md
"""

import argparse
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class SessionArchiver:
    """Manages archiving of session documentation files."""

    KEEP_IN_ROOT = [
        'README.md',
        'CLAUDE.md',
        '.claude/',
        'docs/',
        'app/',
        'scripts/',
        'archives/',
        'adws/',
        'db/',
        '.git/',
        '.venv/',
        'node_modules/',
    ]

    FILE_PATTERNS = [
        'SESSION_*.md',
        'TRACKING_*.md',
        '*_PROMPT.md',
        '*_REPORT.md',
        '*_COMPLETION*.md',
        '*_ANALYSIS*.md',
        '*_SUMMARY*.md',
        '*_AUDIT*.md',
    ]

    def __init__(self, root_path: Optional[Path] = None):
        """Initialize the archiver.

        Args:
            root_path: Project root path. Defaults to parent of scripts directory.
        """
        if root_path is None:
            self.root = Path(__file__).parent.parent
        else:
            self.root = Path(root_path)

        self.archive_root = self.root / 'archives'

    def scan_for_archivable_files(self, session_number: Optional[int] = None) -> List[Path]:
        """Find session files in project root that can be archived.

        Args:
            session_number: If provided, only return files for this session number

        Returns:
            List of file paths that can be archived
        """
        archivable = set()  # Use set to avoid duplicates

        for pattern in self.FILE_PATTERNS:
            files = self.root.glob(pattern)
            for filepath in files:
                # Skip if not in root directory
                if filepath.parent != self.root:
                    continue

                # Filter by session number if provided
                if session_number is not None:
                    file_session = self._extract_session_number(filepath)
                    if file_session != session_number:
                        continue

                if self._is_archivable(filepath):
                    archivable.add(filepath)

        return sorted(list(archivable))

    def _extract_session_number(self, filepath: Path) -> Optional[int]:
        """Extract session number from filename.

        Args:
            filepath: Path to file

        Returns:
            Session number if found, None otherwise
        """
        # Look for SESSION_N or SESSION_N.N patterns
        match = re.search(r'SESSION[_\s]+(\d+(?:\.\d+)?)', filepath.name, re.IGNORECASE)
        if match:
            try:
                # Handle SESSION_1.5 style
                num_str = match.group(1)
                if '.' in num_str:
                    return int(float(num_str))
                return int(num_str)
            except (ValueError, AttributeError):
                pass

        # Look for TRACKING_HANDOFF_SESSIONN
        match = re.search(r'SESSION(\d+)', filepath.name, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, AttributeError):
                pass

        return None

    def _is_archivable(self, filepath: Path) -> bool:
        """Check if file should be archived.

        Args:
            filepath: Path to file

        Returns:
            True if file should be archived, False otherwise
        """
        # Don't archive if in keep list
        for keep_pattern in self.KEEP_IN_ROOT:
            if keep_pattern in str(filepath):
                return False

        # Don't archive current tracking document (most recent)
        if 'TRACKING_HANDOFF' in filepath.name:
            if self._is_current_tracking(filepath):
                return False

        # Don't archive session prompts for incomplete sessions
        if 'PROMPT' in filepath.name and self._is_incomplete_session(filepath):
            return False

        return True

    def _is_current_tracking(self, filepath: Path) -> bool:
        """Check if this is the most recent tracking document.

        Args:
            filepath: Path to tracking file

        Returns:
            True if this is the current (most recent) tracking document
        """
        # Find all tracking documents
        all_tracking = list(self.root.glob('TRACKING_*.md'))

        if not all_tracking:
            return False

        # Get the most recent by modification time
        most_recent = max(all_tracking, key=lambda p: p.stat().st_mtime)

        return filepath == most_recent

    def _is_incomplete_session(self, filepath: Path) -> bool:
        """Check if session is incomplete (no completion report exists).

        Args:
            filepath: Path to session file

        Returns:
            True if session appears incomplete
        """
        session_num = self._extract_session_number(filepath)
        if session_num is None:
            return False

        # Look for completion indicators
        completion_patterns = [
            f'SESSION_{session_num}_COMPLETION*.md',
            f'SESSION_{session_num}_SUMMARY*.md',
            f'SESSION_{session_num}_REPORT*.md',
        ]

        for pattern in completion_patterns:
            if list(self.root.glob(pattern)):
                return False

        # Also check in archives
        for pattern in completion_patterns:
            if list(self.archive_root.rglob(pattern)):
                return False

        return True

    def categorize_file(self, filepath: Path) -> str:
        """Determine archive category for a file.

        Args:
            filepath: Path to file

        Returns:
            Category name (prompts, reports, sessions, tracking, misc)
        """
        name = filepath.name.upper()

        if 'PROMPT' in name:
            return 'prompts'
        elif any(kw in name for kw in ['REPORT', 'COMPLETION', 'SUMMARY', 'AUDIT', 'ANALYSIS']):
            return 'reports'
        elif name.startswith('SESSION_'):
            return 'sessions'
        elif name.startswith('TRACKING_'):
            return 'tracking'
        else:
            return 'misc'

    def archive_file(self, filepath: Path, dry_run: bool = False) -> Optional[Path]:
        """Move file to appropriate archive location.

        Args:
            filepath: Path to file to archive
            dry_run: If True, don't actually move files

        Returns:
            Destination path if successful, None otherwise
        """
        # Determine category
        category = self.categorize_file(filepath)

        # Extract date from filename or use file modification time
        file_date = self._extract_date(filepath)
        year = file_date.year

        # Determine destination directory
        if category == 'tracking':
            dest_dir = self.archive_root / 'tracking'
        else:
            dest_dir = self.archive_root / category / str(year)

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Add date suffix if not present
        if not re.search(r'\d{4}-\d{2}-\d{2}', filepath.name):
            new_name = filepath.stem + f'_{file_date.strftime("%Y-%m-%d")}' + filepath.suffix
        else:
            new_name = filepath.name

        dest_file = dest_dir / new_name

        # Handle name conflicts
        counter = 1
        while dest_file.exists():
            base = dest_file.stem
            suffix = dest_file.suffix
            dest_file = dest_dir / f"{base}_{counter}{suffix}"
            counter += 1

        if not dry_run:
            shutil.move(str(filepath), str(dest_file))

        return dest_file

    def _extract_date(self, filepath: Path) -> datetime:
        """Extract date from filename or use file modification time.

        Args:
            filepath: Path to file

        Returns:
            Date extracted from filename or file modification time
        """
        # Try to extract from filename (YYYY-MM-DD format)
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filepath.name)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                pass

        # Fall back to file modification time
        return datetime.fromtimestamp(filepath.stat().st_mtime)

    def _scan_archive(self) -> Dict[str, List[Path]]:
        """Scan archive directory for all files.

        Returns:
            Dictionary mapping categories to lists of archived files
        """
        archived = {
            'sessions': [],
            'reports': [],
            'prompts': [],
            'tracking': [],
            'misc': []
        }

        for category in archived.keys():
            category_path = self.archive_root / category
            if category_path.exists():
                archived[category].extend(category_path.rglob('*.md'))

        return archived

    def _extract_session_info(self, archived_files: Dict[str, List[Path]]) -> Dict[int, Dict]:
        """Extract session information from archived files.

        Args:
            archived_files: Dictionary of archived files by category

        Returns:
            Dictionary mapping session numbers to session info
        """
        sessions = {}

        # Collect all files with session numbers
        all_files = []
        for category, files in archived_files.items():
            all_files.extend([(f, category) for f in files])

        for filepath, category in all_files:
            session_num = self._extract_session_number(filepath)
            if session_num is None:
                continue

            if session_num not in sessions:
                sessions[session_num] = {
                    'number': session_num,
                    'date': self._extract_date(filepath),
                    'files': {}
                }

            if category not in sessions[session_num]['files']:
                sessions[session_num]['files'][category] = []

            sessions[session_num]['files'][category].append(filepath)

        return sessions

    def update_archive_index(self):
        """Generate ARCHIVE_INDEX.md with all archived files."""
        archived_files = self._scan_archive()
        sessions = self._extract_session_info(archived_files)

        # Sort sessions by number
        sorted_sessions = sorted(sessions.values(), key=lambda s: s['number'])

        # Generate index content
        index_content = "# Session Archive Index\n\n"
        index_content += f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Group by year
        years = {}
        for session in sorted_sessions:
            year = session['date'].year
            if year not in years:
                years[year] = []
            years[year].append(session)

        index_content += "## Sessions by Year\n\n"

        for year in sorted(years.keys(), reverse=True):
            year_sessions = years[year]
            index_content += f"### {year} ({len(year_sessions)} session{'s' if len(year_sessions) != 1 else ''})\n\n"

            for session in sorted(year_sessions, key=lambda s: s['number']):
                index_content += self._format_session_entry(session)
                index_content += "\n"

        # Add statistics
        index_content += self._generate_statistics(sorted_sessions)

        # Add search guide
        index_content += self._generate_search_guide()

        # Write index
        index_file = self.archive_root / 'ARCHIVE_INDEX.md'
        index_file.write_text(index_content)

        return index_file

    def _format_session_entry(self, session: Dict) -> str:
        """Format a session entry for the index.

        Args:
            session: Session info dictionary

        Returns:
            Formatted markdown entry
        """
        entry = f"#### Session {session['number']}\n"
        entry += f"- **Date:** {session['date'].strftime('%Y-%m-%d')}\n"
        entry += "- **Files:**\n"

        for category in ['sessions', 'reports', 'prompts', 'tracking']:
            if category in session['files']:
                for filepath in session['files'][category]:
                    rel_path = filepath.relative_to(self.archive_root)
                    entry += f"  - {category.title()}: [{filepath.name}]({rel_path})\n"

        return entry

    def _generate_statistics(self, sessions: List[Dict]) -> str:
        """Generate statistics section for index.

        Args:
            sessions: List of session info dictionaries

        Returns:
            Formatted statistics section
        """
        if not sessions:
            return "## Statistics\n\nNo sessions archived yet.\n\n"

        total_files = sum(
            len(files)
            for session in sessions
            for files in session['files'].values()
        )

        dates = [s['date'] for s in sessions]
        date_range = f"{min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}"

        stats = "## Statistics\n\n"
        stats += f"- Total sessions archived: {len(sessions)}\n"
        stats += f"- Total files archived: {total_files}\n"
        stats += f"- Date range: {date_range}\n"
        stats += "\n"

        return stats

    def _generate_search_guide(self) -> str:
        """Generate search guide section for index.

        Returns:
            Formatted search guide section
        """
        guide = "## Search\n\n"
        guide += "To find specific content:\n\n"
        guide += "```bash\n"
        guide += "# Search all archived files\n"
        guide += 'grep -r "pattern detection" archives/\n\n'
        guide += "# Find files for specific session\n"
        guide += 'find archives/ -name "*SESSION_7*"\n\n'
        guide += "# List all files in a year\n"
        guide += "ls archives/sessions/2025/\n"
        guide += "```\n"

        return guide

    def cleanup_old_files(self, days_old: int = 30, dry_run: bool = False) -> List[Path]:
        """Remove old files from root after archiving.

        Args:
            days_old: Remove files older than this many days
            dry_run: If True, don't actually remove files

        Returns:
            List of files that were (or would be) removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed = []

        for pattern in self.FILE_PATTERNS:
            for filepath in self.root.glob(pattern):
                # Skip if not in root
                if filepath.parent != self.root:
                    continue

                # Check if old enough
                file_date = datetime.fromtimestamp(filepath.stat().st_mtime)
                if file_date < cutoff_date:
                    # Check if archived
                    if self._is_archived(filepath):
                        removed.append(filepath)
                        if not dry_run:
                            filepath.unlink()

        return removed

    def _is_archived(self, filepath: Path) -> bool:
        """Check if a file has been archived.

        Args:
            filepath: Path to file in root

        Returns:
            True if file exists in archives
        """
        # Check all archive locations
        for archived_file in self.archive_root.rglob('*.md'):
            # Compare by name (may have date suffix added)
            if filepath.stem in archived_file.stem:
                return True

        return False

    def generate_report(self, files: List[Path], dry_run: bool = False) -> str:
        """Generate a report of archivable files.

        Args:
            files: List of files to archive
            dry_run: Whether this is a dry run

        Returns:
            Formatted report string
        """
        if not files:
            return "No archivable files found.\n"

        # Group by category
        by_category = {}
        for filepath in files:
            category = self.categorize_file(filepath)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(filepath)

        # Build report
        report = "=" * 80 + "\n"
        report += "SESSION ARCHIVING " + ("(DRY RUN) " if dry_run else "") + "SCAN\n"
        report += "=" * 80 + "\n\n"

        report += f"ARCHIVABLE FILES ({len(files)} found)\n\n"

        for category in sorted(by_category.keys()):
            files_in_cat = by_category[category]
            report += f"{category.title()} ({len(files_in_cat)}):\n"
            for filepath in sorted(files_in_cat):
                category_path = self.categorize_file(filepath)
                dest = f"archives/{category_path}/"
                if category_path != 'tracking':
                    file_date = self._extract_date(filepath)
                    dest += f"{file_date.year}/"
                report += f"  - {filepath.name} → {dest}\n"
            report += "\n"

        if dry_run:
            report += "Run with --archive (without --dry-run) to move files\n"

        return report


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Archive session documentation files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--scan', action='store_true',
                       help='Scan for archivable files')
    parser.add_argument('--archive', action='store_true',
                       help='Archive files (moves to archives/)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be archived without moving files')
    parser.add_argument('--update-index', action='store_true',
                       help='Update ARCHIVE_INDEX.md')
    parser.add_argument('--session', type=int,
                       help='Archive specific session number')
    parser.add_argument('--cleanup', type=int, metavar='DAYS',
                       help='Remove archived files older than DAYS from root')

    args = parser.parse_args()

    # Create archiver
    archiver = SessionArchiver()

    # Default to scan if no action specified
    if not any([args.scan, args.archive, args.update_index, args.cleanup]):
        args.scan = True

    # Scan and archive
    if args.scan or args.archive:
        files = archiver.scan_for_archivable_files(session_number=args.session)
        report = archiver.generate_report(files, dry_run=args.dry_run)
        print(report)

        if args.archive and not args.dry_run:
            print("Archiving files...")
            for filepath in files:
                dest = archiver.archive_file(filepath, dry_run=False)
                print(f"  Archived: {filepath.name} → {dest.relative_to(archiver.root)}")
            print(f"\n✅ Archived {len(files)} file{'s' if len(files) != 1 else ''}")

            # Auto-update index after archiving
            print("\nUpdating archive index...")
            index_file = archiver.update_archive_index()
            print(f"✅ Updated {index_file.relative_to(archiver.root)}")

    # Update index
    if args.update_index and not args.archive:
        print("Updating archive index...")
        index_file = archiver.update_archive_index()
        print(f"✅ Updated {index_file.relative_to(archiver.root)}")

    # Cleanup old files
    if args.cleanup:
        print(f"Cleaning up files older than {args.cleanup} days...")
        removed = archiver.cleanup_old_files(days_old=args.cleanup, dry_run=args.dry_run)
        if removed:
            for filepath in removed:
                status = "Would remove" if args.dry_run else "Removed"
                print(f"  {status}: {filepath.name}")
            print(f"\n✅ {len(removed)} file{'s' if len(removed) != 1 else ''} cleaned up")
        else:
            print("No old files to clean up")


if __name__ == '__main__':
    main()
