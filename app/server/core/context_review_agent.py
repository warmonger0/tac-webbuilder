"""
Context Review Agent

AI-powered agent that analyzes codebase context before ADW workflow execution.
Uses Claude API to identify relevant files, suggest integration strategies,
assess risks, and optimize context to minimize token usage.
"""

import hashlib
import json
import logging
import os
from pathlib import Path

from anthropic import Anthropic
from models.context_review import ContextReviewResult
from repositories.context_review_repository import ContextReviewRepository

logger = logging.getLogger(__name__)


class ContextReviewAgent:
    """External AI agent for codebase context analysis"""

    def __init__(self, anthropic_api_key: str | None = None):
        """
        Initialize the context review agent.

        Args:
            anthropic_api_key: Anthropic API key (defaults to env var)
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=api_key)
        self.repository = ContextReviewRepository()

    def analyze_context(
        self,
        change_description: str,
        project_path: str,
        max_files: int = 20,
    ) -> ContextReviewResult:
        """
        Analyze codebase context for a proposed change.

        Steps:
        1. Check cache for similar analysis
        2. Identify relevant files using keyword matching
        3. Read sample files to understand patterns
        4. Use Claude to analyze context
        5. Generate integration suggestions
        6. Cache results for similar requests

        Args:
            change_description: Natural language description of the change
            project_path: Path to the project
            max_files: Maximum number of files to analyze

        Returns:
            ContextReviewResult: Structured analysis result
        """
        # Check cache
        cache_key = self._generate_cache_key(change_description, project_path)
        cached = self._check_cache(cache_key)
        if cached:
            logger.info("[AGENT] Cache hit - returning cached analysis")
            return json.loads(cached)

        # Identify relevant files
        relevant_files = self.identify_relevant_files(
            change_description, project_path, max_files
        )

        # Read file samples
        file_samples = self._read_file_samples(relevant_files[:10], project_path)

        # Analyze with Claude
        result = self._analyze_with_claude(
            change_description, relevant_files, file_samples
        )

        # Cache result
        self._cache_result(cache_key, json.dumps(result.__dict__))

        return result

    def identify_relevant_files(
        self, change_description: str, project_path: str, max_files: int = 20
    ) -> list[str]:
        """
        Find files relevant to the change using keyword matching.

        Steps:
        1. Extract keywords from description
        2. Walk project directory
        3. Match file names and paths against keywords
        4. Score by relevance
        5. Return sorted list

        Args:
            change_description: Description of the change
            project_path: Path to project
            max_files: Maximum files to return

        Returns:
            list[str]: Sorted list of relevant file paths
        """
        keywords = self._extract_keywords(change_description)
        project_root = Path(project_path)

        if not project_root.exists():
            logger.warning(f"[AGENT] Project path does not exist: {project_path}")
            return []

        scored_files = []

        # Walk directory and score files
        for file_path in project_root.rglob("*"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                score = self._score_file(file_path, keywords, project_root)
                if score > 0:
                    scored_files.append((score, str(file_path.relative_to(project_root))))

        # Sort by score and return top matches
        scored_files.sort(reverse=True, key=lambda x: x[0])
        return [f[1] for f in scored_files[:max_files]]

    def _analyze_with_claude(
        self,
        description: str,
        relevant_files: list[str],
        file_samples: dict[str, str],
    ) -> ContextReviewResult:
        """
        Use Claude API to analyze context and generate strategy.

        Args:
            description: Change description
            relevant_files: List of relevant files
            file_samples: Sample file contents

        Returns:
            ContextReviewResult: Structured analysis
        """
        prompt = self._build_analysis_prompt(description, relevant_files, file_samples)

        try:
            # Use Haiku for cost efficiency
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response JSON
            content = response.content[0].text
            result_json = json.loads(content)

            return ContextReviewResult(
                integration_strategy=result_json.get("integration_strategy", ""),
                files_to_modify=result_json.get("files_to_modify", []),
                files_to_create=result_json.get("files_to_create", []),
                reference_files=result_json.get("reference_files", []),
                risks=result_json.get("risks", []),
                optimized_context=result_json.get("optimized_context", {}),
                estimated_tokens=result_json.get("estimated_tokens", 0),
            )

        except Exception as e:
            logger.error(f"[ERROR] Claude API call failed: {e}")
            # Return empty result on error
            return ContextReviewResult(
                integration_strategy=f"Analysis failed: {str(e)}",
                files_to_modify=[],
                files_to_create=[],
                reference_files=[],
                risks=["Analysis failed - check logs"],
                optimized_context={},
                estimated_tokens=0,
            )

    def _build_analysis_prompt(
        self, description: str, files: list[str], samples: dict[str, str]
    ) -> str:
        """Build prompt for Claude API."""
        formatted_samples = "\n\n".join(
            [f"### {path}\n```\n{content[:500]}...\n```" for path, content in samples.items()]
        )

        return f"""You are a codebase context analyzer. Analyze how this change should integrate with the codebase.

## Proposed Change
{description}

## Relevant Files (Top {len(files)})
{json.dumps(files, indent=2)}

## Sample Files
{formatted_samples}

Provide analysis as JSON with this exact structure:
{{
  "integration_strategy": "Describe the overall approach for implementing this change...",
  "files_to_modify": ["file1.py", "file2.ts"],
  "files_to_create": ["new_file.py"],
  "reference_files": ["example1.py", "pattern.ts"],
  "risks": ["Potential breaking change in...", "Missing test coverage for..."],
  "optimized_context": {{
    "must_read": ["critical_file.py"],
    "optional": ["reference.md"],
    "skip": ["unrelated.py"]
  }},
  "estimated_tokens": 1500
}}

Return ONLY the JSON object, no additional text.
"""

    def _generate_cache_key(self, description: str, project_path: str) -> str:
        """Generate cache key from description + project."""
        content = f"{description}:{project_path}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> str | None:
        """Check if analysis is cached."""
        return self.repository.check_cache(cache_key)

    def _cache_result(self, cache_key: str, result: str):
        """Cache analysis result."""
        self.repository.cache_result(cache_key, result)

    def _extract_keywords(self, description: str) -> list[str]:
        """Extract keywords from change description."""
        # Simple keyword extraction - split on spaces and common separators
        words = description.lower().replace(",", " ").replace(".", " ").split()
        # Filter out common words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with"}
        return [w for w in words if w not in stopwords and len(w) > 2]

    def _score_file(self, file_path: Path, keywords: list[str], project_root: Path) -> float:
        """Score a file's relevance based on keywords."""
        score = 0.0
        file_str = str(file_path.relative_to(project_root)).lower()

        for keyword in keywords:
            if keyword in file_str:
                score += 1.0

        return score

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        skip_patterns = [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".pytest_cache", "dist", "build", ".next", ".DS_Store"
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _read_file_samples(self, file_paths: list[str], project_root: str) -> dict[str, str]:
        """Read sample content from files."""
        samples = {}
        root = Path(project_root)

        for file_path in file_paths:
            full_path = root / file_path
            try:
                if full_path.exists() and full_path.is_file():
                    with open(full_path, encoding="utf-8") as f:
                        samples[file_path] = f.read(2000)  # First 2000 chars
            except Exception as e:
                logger.warning(f"[AGENT] Could not read {file_path}: {e}")

        return samples
