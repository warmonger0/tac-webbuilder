#!/usr/bin/env python3
"""
Prompt Generator - Session 1: Basic Template Substitution

Generates implementation prompts from planned_features database using template.

Usage:
    python3 scripts/generate_prompt.py --list              # List all features
    python3 scripts/generate_prompt.py 104                 # Generate prompt for feature 104
    python3 scripts/generate_prompt.py 49                  # Generate prompt for bug 49

Session 1 Scope:
- Basic template substitution (type, ID, title, priority, hours)
- Filename generation (QUICK_WIN vs TYPE logic)
- Query planned_features database
- NO codebase analysis (Session 2)
"""

import argparse
import re
import sys
from pathlib import Path

# Add app/server to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.planned_features_service import PlannedFeaturesService


class PromptGenerator:
    """Generate implementation prompts from planned features."""

    def __init__(self):
        """Initialize generator with service and template."""
        self.service = PlannedFeaturesService()
        self.template_path = Path(__file__).parent.parent / ".claude" / "templates" / "IMPLEMENTATION_PROMPT_TEMPLATE.md"

        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        self.template = self.template_path.read_text()

    def list_features(self, status: str | None = None, item_type: str | None = None):
        """
        List all planned features with optional filtering.

        Args:
            status: Filter by status ('planned', 'in_progress', 'completed', 'cancelled')
            item_type: Filter by type ('session', 'feature', 'bug', 'enhancement')
        """
        features = self.service.get_all(status=status, item_type=item_type)

        if not features:
            print("No features found matching criteria.")
            return

        print(f"\n{'ID':<5} {'Type':<12} {'Priority':<10} {'Hours':<8} {'Status':<12} Title")
        print("-" * 100)

        for feature in features:
            hours = f"{feature.estimated_hours:.2f}" if feature.estimated_hours else "TBD"
            priority = feature.priority or "medium"
            print(f"{feature.id:<5} {feature.item_type:<12} {priority:<10} {hours:<8} {feature.status:<12} {feature.title}")

        print(f"\nTotal: {len(features)} features")

    def generate(self, feature_id: int) -> str:
        """
        Generate implementation prompt for a feature.

        Args:
            feature_id: The ID of the feature to generate prompt for

        Returns:
            Generated prompt content

        Raises:
            ValueError: If feature not found
        """
        feature = self.service.get_by_id(feature_id)

        if not feature:
            raise ValueError(f"Feature #{feature_id} not found in database")

        # Fill template with feature data
        prompt_content = self._fill_template(feature)

        # Generate filename
        filename = self._generate_filename(feature)

        # Write to file
        output_path = Path.cwd() / filename
        output_path.write_text(prompt_content)

        print(f"\n✅ Generated prompt: {filename}")
        print(f"   Feature: #{feature.id} - {feature.title}")
        print(f"   Type: {feature.item_type.capitalize()}")
        print(f"   Priority: {feature.priority or 'Medium'}")
        print(f"   Estimated: {feature.estimated_hours}h" if feature.estimated_hours else "   Estimated: TBD")

        return prompt_content

    def _fill_template(self, feature) -> str:
        """
        Fill template placeholders with feature data.

        Session 1: Basic substitution only.
        Session 2: Will add codebase analysis.

        Args:
            feature: PlannedFeature object

        Returns:
            Filled template content
        """
        # Basic replacements for Task Summary section (lines 1-8)
        replacements = {
            "[Type]": feature.item_type.capitalize(),
            "[ID]": str(feature.id),
            "[Title]": feature.title,
            "[One-line description]": feature.description or feature.title,
            "[High/Medium/Low]": (feature.priority or "Medium").capitalize(),
            "[Bug/Feature/Enhancement/Session]": feature.item_type.capitalize(),
            "[X hours]": f"{feature.estimated_hours}" if feature.estimated_hours else "TBD",
        }

        # Apply replacements
        content = self.template
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        return content

    def _generate_filename(self, feature) -> str:
        """
        Generate filename based on feature type and hours.

        Logic:
        - QUICK_WIN if estimated_hours <= 2.0
        - TYPE_ID_slug otherwise

        Args:
            feature: PlannedFeature object

        Returns:
            Generated filename
        """
        # Create slug from title
        slug = self._slugify(feature.title)

        # Determine prefix based on hours
        if feature.estimated_hours and feature.estimated_hours <= 2.0:
            prefix = "QUICK_WIN"
        else:
            prefix = feature.item_type.upper()

        # Format: PREFIX_ID_slug.md
        filename = f"{prefix}_{feature.id}_{slug}.md"

        return filename

    def _slugify(self, text: str) -> str:
        """
        Convert text to slug format.

        Args:
            text: Text to slugify

        Returns:
            Slugified text (lowercase, underscores, alphanumeric only)
        """
        # Convert to lowercase
        text = text.lower()

        # Replace spaces and special chars with underscores
        text = re.sub(r'[^a-z0-9]+', '_', text)

        # Remove leading/trailing underscores
        text = text.strip('_')

        # Limit length to 50 chars
        text = text[:50]

        return text


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate implementation prompts from planned features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all features:
    python3 scripts/generate_prompt.py --list

  List only bugs:
    python3 scripts/generate_prompt.py --list --type bug

  List planned features:
    python3 scripts/generate_prompt.py --list --status planned

  Generate prompt for feature 104:
    python3 scripts/generate_prompt.py 104

  Generate prompt for bug 49:
    python3 scripts/generate_prompt.py 49
        """
    )

    parser.add_argument(
        "feature_id",
        type=int,
        nargs="?",
        help="Feature ID to generate prompt for"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all features instead of generating prompt"
    )

    parser.add_argument(
        "--status",
        choices=["planned", "in_progress", "completed", "cancelled"],
        help="Filter by status (used with --list)"
    )

    parser.add_argument(
        "--type",
        choices=["session", "feature", "bug", "enhancement"],
        help="Filter by type (used with --list)"
    )

    args = parser.parse_args()

    try:
        generator = PromptGenerator()

        if args.list:
            # List features
            generator.list_features(status=args.status, item_type=args.type)
        elif args.feature_id:
            # Generate prompt
            generator.generate(args.feature_id)
        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
