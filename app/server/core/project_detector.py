"""
Project context detection module.
Analyzes project structure to determine framework, tools, and complexity.
"""

import json
from pathlib import Path
from typing import Optional, List
from core.data_models import ProjectContext


def detect_project_context(path: str) -> ProjectContext:
    """
    Detect project context by analyzing directory structure and files.

    This is the main entry point for project analysis. It orchestrates multiple
    detection functions to build a complete picture of the project's technology
    stack, complexity, and characteristics. The information is used to make
    intelligent workflow recommendations.

    Detection Strategy:
    1. Validate directory exists
    2. Check if project is new (empty directory)
    3. Detect frontend framework (React, Vue, Next.js, etc.)
    4. Detect backend framework (FastAPI, Django, Express, etc.)
    5. Identify build tools (Vite, Webpack, TypeScript, etc.)
    6. Identify package manager (npm, yarn, uv, poetry, etc.)
    7. Check git initialization
    8. Calculate complexity score from project structure

    Args:
        path: Path to project directory (can be relative or absolute)

    Returns:
        ProjectContext object containing all detected information:
        - path: Normalized absolute path
        - is_new_project: Whether directory is empty
        - framework: Frontend framework or None
        - backend: Backend framework or None
        - complexity: "low", "medium", or "high"
        - build_tools: List of detected build tools
        - package_manager: Detected package manager or None
        - has_git: Whether .git directory exists

    Raises:
        ValueError: If the project path does not exist
    """
    project_path = Path(path)

    # Check if directory exists
    if not project_path.exists():
        raise ValueError(f"Project path does not exist: {path}")

    # Check if directory is empty (new project)
    is_new_project = is_directory_empty(project_path)

    # Detect framework
    framework = detect_framework(project_path)

    # Detect backend
    backend = detect_backend(project_path)

    # Detect build tools
    build_tools = detect_build_tools(project_path)

    # Detect package manager
    package_manager = detect_package_manager(project_path)

    # Check git status
    has_git = check_git_initialized(project_path)

    # Calculate complexity
    complexity = calculate_complexity_from_structure(
        project_path, framework, backend, build_tools
    )

    return ProjectContext(
        path=str(project_path),
        is_new_project=is_new_project,
        framework=framework,
        backend=backend,
        complexity=complexity,
        build_tools=build_tools,
        package_manager=package_manager,
        has_git=has_git
    )


def is_directory_empty(path: Path) -> bool:
    """
    Check if directory is empty or only contains hidden files.

    Args:
        path: Path to check

    Returns:
        True if empty, False otherwise
    """
    if not path.is_dir():
        return False

    # Get all items, including hidden files
    items = list(path.iterdir())

    # Consider directory empty if it has no items or only .git
    non_hidden = [item for item in items if not item.name.startswith('.')]

    return len(non_hidden) == 0


def detect_framework(path: Path) -> Optional[str]:
    """
    Detect frontend/application framework.

    Args:
        path: Project path

    Returns:
        Framework name or None
    """
    # Check for React with Vite
    if (path / "vite.config.ts").exists() or (path / "vite.config.js").exists():
        package_json = path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "react" in deps:
                        return "react-vite"
                    elif "vue" in deps:
                        return "vue-vite"
            except (OSError, json.JSONDecodeError, KeyError):
                pass
        return "vite"

    # Check for Next.js
    package_json = path / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                if "next" in deps:
                    return "nextjs"
                elif "react" in deps:
                    return "react"
                elif "vue" in deps:
                    return "vue"
                elif "@angular/core" in deps:
                    return "angular"
                elif "svelte" in deps:
                    return "svelte"
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    # Check for Python frameworks
    if (path / "pyproject.toml").exists():
        return None  # Backend framework will be detected separately

    return None


def detect_backend(path: Path) -> Optional[str]:
    """
    Detect backend framework.

    Args:
        path: Project path

    Returns:
        Backend framework name or None
    """
    # Check for FastAPI
    pyproject_toml = path / "pyproject.toml"
    if pyproject_toml.exists():
        try:
            with open(pyproject_toml) as f:
                content = f.read()
                if "fastapi" in content.lower():
                    return "fastapi"
                elif "django" in content.lower():
                    return "django"
                elif "flask" in content.lower():
                    return "flask"
        except OSError:
            pass

    # Check requirements.txt
    requirements = path / "requirements.txt"
    if requirements.exists():
        try:
            with open(requirements) as f:
                content = f.read().lower()
                if "fastapi" in content:
                    return "fastapi"
                elif "django" in content:
                    return "django"
                elif "flask" in content:
                    return "flask"
        except OSError:
            pass

    # Check for Node.js backend
    package_json = path / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                if "express" in deps:
                    return "express"
                elif "fastify" in deps:
                    return "fastify"
                elif "@nestjs/core" in deps:
                    return "nestjs"
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    return None


def detect_build_tools(path: Path) -> List[str]:
    """
    Detect build tools in the project.

    Args:
        path: Project path

    Returns:
        List of detected build tools
    """
    tools = []

    # Check for various build tools
    if (path / "vite.config.ts").exists() or (path / "vite.config.js").exists():
        tools.append("vite")

    if (path / "webpack.config.js").exists():
        tools.append("webpack")

    if (path / "rollup.config.js").exists():
        tools.append("rollup")

    if (path / "tsconfig.json").exists():
        tools.append("typescript")

    if (path / "babel.config.js").exists() or (path / ".babelrc").exists():
        tools.append("babel")

    if (path / "Makefile").exists():
        tools.append("make")

    if (path / "Dockerfile").exists():
        tools.append("docker")

    return tools


def detect_package_manager(path: Path) -> Optional[str]:
    """
    Detect package manager used in the project.

    Args:
        path: Project path

    Returns:
        Package manager name or None
    """
    if (path / "bun.lockb").exists():
        return "bun"

    if (path / "pnpm-lock.yaml").exists():
        return "pnpm"

    if (path / "yarn.lock").exists():
        return "yarn"

    if (path / "package-lock.json").exists():
        return "npm"

    if (path / "uv.lock").exists():
        return "uv"

    if (path / "poetry.lock").exists():
        return "poetry"

    if (path / "Pipfile.lock").exists():
        return "pipenv"

    # Default guesses based on what's present
    if (path / "package.json").exists():
        return "npm"

    if (path / "pyproject.toml").exists():
        return "pip"

    return None


def check_git_initialized(path: Path) -> bool:
    """
    Check if git is initialized in the project.

    Args:
        path: Project path

    Returns:
        True if git is initialized, False otherwise
    """
    return (path / ".git").exists()


def calculate_complexity_from_structure(
    path: Path,
    framework: Optional[str],
    backend: Optional[str],
    build_tools: List[str]
) -> str:
    """
    Calculate project complexity based on structure.

    This function implements a scoring system that evaluates multiple factors
    to determine overall project complexity. The complexity level influences
    which ADW workflow and model set are recommended.

    Scoring Factors:
    - File count: More files = higher complexity
      * >100 files: +2 points
      * >50 files: +1 point
    - Framework presence: Any framework adds +1 point
    - Backend presence: Any backend adds +1 point
    - Build tool count: >2 tools adds +1 point
    - Monorepo structure: packages/ or apps/ directory adds +2 points

    Thresholds:
    - Score >= 5: High complexity
    - Score >= 3: Medium complexity
    - Score < 3: Low complexity

    Args:
        path: Project path
        framework: Detected framework (e.g., "react-vite")
        backend: Detected backend (e.g., "fastapi")
        build_tools: List of build tools (e.g., ["vite", "typescript"])

    Returns:
        Complexity level: "low", "medium", or "high"
    """
    complexity_score = 0

    # Count files in project (excluding node_modules, venv, etc.)
    file_count = count_project_files(path)

    if file_count > 100:
        complexity_score += 2
    elif file_count > 50:
        complexity_score += 1

    # Framework complexity
    if framework:
        complexity_score += 1

    # Backend adds complexity
    if backend:
        complexity_score += 1

    # Multiple build tools indicate complexity
    if len(build_tools) > 2:
        complexity_score += 1

    # Check for multiple packages (monorepo)
    if (path / "packages").exists() or (path / "apps").exists():
        complexity_score += 2

    # Determine complexity level
    if complexity_score >= 5:
        return "high"
    elif complexity_score >= 3:
        return "medium"
    else:
        return "low"


def count_project_files(path: Path) -> int:
    """
    Count source files in project, excluding common ignored directories.

    Args:
        path: Project path

    Returns:
        Number of source files
    """
    ignored_dirs = {
        "node_modules", "venv", ".venv", "dist", "build", ".git",
        "__pycache__", ".pytest_cache", "coverage", ".next"
    }

    count = 0
    try:
        for item in path.rglob("*"):
            # Skip if in ignored directory
            if any(ignored in item.parts for ignored in ignored_dirs):
                continue

            # Count only files (not directories)
            if item.is_file():
                count += 1
    except OSError:
        pass

    return count


def suggest_workflow(context: ProjectContext) -> str:
    """
    Recommend ADW workflow based on project context.

    Args:
        context: ProjectContext object

    Returns:
        Recommended workflow name
    """
    if context.complexity == "high":
        return "adw_plan_build_test_iso"
    elif context.complexity == "medium":
        return "adw_plan_build_test_iso"
    else:
        return "adw_sdlc_iso"


def calculate_complexity(context: ProjectContext) -> str:
    """
    Calculate project complexity from ProjectContext.
    This is a wrapper that returns the already-calculated complexity.

    Args:
        context: ProjectContext object

    Returns:
        Complexity level
    """
    return context.complexity
