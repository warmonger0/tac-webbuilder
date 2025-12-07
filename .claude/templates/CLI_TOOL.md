# Template: CLI Tool

## File Location
`scripts/<tool_name>.py`

## Standard Structure

```python
#!/usr/bin/env python3
"""
<Tool Name> CLI

<One-line description>

Usage:
    python scripts/<tool_name>.py
    python scripts/<tool_name>.py --option value
    python scripts/<tool_name>.py --help
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.server.services.<service>_service import <Service>


class <ToolName>CLI:
    """CLI interface for <functionality>."""

    def __init__(self):
        self.service = <Service>()

    def command_action(self, args):
        """Execute main action."""
        # Implementation here
        print(f"Executing action with {args}")

    def show_statistics(self):
        """Display statistics."""
        stats = self.service.get_statistics()

        print("\n" + "="*80)
        print("<TOOL NAME> STATISTICS")
        print("="*80)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("="*80 + "\n")

    def interactive_mode(self):
        """Run interactive mode."""
        print("\nEntering interactive mode...")
        print("Commands: [a]ction, [s]tats, [q]uit\n")

        while True:
            choice = input("Your choice: ").lower().strip()

            if choice == 'a':
                # Perform action
                pass
            elif choice == 's':
                self.show_statistics()
            elif choice == 'q':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Try again.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='<Tool description>',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Common arguments
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    # Specific arguments
    parser.add_argument(
        '--option',
        type=str,
        help='Option description'
    )

    args = parser.parse_args()

    # Set up logging
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)

    # Initialize CLI
    cli = <ToolName>CLI()

    # Execute based on arguments
    try:
        if args.stats:
            cli.show_statistics()
        elif args.interactive:
            cli.interactive_mode()
        else:
            cli.command_action(args)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
```

## Make Executable

```bash
chmod +x scripts/<tool_name>.py
```

## Usage Patterns

**Simple Command:**
```python
def simple_action(self):
    result = self.service.perform_action()
    print(f"Result: {result}")
```

**Interactive Confirmation:**
```python
def confirm_action(self, prompt: str) -> bool:
    response = input(f"{prompt} [y/N]: ").lower().strip()
    return response in ['y', 'yes']
```

**Progress Display:**
```python
def process_items(self, items):
    total = len(items)
    for i, item in enumerate(items, 1):
        print(f"Processing {i}/{total}...", end='\r')
        # Process item
    print(f"Completed {total}/{total}")
```

**JSON Output Mode:**
```python
parser.add_argument('--json', action='store_true', help='Output as JSON')

if args.json:
    print(json.dumps(result, indent=2))
else:
    print(f"Human-readable: {result}")
```

**Batch Processing:**
```python
def process_batch(self, limit: int = 100):
    items = self.service.get_all(limit=limit)

    for i, item in enumerate(items, 1):
        print(f"\n--- Item {i}/{len(items)} ---")
        # Process each item
```

## Testing CLI Tool

```bash
# Show help
python scripts/<tool_name>.py --help

# Run with stats
python scripts/<tool_name>.py --stats

# Run interactively
python scripts/<tool_name>.py --interactive

# Run with verbose logging
python scripts/<tool_name>.py --verbose
```

## Common Argument Patterns

**File Input:**
```python
parser.add_argument('--input', type=str, help='Input file path')

# Validate file exists
if args.input and not Path(args.input).exists():
    print(f"Error: File not found: {args.input}")
    sys.exit(1)
```

**Date Range:**
```python
from datetime import datetime

parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')

# Parse dates
start = datetime.fromisoformat(args.start_date) if args.start_date else None
```

**Enum Choices:**
```python
parser.add_argument(
    '--status',
    choices=['pending', 'approved', 'rejected'],
    help='Filter by status'
)
```
