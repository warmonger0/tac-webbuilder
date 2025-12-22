"""
Planned Features API Routes

RESTful API endpoints for managing planned features, sessions, bugs, and enhancements.

Endpoints:
- GET    /api/planned-features       - Get all planned features (with optional filters)
- GET    /api/planned-features/stats - Get statistics
- GET    /api/planned-features/recent-completions - Get recent completions
- GET    /api/planned-features/{id}  - Get single feature
- POST   /api/planned-features       - Create new feature
- PATCH  /api/planned-features/{id}  - Update feature
- DELETE /api/planned-features/{id}  - Delete feature (soft delete)
- POST   /api/planned-features/{id}/start-automation - Start event-driven phase automation
"""

import logging
import sys
import uuid
from pathlib import Path

from core.data_models import GitHubIssue
from core.github_poster import GitHubPoster
from core.models import PlannedFeature, PlannedFeatureCreate, PlannedFeatureUpdate
from fastapi import APIRouter, HTTPException, Query
from models.phase_queue_item import PhaseQueueItem
from repositories.phase_queue_repository import PhaseQueueRepository
from services.planned_features_service import PlannedFeaturesService
from services.websocket_manager import get_connection_manager

# Add scripts directory to path for PhaseAnalyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

try:
    from generate_prompt import PromptGenerator
    from plan_phases import PhaseAnalyzer
except ImportError:
    PhaseAnalyzer = None  # Handle gracefully if script not available
    PromptGenerator = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/planned-features", tags=["planned-features"])

# Initialize GitHub poster for issue creation
github_poster = GitHubPoster()


def _create_github_issue_from_feature(feature: PlannedFeature) -> int:
    """
    Create a GitHub issue from a planned feature using GitHubPoster.

    Uses the same service as Panel 1 for consistency and observability.

    Args:
        feature: Planned feature to create issue for

    Returns:
        Issue number of created issue

    Raises:
        RuntimeError: If issue creation fails
    """
    # Build issue body
    body_parts = []
    if feature.description:
        body_parts.append(feature.description)

    if feature.estimated_hours:
        body_parts.append(f"\n**Estimated Hours:** {feature.estimated_hours}")

    if feature.tags:
        body_parts.append(f"\n**Tags:** {', '.join(feature.tags)}")

    body = "\n\n".join(body_parts) if body_parts else "Automated feature from Plans Panel"

    # Add workflow specification for ADW (CRITICAL: ADW needs this to know which workflow to run)
    body += "\n\n---\n\nInclude workflow: adw_sdlc_complete_iso"

    # Build labels
    labels = [feature.item_type]
    if feature.priority:
        labels.append(f"priority-{feature.priority}")

    # Map item_type to classification (feature/bug/chore)
    classification_map = {
        "feature": "feature",
        "enhancement": "feature",
        "bug": "bug",
        "session": "chore",
    }
    classification = classification_map.get(feature.item_type, "feature")

    # Map priority to model_set (lightweight/base/heavy)
    model_set_map = {
        "low": "lightweight",
        "medium": "base",
        "high": "heavy",
    }
    model_set = model_set_map.get(feature.priority or "medium", "base")

    # Create GitHubIssue object
    github_issue = GitHubIssue(
        title=feature.title,
        body=body,
        classification=classification,
        labels=labels,
        workflow="adw_sdlc_complete_iso",
        model_set=model_set
    )

    # Use GitHubPoster (same as Panel 1)
    logger.info(f"Creating GitHub issue for feature #{feature.id} via GitHubPoster: {feature.title}")
    issue_number = github_poster.post_issue(github_issue, confirm=False)
    logger.info(f"Created GitHub issue #{issue_number} for feature #{feature.id}")

    return issue_number


async def _broadcast_planned_features_update():
    """Broadcast planned features update to all WebSocket clients"""
    try:
        manager = get_connection_manager()
        service = PlannedFeaturesService()

        # Get all features and stats
        features = service.get_all(limit=200)
        stats = service.get_statistics()

        # Broadcast update
        await manager.broadcast({
            "type": "planned_features_update",
            "data": {
                "features": [f.model_dump() for f in features],
                "stats": stats
            }
        })
        logger.debug("[WS] Broadcast planned features update")
    except Exception as e:
        logger.error(f"[WS] Error broadcasting planned features update: {e}")


@router.get("/", response_model=list[PlannedFeature])
async def get_planned_features(
    status: str | None = Query(
        None, description="Filter by status: planned, in_progress, completed, cancelled"
    ),
    item_type: str | None = Query(
        None, description="Filter by type: session, feature, bug, enhancement"
    ),
    priority: str | None = Query(
        None, description="Filter by priority: high, medium, low"
    ),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000),
    offset: int = Query(0, description="Number of results to skip (pagination)", ge=0),
):
    """
    Get all planned features with optional filtering and pagination.

    Results are ordered by:
    1. Status (in_progress, planned, completed, cancelled)
    2. Priority (high, medium, low)
    3. Creation date (newest first)

    Query parameters:
    - status: Filter by status
    - item_type: Filter by type
    - priority: Filter by priority
    - limit: Maximum results (1-1000, default: 100)
    - offset: Skip N results for pagination (default: 0)

    Returns:
        List of PlannedFeature objects
    """
    try:
        service = PlannedFeaturesService()
        features = service.get_all(
            status=status, item_type=item_type, priority=priority, limit=limit, offset=offset
        )
        logger.info(
            f"[GET /api/planned-features] Retrieved {len(features)} features (offset: {offset})"
        )
        return features
    except Exception as e:
        logger.error(f"[GET /api/planned-features] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """
    Get statistics about planned features.

    Returns:
        Dictionary with:
        - by_status: Count by status
        - by_priority: Count by priority
        - by_type: Count by item type
        - total_estimated_hours: Sum of estimated hours
        - total_actual_hours: Sum of actual hours
        - completion_rate: Percentage completed
    """
    try:
        service = PlannedFeaturesService()
        stats = service.get_statistics()
        logger.info("[GET /api/planned-features/stats] Generated statistics")
        return stats
    except Exception as e:
        logger.error(f"[GET /api/planned-features/stats] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-completions")
async def get_recent_completions(
    days: int = Query(
        30, description="Number of days to look back", ge=1, le=365
    )
):
    """
    Get recently completed features.

    Query parameters:
    - days: Number of days to look back (1-365, default: 30)

    Returns:
        List of completed PlannedFeature objects ordered by completion date
    """
    try:
        service = PlannedFeaturesService()
        features = service.get_recent_completions(days=days)
        logger.info(
            f"[GET /api/planned-features/recent-completions] Found {len(features)} completions in last {days} days"
        )
        return features
    except Exception as e:
        logger.error(
            f"[GET /api/planned-features/recent-completions] Error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{feature_id}", response_model=PlannedFeature)
async def get_planned_feature(feature_id: int):
    """
    Get single planned feature by ID.

    Path parameters:
    - feature_id: Feature ID

    Returns:
        PlannedFeature object

    Raises:
        404: Feature not found
    """
    try:
        service = PlannedFeaturesService()
        feature = service.get_by_id(feature_id)

        if not feature:
            logger.warning(
                f"[GET /api/planned-features/{feature_id}] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        logger.info(f"[GET /api/planned-features/{feature_id}] Retrieved feature")
        return feature
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /api/planned-features/{feature_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PlannedFeature, status_code=201)
async def create_planned_feature(feature_data: PlannedFeatureCreate):
    """
    Create new planned feature.

    Request body:
    - item_type: Type (session, feature, bug, enhancement)
    - title: Feature title (required)
    - description: Detailed description (optional)
    - status: Initial status (default: 'planned')
    - priority: Priority (high, medium, low)
    - estimated_hours: Estimated hours
    - session_number: Session number (for sessions)
    - github_issue_number: Related GitHub issue
    - parent_id: Parent feature ID (for hierarchical features)
    - tags: List of tags

    Returns:
        Created PlannedFeature object with assigned ID

    Raises:
        400: Invalid feature data
    """
    try:
        service = PlannedFeaturesService()
        feature = service.create(feature_data)
        logger.info(
            f"[POST /api/planned-features] Created feature {feature.id}: {feature.title}"
        )

        # Broadcast update to WebSocket clients
        await _broadcast_planned_features_update()

        return feature
    except ValueError as e:
        logger.error(f"[POST /api/planned-features] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[POST /api/planned-features] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{feature_id}", response_model=PlannedFeature)
async def update_planned_feature(feature_id: int, update_data: PlannedFeatureUpdate):
    """
    Update existing planned feature.

    Path parameters:
    - feature_id: Feature ID

    Request body (all optional):
    - title: New title
    - description: New description
    - status: New status (auto-updates timestamps)
    - priority: New priority
    - estimated_hours: New estimated hours
    - actual_hours: Actual hours spent
    - github_issue_number: GitHub issue number
    - tags: List of tags
    - completion_notes: Completion notes

    Auto-timestamp behavior:
    - started_at: Set when status → 'in_progress'
    - completed_at: Set when status → 'completed' or 'cancelled'

    Returns:
        Updated PlannedFeature object

    Raises:
        404: Feature not found
        400: Invalid update data
    """
    try:
        service = PlannedFeaturesService()

        # Verify feature exists
        existing = service.get_by_id(feature_id)
        if not existing:
            logger.warning(
                f"[PATCH /api/planned-features/{feature_id}] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        feature = service.update(feature_id, update_data)
        logger.info(
            f"[PATCH /api/planned-features/{feature_id}] Updated feature"
        )

        # Broadcast update to WebSocket clients
        await _broadcast_planned_features_update()

        return feature
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            f"[PATCH /api/planned-features/{feature_id}] Validation error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PATCH /api/planned-features/{feature_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{feature_id}", status_code=204)
async def delete_planned_feature(feature_id: int):
    """
    Delete planned feature (soft delete via status='cancelled').

    Path parameters:
    - feature_id: Feature ID

    Returns:
        204 No Content

    Raises:
        404: Feature not found
    """
    try:
        service = PlannedFeaturesService()

        # Verify feature exists
        existing = service.get_by_id(feature_id)
        if not existing:
            logger.warning(
                f"[DELETE /api/planned-features/{feature_id}] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        service.delete(feature_id)
        logger.info(
            f"[DELETE /api/planned-features/{feature_id}] Soft deleted feature"
        )

        # Broadcast update to WebSocket clients
        await _broadcast_planned_features_update()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /api/planned-features/{feature_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{feature_id}/start-automation")
async def start_automation(feature_id: int):
    """
    Start event-driven phase automation for a planned feature.

    This endpoint:
    1. Analyzes the feature to determine optimal phase breakdown
    2. Creates phase queue items with dependencies
    3. Triggers the PhaseCoordinator via event-driven architecture

    Path parameters:
    - feature_id: Feature ID from planned_features table

    Returns:
        Summary of phases created with queue IDs

    Raises:
        404: Feature not found
        400: PhaseAnalyzer not available or feature analysis failed
        500: Phase creation failed
    """
    try:
        # Check if PhaseAnalyzer is available
        if PhaseAnalyzer is None:
            logger.error(
                f"[POST /api/planned-features/{feature_id}/start-automation] PhaseAnalyzer not available"
            )
            raise HTTPException(
                status_code=400,
                detail="PhaseAnalyzer not available. Check scripts/plan_phases.py is accessible."
            )

        # Verify feature exists
        service = PlannedFeaturesService()
        feature = service.get_by_id(feature_id)
        if not feature:
            logger.warning(
                f"[POST /api/planned-features/{feature_id}/start-automation] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        # Create GitHub issue if not already exists or if recorded issue doesn't exist on GitHub
        needs_issue_creation = False
        if not feature.github_issue_number:
            needs_issue_creation = True
            logger.info(f"[POST /api/planned-features/{feature_id}/start-automation] No GitHub issue number recorded")
        else:
            # Verify the issue actually exists on GitHub
            if not github_poster.issue_exists(feature.github_issue_number):
                needs_issue_creation = True
                logger.warning(f"[POST /api/planned-features/{feature_id}/start-automation] GitHub issue #{feature.github_issue_number} recorded but doesn't exist on GitHub - will create new issue")
            else:
                logger.info(f"[POST /api/planned-features/{feature_id}/start-automation] Feature already has GitHub issue #{feature.github_issue_number}")

        if needs_issue_creation:
            logger.info(f"[POST /api/planned-features/{feature_id}/start-automation] Creating GitHub issue...")
            try:
                issue_number = _create_github_issue_from_feature(feature)

                # Update feature with GitHub issue number
                service.update(feature_id, PlannedFeatureUpdate(github_issue_number=issue_number))
                logger.info(f"[POST /api/planned-features/{feature_id}/start-automation] Created GitHub issue #{issue_number}")

                # Reload feature to get updated data
                feature = service.get_by_id(feature_id)
            except RuntimeError as e:
                logger.error(f"[POST /api/planned-features/{feature_id}/start-automation] Failed to create GitHub issue: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create GitHub issue: {str(e)}"
                )

        # Analyze feature and generate phase breakdown
        logger.info(
            f"[POST /api/planned-features/{feature_id}/start-automation] Analyzing feature..."
        )
        analyzer = PhaseAnalyzer()
        phases = analyzer.analyze_feature(feature_id)

        if not phases:
            logger.warning(
                f"[POST /api/planned-features/{feature_id}/start-automation] No phases generated"
            )
            raise HTTPException(
                status_code=400,
                detail="Feature analysis did not produce any phases"
            )

        # Create phase queue items
        logger.info(
            f"[POST /api/planned-features/{feature_id}/start-automation] Creating {len(phases)} phase queue items..."
        )
        repository = PhaseQueueRepository()
        created_phases = []

        for phase in phases:
            # Generate unique queue_id
            queue_id = f"{feature_id}_{phase.phase_number}_{uuid.uuid4().hex[:8]}"

            # Determine initial status: 'ready' if no dependencies, else 'queued'
            initial_status = 'ready' if not phase.depends_on else 'queued'

            # Convert depends_on from List[Tuple[int, int]] to List[int] (just phase numbers)
            # Note: In the new architecture, we track phase_number dependencies within the same feature
            depends_on_phase_numbers = [dep_phase_num for _, dep_phase_num in phase.depends_on]

            # Create phase data with detailed information
            phase_data = {
                "title": phase.title,
                "description": phase.description,
                "estimated_hours": phase.estimated_hours,
                "files_to_modify": phase.files_to_modify,
                "total_phases": phase.total_phases,
                "prompt_filename": phase.filename,
            }

            # Create PhaseQueueItem
            queue_item = PhaseQueueItem(
                queue_id=queue_id,
                feature_id=feature_id,
                phase_number=phase.phase_number,
                status=initial_status,
                depends_on_phases=depends_on_phase_numbers,
                phase_data=phase_data,
                priority=50,  # Normal priority
            )

            # Insert into database
            created_item = repository.create(queue_item)
            created_phases.append({
                "queue_id": created_item.queue_id,
                "phase_number": phase.phase_number,
                "title": phase.title,
                "status": initial_status,
                "depends_on_phases": depends_on_phase_numbers,
                "estimated_hours": phase.estimated_hours,
            })

            logger.info(
                f"[POST /api/planned-features/{feature_id}/start-automation] Created phase {phase.phase_number}/{phase.total_phases}: {queue_id}"
            )

        # Update feature status to 'in_progress'
        service.update(feature_id, PlannedFeatureUpdate(status='in_progress'))

        # Broadcast update to WebSocket clients
        await _broadcast_planned_features_update()

        # Return summary
        summary = {
            "feature_id": feature_id,
            "feature_title": feature.title,
            "total_phases": len(phases),
            "phases_created": created_phases,
            "ready_phases": sum(1 for p in created_phases if p["status"] == "ready"),
            "queued_phases": sum(1 for p in created_phases if p["status"] == "queued"),
            "message": f"Successfully created {len(phases)} phases. PhaseCoordinator will automatically launch ready phases.",
        }

        logger.info(
            f"[POST /api/planned-features/{feature_id}/start-automation] Automation started successfully"
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[POST /api/planned-features/{feature_id}/start-automation] Error: {e}"
        )
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{feature_id}/generate-plan")
async def generate_plan(feature_id: int):
    """
    Generate full markdown implementation prompts for a planned feature.

    This endpoint:
    1. Analyzes the feature to determine phase breakdown
    2. Generates complete markdown prompts for each phase (using template)
    3. Returns full prompt content ready to copy into Panel 1

    Does NOT:
    - Create GitHub issues
    - Create phase queue items
    - Trigger automation

    Path parameters:
    - feature_id: Feature ID from planned_features table

    Returns:
        Full markdown prompts for each phase

    Raises:
        404: Feature not found
        400: PhaseAnalyzer or PromptGenerator not available
    """
    try:
        # Check if required modules are available
        if PhaseAnalyzer is None or PromptGenerator is None:
            logger.error(
                f"[POST /api/planned-features/{feature_id}/generate-plan] Required modules not available"
            )
            raise HTTPException(
                status_code=400,
                detail="PhaseAnalyzer or PromptGenerator not available. Check scripts are accessible."
            )

        # Verify feature exists
        service = PlannedFeaturesService()
        feature = service.get_by_id(feature_id)
        if not feature:
            logger.warning(
                f"[POST /api/planned-features/{feature_id}/generate-plan] Feature not found"
            )
            raise HTTPException(status_code=404, detail="Feature not found")

        # Analyze feature and generate phase breakdown
        logger.info(
            f"[POST /api/planned-features/{feature_id}/generate-plan] Analyzing feature..."
        )
        analyzer = PhaseAnalyzer()
        phases = analyzer.analyze_feature(feature_id)

        if not phases:
            logger.warning(
                f"[POST /api/planned-features/{feature_id}/generate-plan] No phases generated"
            )
            raise HTTPException(
                status_code=400,
                detail="Feature analysis did not produce any phases"
            )

        # Generate full markdown prompts for each phase
        logger.info(
            f"[POST /api/planned-features/{feature_id}/generate-plan] Generating markdown prompts..."
        )

        prompt_generator = PromptGenerator()
        formatted_phases = []

        for phase in phases:
            # Generate markdown prompt for this phase
            # For multi-phase features, we need to create phase-specific prompts
            markdown_prompt = _generate_phase_prompt(
                feature=feature,
                phase=phase,
                prompt_generator=prompt_generator
            )

            formatted_phases.append({
                "phase_number": phase.phase_number,
                "total_phases": phase.total_phases,
                "title": phase.title,
                "description": phase.description,
                "estimated_hours": phase.estimated_hours,
                "files_to_modify": phase.files_to_modify,
                "depends_on": phase.depends_on,
                "prompt_filename": phase.filename,
                "markdown_prompt": markdown_prompt,  # Full markdown content
            })

        # Return plan summary
        plan_summary = {
            "feature_id": feature_id,
            "feature_title": feature.title,
            "total_phases": len(phases),
            "total_estimated_hours": sum(p.estimated_hours for p in phases),
            "phases": formatted_phases,
        }

        # Persist the generated plan to the database
        logger.info(
            f"[POST /api/planned-features/{feature_id}/generate-plan] Persisting plan to database..."
        )
        service.update(feature_id, PlannedFeatureUpdate(generated_plan=plan_summary))

        logger.info(
            f"[POST /api/planned-features/{feature_id}/generate-plan] Generated {len(phases)} markdown prompts"
        )

        return plan_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[POST /api/planned-features/{feature_id}/generate-plan] Error: {e}"
        )
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _generate_phase_prompt(feature, phase, prompt_generator) -> str:
    """
    Generate full markdown prompt for a specific phase.

    Args:
        feature: PlannedFeature object
        phase: Phase object from PhaseAnalyzer
        prompt_generator: PromptGenerator instance

    Returns:
        Complete markdown prompt content
    """
    from utils.codebase_analyzer import CodebaseAnalyzer

    # Get codebase context for this phase's files
    analyzer = CodebaseAnalyzer()

    # Create a filtered context based on phase files
    context = {
        "backend_files": [],
        "frontend_files": [],
        "related_functions": [],
        "test_files": [],
        "suggested_locations": []
    }

    # Analyze the specific files for this phase
    for file_path in phase.files_to_modify:
        if "app/server" in file_path or "adws" in file_path:
            context["backend_files"].append((file_path, 10.0))
        elif "app/client" in file_path:
            context["frontend_files"].append((file_path, 10.0))

    # Build phase-specific prompt
    # Path from app/server/routes/ -> project root is 3 levels up
    template_path = Path(__file__).parent.parent.parent.parent / ".claude" / "templates" / "IMPLEMENTATION_PROMPT_TEMPLATE.md"
    template = template_path.read_text()

    # Basic replacements
    replacements = {
        "[Type]": "Feature",
        "[ID]": str(feature.id),
        "[Title]": phase.title,
        "[One-line description]": phase.description,
        "[High/Medium/Low]": (feature.priority or "Medium").capitalize(),
        "[Bug/Feature/Enhancement/Session]": "Feature",
        "[X hours]": f"{phase.estimated_hours}",
    }

    # Apply replacements
    content = template
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    # Generate codebase section
    codebase_section = _generate_codebase_section_for_phase(context)

    # Insert context before "## Problem Statement"
    problem_statement_pos = content.find("## Problem Statement")
    if problem_statement_pos != -1:
        content = (
            content[:problem_statement_pos] +
            codebase_section + "\n\n" +
            content[problem_statement_pos:]
        )

    # Add phase-specific notes at the top
    phase_header = f"\n**Phase {phase.phase_number}/{phase.total_phases}**\n"
    if phase.depends_on:
        deps = ", ".join(f"Phase {pn}" for _, pn in phase.depends_on)
        phase_header += f"**Depends on:** {deps}\n"
    phase_header += "\n"

    # Insert phase header after the first line (title)
    lines = content.split("\n")
    lines.insert(2, phase_header)
    content = "\n".join(lines)

    return content


def _generate_codebase_section_for_phase(context: dict) -> str:
    """Generate codebase context section for a phase."""
    sections = ["## Codebase Context (Auto-Generated)", ""]

    # Backend files
    if context["backend_files"]:
        sections.append("### Files to Modify (Backend)")
        sections.append("")
        for file_path, _ in context["backend_files"]:
            sections.append(f"- `{file_path}`")
        sections.append("")

    # Frontend files
    if context["frontend_files"]:
        sections.append("### Files to Modify (Frontend)")
        sections.append("")
        for file_path, _ in context["frontend_files"]:
            sections.append(f"- `{file_path}`")
        sections.append("")

    if not context["backend_files"] and not context["frontend_files"]:
        sections.append("*Files will be determined during implementation.*")
        sections.append("")

    return "\n".join(sections)
