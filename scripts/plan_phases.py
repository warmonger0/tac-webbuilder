#!/usr/bin/env python3
"""
Phase Planning and Prompt Generation

Analyzes planned features, determines phase breakdown, and generates
implementation prompts for each phase with dependency analysis.

Usage:
    python3 scripts/plan_phases.py 49 52 55 57    # Specific issues
    python3 scripts/plan_phases.py                 # All planned issues
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Add app/server to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from services.planned_features_service import PlannedFeaturesService
from utils.codebase_analyzer import CodebaseAnalyzer


@dataclass
class Phase:
    """Represents a single implementation phase."""
    issue_id: int
    phase_number: int
    total_phases: int
    title: str
    description: str
    estimated_hours: float
    files_to_modify: List[str]
    depends_on: List[Tuple[int, int]]  # List of (issue_id, phase_number) dependencies

    @property
    def filename(self) -> str:
        """Generate filename for this phase prompt."""
        slug = self._slugify(self.title)
        if self.total_phases == 1:
            if self.estimated_hours <= 2.0:
                return f"QUICK_WIN_{self.issue_id}_{slug}.md"
            return f"FEATURE_{self.issue_id}_{slug}.md"
        return f"FEATURE_{self.issue_id}_PHASE_{self.phase_number}_{slug}.md"

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to slug format."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '_', text)
        text = text.strip('_')
        return text[:50]


class PhaseAnalyzer:
    """Analyzes features and determines optimal phase breakdown."""

    def __init__(self):
        """Initialize analyzer."""
        self.service = PlannedFeaturesService()
        self.codebase_analyzer = CodebaseAnalyzer()

    def analyze_feature(self, feature_id: int) -> List[Phase]:
        """
        Analyze a feature and determine phase breakdown.

        Args:
            feature_id: ID of feature to analyze

        Returns:
            List of Phase objects representing the breakdown
        """
        feature = self.service.get_by_id(feature_id)
        if not feature:
            raise ValueError(f"Feature #{feature_id} not found")

        # Determine number of phases based on complexity
        phase_count = self._determine_phase_count(feature)

        # Get codebase context
        context = self.codebase_analyzer.find_relevant_files(feature)

        # Create phases
        phases = []
        if phase_count == 1:
            # Single phase - entire feature
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=1,
                total_phases=1,
                title=feature.title,
                description=feature.description or "",
                estimated_hours=feature.estimated_hours or 1.0,
                files_to_modify=self._extract_file_list(context),
                depends_on=[]
            ))
        else:
            # Multi-phase - break down by layer
            phases = self._create_multi_phase_breakdown(feature, phase_count, context)

        return phases

    def _determine_phase_count(self, feature) -> int:
        """
        Determine how many phases a feature needs.

        Logic:
        - 0.25h - 2h: 1 phase (quick win)
        - 2h - 6h: 2 phases (foundation + integration)
        - 6h - 12h: 3 phases (data + backend + frontend)
        - 12h+: 4+ phases (data + backend + frontend + integration)

        Also check description for explicit phase mentions.
        """
        hours = feature.estimated_hours or 1.0
        description = (feature.description or "").lower()

        # Check for explicit phase mentions in description
        phase_mentions = re.findall(r'phase \d+', description)
        if phase_mentions:
            # Extract highest phase number mentioned
            numbers = [int(re.search(r'\d+', m).group()) for m in phase_mentions]
            explicit_count = max(numbers)
            return max(explicit_count, self._hours_to_phases(hours))

        return self._hours_to_phases(hours)

    @staticmethod
    def _hours_to_phases(hours: float) -> int:
        """Convert estimated hours to phase count."""
        if hours <= 2.0:
            return 1
        elif hours <= 6.0:
            return 2
        elif hours <= 12.0:
            return 3
        else:
            # For very large features, use 4h per phase
            return min(5, int((hours + 3) / 4))

    def _create_multi_phase_breakdown(self, feature, phase_count: int, context: dict) -> List[Phase]:
        """Create multi-phase breakdown for a feature."""
        phases = []
        base_hours = (feature.estimated_hours or 4.0) / phase_count

        # Standard breakdown patterns
        if phase_count == 2:
            # Phase 1: Backend/Foundation
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=1,
                total_phases=2,
                title=f"{feature.title} - Foundation",
                description="Database models, backend services, API endpoints",
                estimated_hours=base_hours,
                files_to_modify=self._filter_backend_files(context),
                depends_on=[]
            ))
            # Phase 2: Frontend/Integration
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=2,
                total_phases=2,
                title=f"{feature.title} - Integration",
                description="Frontend UI, integration, E2E tests",
                estimated_hours=base_hours,
                files_to_modify=self._filter_frontend_files(context),
                depends_on=[(feature.id, 1)]
            ))

        elif phase_count == 3:
            # Phase 1: Data Layer
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=1,
                total_phases=3,
                title=f"{feature.title} - Data Layer",
                description="Database schema, repositories, data models",
                estimated_hours=base_hours,
                files_to_modify=self._filter_data_files(context),
                depends_on=[]
            ))
            # Phase 2: Backend Services
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=2,
                total_phases=3,
                title=f"{feature.title} - Backend Services",
                description="Business logic, services, API routes",
                estimated_hours=base_hours,
                files_to_modify=self._filter_backend_files(context, exclude_data=True),
                depends_on=[(feature.id, 1)]
            ))
            # Phase 3: Frontend & Integration
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=3,
                total_phases=3,
                title=f"{feature.title} - Frontend & Integration",
                description="UI components, integration, E2E tests",
                estimated_hours=base_hours,
                files_to_modify=self._filter_frontend_files(context),
                depends_on=[(feature.id, 2)]
            ))

        else:  # 4+ phases
            # Phase 1: Database
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=1,
                total_phases=phase_count,
                title=f"{feature.title} - Database",
                description="Database migrations, schema updates",
                estimated_hours=base_hours,
                files_to_modify=self._filter_data_files(context),
                depends_on=[]
            ))
            # Phase 2: Backend Core
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=2,
                total_phases=phase_count,
                title=f"{feature.title} - Backend Core",
                description="Repositories, services, core business logic",
                estimated_hours=base_hours,
                files_to_modify=self._filter_backend_files(context, exclude_data=True),
                depends_on=[(feature.id, 1)]
            ))
            # Phase 3: API Layer
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=3,
                total_phases=phase_count,
                title=f"{feature.title} - API Layer",
                description="API routes, request/response models",
                estimated_hours=base_hours,
                files_to_modify=self._filter_api_files(context),
                depends_on=[(feature.id, 2)]
            ))
            # Phase 4: Frontend
            phases.append(Phase(
                issue_id=feature.id,
                phase_number=4,
                total_phases=phase_count,
                title=f"{feature.title} - Frontend",
                description="UI components, client integration",
                estimated_hours=base_hours,
                files_to_modify=self._filter_frontend_files(context),
                depends_on=[(feature.id, 3)]
            ))
            # Phase 5: Integration & Tests (if needed)
            if phase_count >= 5:
                phases.append(Phase(
                    issue_id=feature.id,
                    phase_number=5,
                    total_phases=phase_count,
                    title=f"{feature.title} - Integration & Tests",
                    description="E2E tests, integration testing, final validation",
                    estimated_hours=base_hours,
                    files_to_modify=[],
                    depends_on=[(feature.id, 4)]
                ))

        return phases

    def _extract_file_list(self, context: dict) -> List[str]:
        """Extract all file paths from context."""
        files = []
        for file_path, _ in context.get('backend_files', []):
            files.append(file_path)
        for file_path, _ in context.get('frontend_files', []):
            files.append(file_path)
        return files

    def _filter_backend_files(self, context: dict, exclude_data: bool = False) -> List[str]:
        """Filter for backend files only."""
        files = []
        for file_path, _ in context.get('backend_files', []):
            if exclude_data and any(pattern in file_path for pattern in ['database/', 'repositories/', 'models/']):
                continue
            if not any(pattern in file_path for pattern in ['routes/', 'api/']):
                files.append(file_path)
        return files

    def _filter_frontend_files(self, context: dict) -> List[str]:
        """Filter for frontend files only."""
        return [file_path for file_path, _ in context.get('frontend_files', [])]

    def _filter_data_files(self, context: dict) -> List[str]:
        """Filter for data layer files only."""
        files = []
        for file_path, _ in context.get('backend_files', []):
            if any(pattern in file_path for pattern in ['database/', 'repositories/', 'models/']):
                files.append(file_path)
        return files

    def _filter_api_files(self, context: dict) -> List[str]:
        """Filter for API/routes files only."""
        files = []
        for file_path, _ in context.get('backend_files', []):
            if any(pattern in file_path for pattern in ['routes/', 'api/']):
                files.append(file_path)
        return files


class DependencyAnalyzer:
    """Analyzes dependencies between phases and identifies parallel execution opportunities."""

    def analyze_dependencies(self, all_phases: List[List[Phase]]) -> Dict:
        """
        Analyze dependencies across all phases.

        Args:
            all_phases: List of phase lists (one per feature)

        Returns:
            Dependency analysis with parallel/sequential execution plan
        """
        # Flatten phases
        flat_phases = [phase for phases in all_phases for phase in phases]

        # Find file conflicts
        file_to_phases = {}
        for phase in flat_phases:
            for file in phase.files_to_modify:
                if file not in file_to_phases:
                    file_to_phases[file] = []
                file_to_phases[file].append(phase)

        # Identify parallel tracks
        parallel_tracks = self._find_parallel_tracks(flat_phases, file_to_phases)

        return {
            'total_phases': len(flat_phases),
            'total_hours': sum(p.estimated_hours for p in flat_phases),
            'parallel_tracks': parallel_tracks,
            'file_conflicts': {f: len(phases) for f, phases in file_to_phases.items() if len(phases) > 1},
        }

    def _find_parallel_tracks(self, phases: List[Phase], file_to_phases: Dict) -> List[List[Phase]]:
        """Find groups of phases that can run in parallel."""
        # For now, simple logic: phases with no file conflicts can run in parallel
        tracks = []
        remaining = set(range(len(phases)))

        while remaining:
            track = []
            used_files = set()

            for i in list(remaining):
                phase = phases[i]

                # Check if any files conflict with current track
                conflicts = any(f in used_files for f in phase.files_to_modify)

                # Check if phase has dependencies
                has_dependencies = bool(phase.depends_on)

                if not conflicts and not has_dependencies:
                    track.append(phase)
                    used_files.update(phase.files_to_modify)
                    remaining.remove(i)

            if track:
                tracks.append(track)
            else:
                # Add first remaining phase to break deadlock
                if remaining:
                    i = min(remaining)
                    tracks.append([phases[i]])
                    remaining.remove(i)

        return tracks


class CoordinationDocGenerator:
    """Generates coordination document with execution plan."""

    def generate(self, all_phases: List[List[Phase]], dependency_analysis: Dict) -> str:
        """Generate coordination document."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PHASE_PLAN_{timestamp}.md"

        doc_lines = [
            f"# Phase Implementation Plan",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            f"- Total Features: {len(all_phases)}",
            f"- Total Phases: {dependency_analysis['total_phases']}",
            f"- Estimated Time: {dependency_analysis['total_hours']:.1f}h",
            f"- Parallel Tracks: {len(dependency_analysis['parallel_tracks'])}",
            "",
            "## Features Analyzed",
            "",
        ]

        # Table of features
        doc_lines.append("| Issue | Type | Phases | Hours | Title |")
        doc_lines.append("|-------|------|--------|-------|-------|")
        for phases in all_phases:
            if phases:
                p = phases[0]
                total_hours = sum(ph.estimated_hours for ph in phases)
                doc_lines.append(
                    f"| #{p.issue_id} | Feature | {len(phases)} | {total_hours:.1f}h | {p.title.split(' - ')[0]} |"
                )
        doc_lines.append("")

        # Execution sequence
        doc_lines.append("## Execution Sequence")
        doc_lines.append("")

        for i, track in enumerate(dependency_analysis['parallel_tracks'], 1):
            if len(dependency_analysis['parallel_tracks']) > 1:
                doc_lines.append(f"### Track {i} (parallel)")
            else:
                doc_lines.append(f"### Sequential Execution")
            doc_lines.append("")

            for phase in track:
                deps = ""
                if phase.depends_on:
                    dep_str = ", ".join(f"#{issue_id} Phase {phase_num}" for issue_id, phase_num in phase.depends_on)
                    deps = f" (depends on: {dep_str})"

                doc_lines.append(f"- **{phase.filename}**{deps}")
                doc_lines.append(f"  - Issue #{phase.issue_id}: {phase.title}")
                doc_lines.append(f"  - Estimated: {phase.estimated_hours:.1f}h")
                if phase.files_to_modify:
                    doc_lines.append(f"  - Files: {len(phase.files_to_modify)} to modify")
                doc_lines.append("")

        # File conflicts
        if dependency_analysis['file_conflicts']:
            doc_lines.append("## File Modification Conflicts")
            doc_lines.append("")
            doc_lines.append("These files are modified by multiple phases (requires coordination):")
            doc_lines.append("")
            for file, count in sorted(dependency_analysis['file_conflicts'].items(), key=lambda x: -x[1]):
                doc_lines.append(f"- `{file}` ({count} phases)")
            doc_lines.append("")

        # Generated files
        doc_lines.append("## Generated Prompt Files")
        doc_lines.append("")
        for phases in all_phases:
            for phase in phases:
                doc_lines.append(f"- {phase.filename}")
        doc_lines.append("")

        # Next steps
        doc_lines.append("## Next Steps")
        doc_lines.append("")
        doc_lines.append("1. Review this coordination document")
        doc_lines.append("2. Generate individual phase prompts (run with --generate flag)")
        doc_lines.append("3. Execute phases in order per tracks above")
        doc_lines.append("4. Mark each phase complete in Plans Panel before moving to next")
        doc_lines.append("")

        # Write to file
        output_path = Path.cwd() / filename
        output_path.write_text("\n".join(doc_lines))

        return filename


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze features and generate phase implementation plan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "feature_ids",
        type=int,
        nargs="*",
        help="Feature IDs to analyze (empty for all planned)"
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate individual phase prompt files (not just coordination doc)"
    )

    args = parser.parse_args()

    try:
        analyzer = PhaseAnalyzer()
        dep_analyzer = DependencyAnalyzer()
        doc_gen = CoordinationDocGenerator()

        # Get feature IDs
        if args.feature_ids:
            feature_ids = args.feature_ids
        else:
            # Get all planned features
            service = PlannedFeaturesService()
            features = service.get_all(status='planned')
            feature_ids = [f.id for f in features]

        if not feature_ids:
            print("No features to analyze")
            return

        # Analyze each feature
        print(f"\n📊 Analyzing {len(feature_ids)} feature(s)...")
        all_phases = []
        for feature_id in feature_ids:
            print(f"   Analyzing feature #{feature_id}...")
            phases = analyzer.analyze_feature(feature_id)
            all_phases.append(phases)
            print(f"   → {len(phases)} phase(s)")

        # Analyze dependencies
        print("\n🔍 Analyzing dependencies...")
        dependency_analysis = dep_analyzer.analyze_dependencies(all_phases)

        # Generate coordination document
        print("\n📝 Generating coordination document...")
        doc_filename = doc_gen.generate(all_phases, dependency_analysis)

        # Summary
        print(f"\n✅ Phase Planning Complete\n")
        print(f"Features Analyzed: {len(feature_ids)}")
        print(f"Total Phases: {dependency_analysis['total_phases']}")
        print(f"Estimated Time: {dependency_analysis['total_hours']:.1f}h")
        print(f"Parallel Tracks: {len(dependency_analysis['parallel_tracks'])}")
        print(f"\n📄 Coordination Document: {doc_filename}")

        if not args.generate:
            print("\n💡 Tip: Run with --generate flag to create individual phase prompt files")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
