#!/usr/bin/env python3
"""
Extract individual workflows from phase detailed files.

This script reads all PHASE_*_DETAILED.md files and extracts each workflow
into a separate markdown file.
"""

import re
from pathlib import Path
from typing import List, Tuple


def extract_workflows(phase_file: Path) -> List[Tuple[str, str, str]]:
    """
    Extract workflows from a phase file.

    Returns:
        List of (workflow_id, title, content) tuples
    """
    content = phase_file.read_text()
    workflows = []

    # Pattern to match workflow headers (## or ###)
    workflow_pattern = r'^(#{2,3})\s+Workflow\s+([\w.]+):\s+(.+?)$'

    lines = content.split('\n')
    current_workflow = None
    current_content = []
    current_level = None

    for i, line in enumerate(lines):
        match = re.match(workflow_pattern, line)

        if match:
            # Save previous workflow if exists
            if current_workflow:
                workflows.append((
                    current_workflow[0],  # workflow_id
                    current_workflow[1],  # title
                    '\n'.join(current_content)
                ))

            # Start new workflow
            level = match.group(1)  # ## or ###
            workflow_id = match.group(2)  # e.g., "1.1" or "3A.2"
            title = match.group(3).strip()  # e.g., "Create WebSocket Manager Module"

            current_workflow = (workflow_id, title)
            current_content = [line]  # Include the header
            current_level = len(level)  # 2 for ##, 3 for ###

        elif current_workflow:
            # Check if we've hit the next workflow or major section
            if line.startswith('##'):
                # Check if it's a same-level or higher-level heading
                heading_level = len(re.match(r'^(#+)', line).group(1))
                if heading_level <= current_level:
                    # End current workflow
                    workflows.append((
                        current_workflow[0],
                        current_workflow[1],
                        '\n'.join(current_content)
                    ))
                    current_workflow = None
                    current_content = []
                    current_level = None
                    continue

            # Add line to current workflow
            current_content.append(line)

    # Don't forget the last workflow
    if current_workflow:
        workflows.append((
            current_workflow[0],
            current_workflow[1],
            '\n'.join(current_content)
        ))

    return workflows


def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filename."""
    # Remove or replace invalid characters
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text[:50]  # Limit length


def main():
    # Get the directory containing the script
    script_dir = Path(__file__).parent
    output_dir = script_dir / "workflows"
    output_dir.mkdir(exist_ok=True)

    # Find all PHASE_*_DETAILED.md files
    phase_files = sorted(script_dir.glob("PHASE_*_DETAILED.md"))

    if not phase_files:
        print("No PHASE_*_DETAILED.md files found!")
        return

    total_workflows = 0

    for phase_file in phase_files:
        print(f"\nProcessing {phase_file.name}...")
        phase_num = re.search(r'PHASE_(\d+)', phase_file.name).group(1)

        workflows = extract_workflows(phase_file)
        print(f"  Found {len(workflows)} workflows")

        for workflow_id, title, content in workflows:
            # Create filename
            safe_title = sanitize_filename(title)
            filename = f"PHASE{phase_num}_WORKFLOW_{workflow_id}_{safe_title}.md"
            output_path = output_dir / filename

            # Write workflow to file
            output_path.write_text(content)
            print(f"    ✓ Extracted: {filename}")
            total_workflows += 1

    print(f"\n✅ Total workflows extracted: {total_workflows}")
    print(f"📁 Output directory: {output_dir}")


if __name__ == "__main__":
    main()
