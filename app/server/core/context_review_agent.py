"""AI-powered context review agent using Claude API."""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextReviewResult:
    """
    Results from context analysis.

    Attributes:
        integration_strategy: High-level approach for implementing the change
        files_to_modify: List of existing files that need modifications
        files_to_create: List of new files to create
        reference_files: List of files to reference for patterns/examples
        risks: List of potential risks or concerns
        optimized_context: Categorized files (must-read vs optional vs skip)
        estimated_tokens: Estimated token count for optimized context
    """
    integration_strategy: str
    files_to_modify: List[str]
    files_to_create: List[str]
    reference_files: List[str]
    risks: List[str]
    optimized_context: Dict[str, List[str]]
    estimated_tokens: int


class ContextReviewAgent:
    """
    External AI agent for codebase context analysis.

    Uses Claude API to analyze proposed changes and generate:
    - Integration strategy
    - File identification (modify/create/reference)
    - Risk assessment
    - Context optimization (token savings)
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize agent with Claude API key.

        Args:
            anthropic_api_key: Anthropic API key (defaults to env var)

        Raises:
            ValueError: If API key not provided or found in environment
        """
        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set environment variable or pass to constructor."
            )

        # Import here to fail fast if anthropic not installed
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Run: uv add anthropic"
            )

    async def analyze_context(
        self,
        change_description: str,
        project_path: str,
        existing_files: Optional[List[str]] = None
    ) -> ContextReviewResult:
        """
        Analyze codebase context for a proposed change.

        Args:
            change_description: User's description of the change
            project_path: Path to the project directory
            existing_files: Optional list of files (for testing)

        Returns:
            ContextReviewResult with analysis and recommendations

        Raises:
            Exception: If analysis fails
        """
        logger.info(f"Starting context analysis for: {change_description[:100]}...")

        # Identify relevant files
        relevant_files = self.identify_relevant_files(
            change_description,
            project_path,
            existing_files
        )

        # Read sample files for context
        file_samples = self._read_file_samples(relevant_files[:10])

        # Analyze with Claude
        result = await self._analyze_with_claude(
            change_description,
            relevant_files,
            file_samples
        )

        logger.info("Context analysis complete")
        return result

    def identify_relevant_files(
        self,
        change_description: str,
        project_path: str,
        existing_files: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find files relevant to the change using keyword matching.

        Extracts keywords from description and matches against file paths.

        Args:
            change_description: Description of the proposed change
            project_path: Root path of the project
            existing_files: Optional pre-computed file list (for testing)

        Returns:
            List of relevant file paths (relative to project root)
        """
        # Extract keywords from description
        keywords = self._extract_keywords(change_description)
        logger.debug(f"Extracted keywords: {keywords}")

        # Get file list
        if existing_files is not None:
            all_files = existing_files
        else:
            all_files = self._scan_project_files(project_path)

        # Score files by relevance
        scored_files = []
        for file_path in all_files:
            score = self._score_file_relevance(file_path, keywords)
            if score > 0:
                scored_files.append((file_path, score))

        # Sort by score (descending) and return top matches
        scored_files.sort(key=lambda x: x[1], reverse=True)
        relevant = [path for path, score in scored_files[:50]]

        logger.info(f"Identified {len(relevant)} relevant files")
        return relevant

    def _extract_keywords(self, description: str) -> List[str]:
        """
        Extract keywords from change description.

        Args:
            description: Change description text

        Returns:
            List of lowercase keywords
        """
        # Remove common words
        stopwords = {
            'a', 'an', 'and', 'the', 'to', 'for', 'with', 'in', 'on', 'at',
            'from', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'add', 'create', 'implement'
        }

        # Extract words (alphanumeric + underscore)
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', description.lower())

        # Filter stopwords and short words
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:20]  # Limit to top 20 keywords

    def _scan_project_files(
        self,
        project_path: str,
        max_files: int = 10000
    ) -> List[str]:
        """
        Scan project directory for files.

        Args:
            project_path: Root directory path
            max_files: Maximum files to scan (default: 10000)

        Returns:
            List of file paths relative to project root
        """
        if not os.path.exists(project_path):
            logger.warning(f"Project path does not exist: {project_path}")
            return []

        exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', '.venv', 'build', 'dist', '.next', 'coverage',
            '.idea', '.vscode', 'target', 'out'
        }

        exclude_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe',
            '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg',
            '.woff', '.woff2', '.ttf', '.eot', '.map',
            '.min.js', '.min.css', '.bundle.js'
        }

        files = []
        try:
            for root, dirs, filenames in os.walk(project_path):
                # Filter excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                # Get relative path
                rel_root = os.path.relpath(root, project_path)

                for filename in filenames:
                    # Skip excluded extensions
                    if any(filename.endswith(ext) for ext in exclude_extensions):
                        continue

                    # Build relative path
                    if rel_root == '.':
                        file_path = filename
                    else:
                        file_path = os.path.join(rel_root, filename)

                    files.append(file_path)

                    # Stop if limit reached
                    if len(files) >= max_files:
                        logger.warning(f"File limit ({max_files}) reached")
                        return files

        except Exception as e:
            logger.error(f"Error scanning project files: {e}")

        return files

    def _score_file_relevance(self, file_path: str, keywords: List[str]) -> int:
        """
        Score file relevance based on keyword matching.

        Args:
            file_path: Relative file path
            keywords: List of keywords to match

        Returns:
            Relevance score (higher = more relevant)
        """
        score = 0
        lower_path = file_path.lower()

        # Exact matches in filename (highest weight)
        filename = os.path.basename(lower_path)
        for keyword in keywords:
            if keyword in filename:
                score += 10

        # Matches in directory path (medium weight)
        for keyword in keywords:
            if keyword in lower_path:
                score += 3

        # Boost for common code file extensions
        if any(lower_path.endswith(ext) for ext in ['.py', '.ts', '.tsx', '.js', '.jsx']):
            score += 1

        return score

    def _read_file_samples(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Read sample content from files.

        Args:
            file_paths: List of file paths to read

        Returns:
            Dictionary mapping file path to content (truncated)
        """
        samples = {}
        max_size = 5000  # Max chars per file

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(max_size)
                    samples[file_path] = content
            except Exception as e:
                logger.debug(f"Could not read {file_path}: {e}")
                continue

        return samples

    async def _analyze_with_claude(
        self,
        description: str,
        relevant_files: List[str],
        file_samples: Dict[str, str]
    ) -> ContextReviewResult:
        """
        Use Claude API to analyze context and generate strategy.

        Args:
            description: Change description
            relevant_files: List of relevant file paths
            file_samples: Sample file contents

        Returns:
            Parsed ContextReviewResult

        Raises:
            Exception: If API call fails or response is invalid
        """
        prompt = self._build_analysis_prompt(
            description,
            relevant_files,
            file_samples
        )

        try:
            # Use Haiku for cost efficiency
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract text content
            response_text = response.content[0].text

            # Parse JSON response
            result_json = self._extract_json(response_text)
            result = self._parse_result(result_json)

            return result

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    def _build_analysis_prompt(
        self,
        description: str,
        files: List[str],
        samples: Dict[str, str]
    ) -> str:
        """
        Build structured prompt for Claude API.

        Args:
            description: Change description
            files: Relevant file list
            samples: File content samples

        Returns:
            Formatted prompt string
        """
        samples_text = self._format_samples(samples)

        return f"""You are a codebase context analyzer. Analyze how this change should integrate.

## Proposed Change
{description}

## Relevant Files (Top {len(files[:20])})
{json.dumps(files[:20], indent=2)}

## Sample Files
{samples_text}

Provide analysis as JSON (no markdown, just pure JSON):
{{
  "integration_strategy": "Describe the overall approach in 2-3 sentences...",
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

Be specific with file paths. Include rationale in the strategy."""

    def _format_samples(self, samples: Dict[str, str]) -> str:
        """Format file samples for prompt."""
        if not samples:
            return "(No sample files available)"

        formatted = []
        for path, content in list(samples.items())[:5]:
            truncated = content[:500]
            formatted.append(f"### {path}\n```\n{truncated}\n...\n```")

        return "\n\n".join(formatted)

    def _extract_json(self, text: str) -> dict:
        """
        Extract JSON from Claude response.

        Handles cases where response is wrapped in markdown.

        Args:
            text: Response text

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If JSON cannot be extracted
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        # Try finding JSON object in text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        raise json.JSONDecodeError("No valid JSON found in response", text, 0)

    def _parse_result(self, result_json: dict) -> ContextReviewResult:
        """
        Parse Claude response into ContextReviewResult.

        Args:
            result_json: Parsed JSON dictionary

        Returns:
            ContextReviewResult instance

        Raises:
            KeyError: If required fields are missing
        """
        return ContextReviewResult(
            integration_strategy=result_json["integration_strategy"],
            files_to_modify=result_json.get("files_to_modify", []),
            files_to_create=result_json.get("files_to_create", []),
            reference_files=result_json.get("reference_files", []),
            risks=result_json.get("risks", []),
            optimized_context=result_json.get("optimized_context", {
                "must_read": [],
                "optional": [],
                "skip": []
            }),
            estimated_tokens=result_json.get("estimated_tokens", 0)
        )

    def generate_cache_key(
        self,
        description: str,
        project_path: str
    ) -> str:
        """
        Generate SHA256 cache key from description and project path.

        Args:
            description: Change description
            project_path: Project path

        Returns:
            Hex-encoded SHA256 hash
        """
        content = f"{description}:{project_path}"
        return hashlib.sha256(content.encode()).hexdigest()
