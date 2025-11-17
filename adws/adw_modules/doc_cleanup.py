"""
Documentation cleanup module for ADW workflows.

Organizes documentation files after successful PR merge by:
1. Classifying documents by type (architecture, guide, implementation, etc.)
2. Moving them to appropriate subfolders in /docs
3. Archiving specs and issue-related docs
4. Preserving git history using git mv

This module is designed to never fail the ship workflow - all errors are logged
as warnings and the workflow continues.
"""

import os
import re
import subprocess
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime

from .state import ADWState
from .github import fetch_issue, extract_repo_path, get_repo_url


# Document type classification patterns
DOC_PATTERNS = {
    "architecture": [
        r".*_ARCHITECTURE\.md$",
        r".*_TECHNICAL_OVERVIEW\.md$",
        r".*_DESIGN\.md$",
    ],
    "implementation": [
        r".*_IMPLEMENTATION(_PLAN)?\.md$",
        r".*_PLAN\.md$",
    ],
    "guide": [
        r".*_GUIDE\.md$",
        r".*_QUICK_START\.md$",
        r".*_SETUP\.md$",
        r".*_USAGE.*\.md$",
        r".*_EXAMPLES\.md$",
        r"HOW_TO_.*\.md$",
    ],
    "analysis": [
        r".*_ANALYSIS\.md$",
        r".*_INVESTIGATION\.md$",
    ],
    "summary": [
        r".*_SUMMARY\.md$",
        r".*_COMPLETION\.md$",
        r".*_HANDOFF\.md$",
        r".*_STATUS\.md$",
    ],
    "phase": [
        r"PHASE_\d+.*\.md$",
        r".*_PHASE_\d+.*\.md$",
    ],
}

# Core docs that should stay in /docs root
CORE_DOCS = {
    "api.md",
    "architecture.md",
    "cli.md",
    "configuration.md",
    "examples.md",
    "troubleshooting.md",
    "web-ui.md",
    "playwright-mcp.md",
    "README.md",
    "adw-optimization.md",
    "INVERTED_CONTEXT_FLOW.md",
}

# Folder structure
DOCS_ROOT = "docs"
FOLDER_STRUCTURE = {
    "architecture": "Architecture",
    "implementation": "Implementation Plans",
    "guide": "Guides",
    "analysis": "Analysis",
    "archived": "Archived Issues",
    "features": "features",
}


def classify_document(file_path: str) -> str:
    """
    Classify a document based on naming patterns.

    Args:
        file_path: Path to the document file

    Returns:
        Document type: 'architecture', 'implementation', 'guide', 'analysis',
                      'summary', 'phase', or 'other'
    """
    filename = os.path.basename(file_path)

    # Check if it's a core doc that should stay in root
    if filename in CORE_DOCS:
        return "core"

    # Check against patterns
    for doc_type, patterns in DOC_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return doc_type

    return "other"


def get_issue_title_slug(issue_number: str, logger: Optional[logging.Logger] = None) -> str:
    """
    Get slugified issue title from GitHub.

    Args:
        issue_number: GitHub issue number
        logger: Optional logger instance

    Returns:
        Slugified title or empty string if unable to fetch
    """
    try:
        repo_url = get_repo_url()
        repo_path = extract_repo_path(repo_url)
        issue = fetch_issue(issue_number, repo_path)

        # Slugify title
        title = issue.title.lower()
        title = re.sub(r'[^\w\s-]', '', title)
        title = re.sub(r'[-\s]+', '-', title)
        title = title[:50]  # Limit length

        return title
    except Exception as e:
        if logger:
            logger.warning(f"Could not fetch issue title: {e}")
        return ""


def get_cleanup_destination(
    file_path: str,
    issue_number: Optional[str] = None,
    adw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> Optional[str]:
    """
    Determine destination path for a document.

    Args:
        file_path: Current path to the document
        issue_number: Optional GitHub issue number for issue-specific cleanup
        adw_id: Optional ADW ID for tracking
        logger: Optional logger instance

    Returns:
        Destination path or None if document should stay in place
    """
    doc_type = classify_document(file_path)

    # Core docs stay in root
    if doc_type == "core":
        return None

    # Issue-specific cleanup
    if issue_number and adw_id:
        # Check if this doc is related to the issue
        filename = os.path.basename(file_path)

        # Summaries and implementation plans for this issue go to archived
        if doc_type in ["summary", "implementation", "phase"]:
            # Create issue-specific folder
            title_slug = get_issue_title_slug(issue_number, logger)
            issue_folder = f"issue-{issue_number}"
            if title_slug:
                issue_folder += f"-{title_slug}"

            dest_dir = os.path.join(DOCS_ROOT, FOLDER_STRUCTURE["archived"], issue_folder)
            return os.path.join(dest_dir, filename)

    # General cleanup by type
    if doc_type in FOLDER_STRUCTURE:
        dest_dir = os.path.join(DOCS_ROOT, FOLDER_STRUCTURE[doc_type])
        return os.path.join(dest_dir, os.path.basename(file_path))

    # Don't move if we don't know where it should go
    return None


def is_git_tracked(file_path: str) -> bool:
    """
    Check if a file is tracked by git.

    Args:
        file_path: Path to check

    Returns:
        True if file is tracked by git
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", file_path],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def move_file_with_git(
    src: str,
    dest: str,
    logger: logging.Logger,
    dry_run: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Move a file preserving git history.

    Args:
        src: Source file path
        dest: Destination file path
        logger: Logger instance
        dry_run: If True, don't actually move files

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(dest)

        if dry_run:
            logger.info(f"[DRY RUN] Would move: {src} -> {dest}")
            return True, None

        # Create destination directory
        os.makedirs(dest_dir, exist_ok=True)

        # Use git mv if file is tracked
        if is_git_tracked(src):
            result = subprocess.run(
                ["git", "mv", src, dest],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                logger.info(f"Moved (git): {src} -> {dest}")
                return True, None
            else:
                error = f"git mv failed: {result.stderr}"
                logger.error(error)
                return False, error
        else:
            # Use regular mv for untracked files
            import shutil
            shutil.move(src, dest)
            logger.info(f"Moved: {src} -> {dest}")
            return True, None

    except Exception as e:
        error = f"Error moving file: {e}"
        logger.error(error)
        return False, error


def cleanup_adw_documentation(
    issue_number: str,
    adw_id: str,
    state: ADWState,
    logger: logging.Logger,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Clean up documentation after successful ADW workflow ship.

    This function:
    1. Moves specs from /specs/ to archived issues folder
    2. Moves implementation plans and summaries to archived issues folder
    3. Updates state with cleanup metadata
    4. Never fails - logs warnings instead

    Args:
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        state: ADW state object
        logger: Logger instance
        dry_run: If True, don't actually move files

    Returns:
        Dictionary with cleanup results:
        {
            "success": bool,
            "files_moved": int,
            "summary": str,
            "errors": List[str],
            "moves": List[Dict[str, str]]
        }
    """
    result = {
        "success": True,
        "files_moved": 0,
        "summary": "",
        "errors": [],
        "moves": [],
    }

    try:
        logger.info(f"Starting documentation cleanup for issue #{issue_number}, ADW {adw_id}")

        # Get issue title for folder name
        title_slug = get_issue_title_slug(issue_number, logger)
        issue_folder = f"issue-{issue_number}"
        if title_slug:
            issue_folder += f"-{title_slug}"

        archived_dir = os.path.join(DOCS_ROOT, FOLDER_STRUCTURE["archived"], issue_folder)

        # 1. Move spec files from /specs/
        spec_file = state.get("plan_file")
        if spec_file and os.path.exists(spec_file):
            # Create specs subdirectory in archived folder
            specs_dir = os.path.join(archived_dir, "specs")
            dest = os.path.join(specs_dir, os.path.basename(spec_file))

            success, error = move_file_with_git(spec_file, dest, logger, dry_run)
            if success:
                result["files_moved"] += 1
                result["moves"].append({
                    "src": spec_file,
                    "dest": dest,
                    "type": "spec"
                })

                # Update state with new path
                if not dry_run:
                    state.update(plan_file=dest)
                    logger.info(f"Updated state.plan_file: {spec_file} -> {dest}")
            else:
                result["errors"].append(f"Failed to move spec: {error}")

        # 2. Look for implementation plans in /docs root
        docs_root_files = []
        if os.path.exists(DOCS_ROOT):
            docs_root_files = [
                os.path.join(DOCS_ROOT, f)
                for f in os.listdir(DOCS_ROOT)
                if f.endswith(".md") and os.path.isfile(os.path.join(DOCS_ROOT, f))
            ]

        # Filter for docs related to this issue/adw
        for doc_file in docs_root_files:
            filename = os.path.basename(doc_file)

            # Skip core docs
            if filename in CORE_DOCS:
                continue

            # Check if doc mentions this issue or adw_id
            doc_type = classify_document(doc_file)

            # Move implementation plans, summaries, and phase docs
            if doc_type in ["implementation", "summary", "phase"]:
                # Check if it's related to this issue
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Just check first 500 chars

                    # Check for issue number or adw_id in content
                    if issue_number in content or adw_id in content or \
                       f"issue-{issue_number}" in filename.lower():
                        dest = os.path.join(archived_dir, filename)

                        success, error = move_file_with_git(doc_file, dest, logger, dry_run)
                        if success:
                            result["files_moved"] += 1
                            result["moves"].append({
                                "src": doc_file,
                                "dest": dest,
                                "type": doc_type
                            })
                        else:
                            result["errors"].append(f"Failed to move {filename}: {error}")
                except Exception as e:
                    logger.warning(f"Could not read {doc_file}: {e}")

        # 3. Create README in archived folder
        if result["files_moved"] > 0 and not dry_run:
            readme_path = os.path.join(archived_dir, "README.md")
            if not os.path.exists(readme_path):
                try:
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Issue #{issue_number}\n\n")
                        f.write(f"**ADW ID:** {adw_id}\n")
                        f.write(f"**Archived:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
                        f.write(f"## Documentation\n\n")

                        for move in result["moves"]:
                            rel_path = os.path.relpath(move["dest"], archived_dir)
                            f.write(f"- [{os.path.basename(move['dest'])}]({rel_path})\n")

                    logger.info(f"Created README at {readme_path}")
                except Exception as e:
                    logger.warning(f"Could not create README: {e}")

        # 4. Update summary
        if result["files_moved"] > 0:
            result["summary"] = f"- Archived {result['files_moved']} files to `{archived_dir}`\n"

            # Group by type
            by_type = {}
            for move in result["moves"]:
                move_type = move["type"]
                by_type[move_type] = by_type.get(move_type, 0) + 1

            for move_type, count in by_type.items():
                result["summary"] += f"  - {count} {move_type} file(s)\n"
        else:
            result["summary"] = "- No files needed cleanup"

        # 5. Update state
        if not dry_run:
            cleanup_metadata = {
                "timestamp": datetime.now().isoformat(),
                "files_moved": result["files_moved"],
                "archived_to": archived_dir,
                "moves": result["moves"],
            }
            state.update(cleanup_metadata=cleanup_metadata)

        logger.info(f"Cleanup completed: {result['files_moved']} files moved")

    except Exception as e:
        error_msg = f"Unexpected error during cleanup: {e}"
        logger.error(error_msg)
        result["success"] = False
        result["errors"].append(error_msg)

    return result


def organize_root_docs(
    dry_run: bool = True,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Organize all loose docs in /docs root by moving them to appropriate subfolders.

    This is a batch utility for cleaning up existing documentation.

    Args:
        dry_run: If True, don't actually move files (default: True)
        logger: Optional logger instance

    Returns:
        Dictionary with organization results
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        "success": True,
        "files_moved": 0,
        "summary": "",
        "errors": [],
        "moves": [],
    }

    try:
        logger.info("Starting batch documentation organization")

        # Get all .md files in /docs root
        docs_root_files = []
        if os.path.exists(DOCS_ROOT):
            docs_root_files = [
                os.path.join(DOCS_ROOT, f)
                for f in os.listdir(DOCS_ROOT)
                if f.endswith(".md") and os.path.isfile(os.path.join(DOCS_ROOT, f))
            ]

        # Classify and move each file
        for doc_file in docs_root_files:
            dest = get_cleanup_destination(doc_file, logger=logger)

            if dest and dest != doc_file:
                success, error = move_file_with_git(doc_file, dest, logger, dry_run)

                if success:
                    result["files_moved"] += 1
                    doc_type = classify_document(doc_file)
                    result["moves"].append({
                        "src": doc_file,
                        "dest": dest,
                        "type": doc_type
                    })
                else:
                    result["errors"].append(f"Failed to move {doc_file}: {error}")

        # Generate summary
        if result["files_moved"] > 0:
            result["summary"] = f"Organized {result['files_moved']} files:\n"

            # Group by destination folder
            by_folder = {}
            for move in result["moves"]:
                folder = os.path.dirname(move["dest"])
                by_folder[folder] = by_folder.get(folder, 0) + 1

            for folder, count in by_folder.items():
                result["summary"] += f"  - {count} file(s) → {folder}\n"
        else:
            result["summary"] = "No files needed organization"

        logger.info(f"Organization completed: {result['files_moved']} files would be moved")

    except Exception as e:
        error_msg = f"Unexpected error during organization: {e}"
        logger.error(error_msg)
        result["success"] = False
        result["errors"].append(error_msg)

    return result


def create_folder_structure(logger: Optional[logging.Logger] = None) -> bool:
    """
    Create the documentation folder structure with README files.

    Args:
        logger: Optional logger instance

    Returns:
        True if successful
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        # Create folders
        folders = {
            "Architecture": "System architecture and technical design documents",
            "Guides": "How-to guides, quick starts, and setup instructions",
            "Implementation Plans": "Feature planning and implementation plan documents",
            "Analysis": "Research, investigation, and analysis documents",
        }

        for folder, description in folders.items():
            folder_path = os.path.join(DOCS_ROOT, folder)

            # Create folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                logger.info(f"Created folder: {folder_path}")

            # Create README if it doesn't exist
            readme_path = os.path.join(folder_path, "README.md")
            if not os.path.exists(readme_path):
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {folder}\n\n")
                    f.write(f"{description}\n\n")
                    f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d')}\n")

                logger.info(f"Created README: {readme_path}")

        return True

    except Exception as e:
        logger.error(f"Error creating folder structure: {e}")
        return False
