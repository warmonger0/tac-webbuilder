#!/usr/bin/env python3
"""
Test script for multi-phase file upload functionality.
Parses the test markdown file and submits it to the backend API.
"""
import json
import re
import sys
from pathlib import Path

import requests


def parse_phases(markdown_content: str) -> list[dict]:
    """Parse markdown content to extract phases (similar to frontend parser)."""
    # Phase header regex: matches "## Phase 1:", "## Phase One:", etc.
    PHASE_HEADER_REGEX = r'^(#{1,6})\s*[Pp]hase\s+(\d+|[Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive|[Ss]ix|[Ss]even|[Ee]ight|[Nn]ine|[Tt]en)\s*[:\-]?\s*(.*)$'

    lines = markdown_content.split('\n')
    phases = []
    current_phase = None
    phase_position = 0

    for i, line in enumerate(lines):
        match = re.match(PHASE_HEADER_REGEX, line)

        if match:
            # Save previous phase if it exists
            if current_phase and 'start_line' in current_phase:
                current_phase['end_line'] = i - 1
                current_phase['content'] = '\n'.join(
                    lines[current_phase['start_line'] + 1:i]
                ).strip()
                phases.append(current_phase)

            # Start new phase
            phase_position += 1
            phase_num_text = match.group(2)
            raw_title = match.group(3).strip() if match.group(3) else ''
            title = re.sub(r'^[:\-]\s*', '', raw_title).strip() or f'Phase {phase_position}'

            # Convert word numbers to integers
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
            try:
                phase_number = int(phase_num_text)
            except ValueError:
                phase_number = word_to_num.get(phase_num_text.lower(), phase_position)

            current_phase = {
                'number': phase_number,
                'title': title,
                'content': '',
                'external_docs': [],  # Note: Using snake_case as per backend model
                'start_line': i
            }

    # Save last phase
    if current_phase and 'start_line' in current_phase:
        current_phase['end_line'] = len(lines) - 1
        current_phase['content'] = '\n'.join(
            lines[current_phase['start_line'] + 1:]
        ).strip()
        phases.append(current_phase)

    # Clean up temporary fields
    for phase in phases:
        phase.pop('start_line', None)
        phase.pop('end_line', None)

    return phases


def test_file_upload(file_path: str, backend_url: str = "http://localhost:8000"):
    """Test multi-phase file upload."""
    print(f"📄 Reading test file: {file_path}")

    # Read markdown file
    try:
        with open(file_path, 'r') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        return False

    print(f"✓ File read successfully ({len(markdown_content)} characters)")

    # Parse phases
    print("\n🔍 Parsing phases...")
    phases = parse_phases(markdown_content)

    if not phases:
        print("❌ Error: No phases found in markdown file")
        return False

    print(f"✓ Found {len(phases)} phases:")
    for phase in phases:
        print(f"  - Phase {phase['number']}: {phase['title']}")

    # Prepare request data
    request_data = {
        "nl_input": f"Multi-phase test workflow from {Path(file_path).name}",
        "project_path": "/Users/Warmonger0/tac/tac-webbuilder",
        "auto_post": False,  # Don't auto-post, we want to see preview first
        "phases": phases
    }

    # Submit to backend
    print(f"\n🚀 Submitting to backend API: {backend_url}/api/v1/request")
    try:
        response = requests.post(
            f"{backend_url}/api/v1/request",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()

        print("✅ Upload successful!")
        print(f"\nResponse:")
        print(f"  Request ID: {result.get('request_id')}")
        print(f"  Status: {result.get('status')}")

        if 'child_issues' in result:
            print(f"\n📋 Child Issues Created:")
            for child in result['child_issues']:
                issue_num = child.get('issue_number')
                phase_num = child.get('phase_number')
                queue_id = child.get('queue_id')
                status = f"Issue #{issue_num}" if issue_num else "Queued"
                print(f"  - Phase {phase_num}: {status} (Queue ID: {queue_id})")

        print(f"\n✓ Check Hopper Queue 'In Progress' tab at http://localhost:5173")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to backend at {backend_url}")
        print("   Make sure the backend server is running on port 8000")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    file_path = "/tmp/test_hopper_queue.md"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    success = test_file_upload(file_path)
    sys.exit(0 if success else 1)
