#!/usr/bin/env python3
"""
Organize existing documentation files in /docs by moving them to appropriate subfolders.

This is a utility script for batch organization of existing documentation.
It runs in dry-run mode by default to show what would be moved.

Usage:
    python3 scripts/organize_existing_docs.py [--execute]

Options:
    --execute    Actually move files (default is dry-run)
"""

import sys
import os
import logging

# Add adws to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "adws"))

from adw_modules.doc_cleanup import organize_root_docs, create_folder_structure


def setup_logging():
    """Set up logging to both console and file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("organize_docs.log")
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger = setup_logging()

    # Check for execute flag
    dry_run = "--execute" not in sys.argv

    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No files will be moved")
        print("=" * 60)
        print("\nThis will show what WOULD be moved without actually moving anything.")
        print("To actually move files, run with --execute flag\n")
    else:
        print("=" * 60)
        print("EXECUTE MODE - Files will be moved")
        print("=" * 60)
        print("\nConfirm: This will move documentation files to subfolders.")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            return

    # Ensure folder structure exists
    logger.info("Ensuring folder structure exists...")
    create_folder_structure(logger)

    # Run organization
    logger.info("Starting documentation organization...")
    result = organize_root_docs(dry_run=dry_run, logger=logger)

    # Print summary
    print("\n" + "=" * 60)
    print("ORGANIZATION SUMMARY")
    print("=" * 60)
    print(f"\nSuccess: {result['success']}")
    print(f"Files moved: {result['files_moved']}")
    print(f"\n{result['summary']}")

    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  - {error}")

    if dry_run:
        print("\n" + "=" * 60)
        print("This was a DRY RUN - no files were actually moved")
        print("To execute these moves, run:")
        print("  python3 scripts/organize_existing_docs.py --execute")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Documentation organization completed")
        print("=" * 60)


if __name__ == "__main__":
    main()
