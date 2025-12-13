"""
Codebase Analyzer - Session 2: Intelligent File/Function Discovery

Analyzes codebase to find relevant files, functions, and suggest implementation locations.
"""

import re
from pathlib import Path
from typing import Any

# Common English stopwords to filter out from keyword extraction
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with", "not", "this", "when", "where", "why",
    "how", "what", "which", "who", "if", "can", "should", "would", "could"
}


class CodebaseAnalyzer:
    """Analyzes codebase to discover relevant files and functions for a feature."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize analyzer.

        Args:
            project_root: Root directory of project (defaults to repo root)
        """
        if project_root is None:
            # Default to repo root
            # This file is at: <project_root>/app/server/utils/codebase_analyzer/analyzer.py
            # So we need to go up 5 levels: analyzer.py -> codebase_analyzer -> utils -> server -> app -> project_root
            project_root = Path(__file__).parent.parent.parent.parent.parent

        self.project_root = Path(project_root)
        self.backend_root = self.project_root / "app" / "server"
        self.frontend_root = self.project_root / "app" / "client"

    def find_relevant_files(self, feature: Any) -> dict[str, Any]:
        """
        Find relevant files and functions for a feature.

        Args:
            feature: PlannedFeature object with title, description, etc.

        Returns:
            Dictionary with:
            - backend_files: List of (path, relevance_score) tuples
            - frontend_files: List of (path, relevance_score) tuples
            - test_files: List of suggested test file paths
            - related_functions: List of (file, function_name) tuples
            - suggested_locations: List of implementation suggestions
        """
        # Extract keywords from title and description
        keywords = self._extract_keywords(feature.title, feature.description or "")

        # Search for relevant files
        backend_files = self._search_python_files(keywords)
        frontend_files = self._search_ts_files(keywords)

        # Find related functions
        related_functions = self._find_functions(keywords)

        # Suggest test locations
        test_files = self._suggest_test_files(backend_files, frontend_files)

        # Suggest implementation locations
        suggested_locations = self._suggest_locations(feature, backend_files, frontend_files)

        return {
            "backend_files": backend_files,
            "frontend_files": frontend_files,
            "test_files": test_files,
            "related_functions": related_functions,
            "suggested_locations": suggested_locations,
        }

    def _extract_keywords(self, title: str, description: str) -> list[str]:
        """
        Extract keywords from title and description.

        Args:
            title: Feature title
            description: Feature description

        Returns:
            List of keywords (lowercase, no stopwords, max 10)
        """
        # Combine title and description
        text = f"{title} {description}".lower()

        # Extract words (alphanumeric + underscores)
        words = re.findall(r'\w+', text)

        # Filter out stopwords and short words
        keywords = [
            word for word in words
            if word not in STOPWORDS and len(word) > 2
        ]

        # Count frequency and take top 10 most common
        word_freq: dict[str, int] = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and take top 10
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [word for word, _ in sorted_keywords[:10]]

        return top_keywords

    def _search_python_files(self, keywords: list[str]) -> list[tuple[str, float]]:
        """
        Search Python files for keyword matches.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of (relative_path, relevance_score) tuples, sorted by score
        """
        if not self.backend_root.exists():
            return []

        results: list[tuple[str, float]] = []

        # Search in key backend directories
        search_patterns = [
            "**/*.py",
        ]

        # Directories to exclude
        exclude_dirs = {"__pycache__", ".venv", "venv", "node_modules", ".git", ".pytest_cache"}

        for pattern in search_patterns:
            for file_path in self.backend_root.glob(pattern):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                # Skip __init__.py files (usually not implementation files)
                if file_path.name == "__init__.py":
                    continue

                # Calculate relevance score
                score = self._calculate_file_score(file_path, keywords)

                if score > 0:
                    relative_path = str(file_path.relative_to(self.project_root))
                    results.append((relative_path, score))

        # Sort by score (highest first) and limit to top 10
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:10]

    def _search_ts_files(self, keywords: list[str]) -> list[tuple[str, float]]:
        """
        Search TypeScript/TSX files for keyword matches.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of (relative_path, relevance_score) tuples, sorted by score
        """
        if not self.frontend_root.exists():
            return []

        results: list[tuple[str, float]] = []

        # Search for TypeScript and TSX files
        search_patterns = [
            "**/*.ts",
            "**/*.tsx",
        ]

        # Directories to exclude
        exclude_dirs = {"node_modules", ".git", "dist", "build", ".next"}

        for pattern in search_patterns:
            for file_path in self.frontend_root.glob(pattern):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                # Calculate relevance score
                score = self._calculate_file_score(file_path, keywords)

                if score > 0:
                    relative_path = str(file_path.relative_to(self.project_root))
                    results.append((relative_path, score))

        # Sort by score (highest first) and limit to top 10
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:10]

    def _calculate_file_score(self, file_path: Path, keywords: list[str]) -> float:
        """
        Calculate relevance score for a file based on keywords.

        Args:
            file_path: Path to file
            keywords: Keywords to search for

        Returns:
            Relevance score (0.0 = no match, higher = more relevant)
        """
        try:
            content = file_path.read_text(errors='ignore').lower()
        except Exception:
            return 0.0

        score = 0.0

        # Check filename (higher weight)
        filename = file_path.stem.lower()
        for keyword in keywords:
            if keyword in filename:
                score += 3.0  # Filename match is highly relevant

        # Check file content
        for keyword in keywords:
            # Count occurrences (diminishing returns after 5 mentions)
            occurrences = content.count(keyword)
            score += min(occurrences * 0.5, 2.5)

        return score

    def _find_functions(self, keywords: list[str]) -> list[tuple[str, str]]:
        """
        Find function/method names matching keywords.

        Args:
            keywords: Keywords to search for

        Returns:
            List of (relative_file_path, function_name) tuples
        """
        if not self.backend_root.exists():
            return []

        results: list[tuple[str, str]] = []

        # Search Python files for function definitions
        exclude_dirs = {"__pycache__", ".venv", "venv", "node_modules", ".git"}

        for file_path in self.backend_root.glob("**/*.py"):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue

            try:
                content = file_path.read_text(errors='ignore')
            except Exception:
                continue

            # Find function/method definitions
            # Matches: def function_name(...):
            function_pattern = r'^[ \t]*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            matches = re.finditer(function_pattern, content, re.MULTILINE)

            relative_path = str(file_path.relative_to(self.project_root))

            for match in matches:
                function_name = match.group(1)

                # Check if function name contains any keyword
                function_lower = function_name.lower()
                for keyword in keywords:
                    if keyword in function_lower:
                        results.append((relative_path, function_name))
                        break  # Only add once per function

        # Limit to top 15 results
        return results[:15]

    def _suggest_test_files(
        self,
        backend_files: list[tuple[str, float]],
        frontend_files: list[tuple[str, float]]
    ) -> list[str]:
        """
        Suggest test file paths based on implementation files.

        Args:
            backend_files: Backend implementation files
            frontend_files: Frontend implementation files

        Returns:
            List of suggested test file paths
        """
        suggestions = []

        # For each backend file, suggest corresponding test file
        for file_path, _ in backend_files[:5]:  # Limit to top 5
            if "test_" not in file_path and not file_path.endswith("_test.py"):
                # Convert app/server/foo/bar.py -> app/server/tests/foo/test_bar.py
                path = Path(file_path)

                # Remove app/server prefix
                if path.parts[:2] == ("app", "server"):
                    relative_parts = path.parts[2:]

                    # Add tests directory
                    test_path = Path("app/server/tests") / Path(*relative_parts[:-1]) / f"test_{path.name}"
                    suggestions.append(str(test_path))

        # For frontend files, suggest test files
        for file_path, _ in frontend_files[:5]:  # Limit to top 5
            if ".test." not in file_path and ".spec." not in file_path:
                # Convert app/client/src/foo/Bar.tsx -> app/client/src/foo/Bar.test.tsx
                path = Path(file_path)
                test_path = path.with_suffix(f".test{path.suffix}")
                suggestions.append(str(test_path))

        return suggestions[:10]  # Limit to 10 suggestions

    def _suggest_locations(
        self,
        feature: Any,
        backend_files: list[tuple[str, float]],
        frontend_files: list[tuple[str, float]]
    ) -> list[str]:
        """
        Suggest implementation locations based on feature type.

        Args:
            feature: PlannedFeature object
            backend_files: Relevant backend files
            frontend_files: Relevant frontend files

        Returns:
            List of implementation suggestions (human-readable strings)
        """
        suggestions = []

        # Determine feature category from keywords/type
        title_lower = feature.title.lower()
        desc_lower = (feature.description or "").lower()

        # Backend suggestions
        if "database" in title_lower or "schema" in title_lower or "migration" in title_lower:
            suggestions.append("Database: Consider migration in app/server/migrations/")

        if "api" in title_lower or "endpoint" in title_lower or "route" in title_lower:
            suggestions.append("API: Add route in app/server/routes/")

        if "service" in title_lower or "business logic" in desc_lower:
            suggestions.append("Service: Add logic in app/server/services/")

        if "repository" in title_lower or "data access" in desc_lower:
            suggestions.append("Repository: Add data layer in app/server/repositories/")

        # Frontend suggestions
        if "ui" in title_lower or "component" in title_lower or "display" in title_lower:
            suggestions.append("UI: Add component in app/client/src/components/")

        if "page" in title_lower or "view" in title_lower:
            suggestions.append("Frontend: Add page in app/client/src/pages/")

        if "hook" in title_lower:
            suggestions.append("Frontend: Add hook in app/client/src/hooks/")

        # If we found relevant files, suggest modifying them
        if backend_files and not suggestions:
            top_file = backend_files[0][0]
            suggestions.append(f"Modify existing: {top_file}")

        if frontend_files and len(suggestions) < 2:
            top_file = frontend_files[0][0]
            suggestions.append(f"Modify existing: {top_file}")

        # Default suggestion if nothing specific found
        if not suggestions:
            if feature.item_type == "bug":
                suggestions.append("Bug fix: Start by examining related test failures")
            else:
                suggestions.append("New feature: Consider creating new service/component")

        return suggestions[:5]  # Limit to 5 suggestions
