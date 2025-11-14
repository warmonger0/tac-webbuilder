"""
Routes Analyzer Module

Scans FastAPI route definitions and extracts route metadata including:
- HTTP method (GET, POST, PUT, DELETE, PATCH)
- Route path
- Handler function name
- Route description from docstring
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RoutesAnalyzer:
    """Analyzes FastAPI application files to extract route information."""

    def __init__(self, server_file_path: str = "server.py"):
        """
        Initialize the routes analyzer.

        Args:
            server_file_path: Path to the main server file to analyze (relative to current directory)
        """
        # If path is not absolute and file doesn't exist, try to find it
        if not Path(server_file_path).is_absolute() and not Path(server_file_path).exists():
            # Try relative to current working directory
            cwd_path = Path.cwd() / server_file_path
            if cwd_path.exists():
                self.server_file_path = str(cwd_path)
            else:
                # Try relative to this module's directory
                module_dir = Path(__file__).parent.parent
                module_path = module_dir / server_file_path
                if module_path.exists():
                    self.server_file_path = str(module_path)
                else:
                    self.server_file_path = server_file_path
        else:
            self.server_file_path = server_file_path

    def analyze_routes(self) -> List[Dict[str, Any]]:
        """
        Analyze the server file and extract all route definitions.

        Returns:
            List of route dictionaries with keys: path, method, handler, description
        """
        try:
            routes = self._analyze_file(self.server_file_path)
            # Sort routes by path for consistent ordering
            routes.sort(key=lambda r: r['path'])
            return routes
        except FileNotFoundError:
            logger.error(f"Server file not found: {self.server_file_path}")
            return []
        except Exception as e:
            logger.error(f"Error analyzing routes: {e}")
            return []

    def _analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single Python file for FastAPI route decorators.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            List of route dictionaries
        """
        routes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Parse the file into an AST
            tree = ast.parse(file_content)

            # Visit all nodes in the module
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Check for route decorators
                    route_info = self._extract_route_from_decorators(node)
                    if route_info:
                        routes.append(route_info)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

        return routes

    def _extract_route_from_decorators(self, func_node) -> Optional[Dict[str, Any]]:
        """
        Extract route information from function decorators.

        Args:
            func_node: AST FunctionDef or AsyncFunctionDef node to analyze

        Returns:
            Dictionary with route info, or None if no route decorator found
        """
        for decorator in func_node.decorator_list:
            # Handle @app.get(), @app.post(), etc.
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    method = decorator.func.attr.upper()

                    # Check if this is a valid HTTP method
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        # Extract the route path (first argument)
                        if decorator.args:
                            path = self._extract_string_value(decorator.args[0])
                            if path:
                                description = self._extract_docstring(func_node)
                                return {
                                    'path': path,
                                    'method': method,
                                    'handler': func_node.name,
                                    'description': description
                                }

        return None

    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """
        Extract string value from an AST node.

        Args:
            node: AST node to extract string from

        Returns:
            String value or None
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Str):  # For Python < 3.8 compatibility
            return node.s
        return None

    def _extract_docstring(self, func_node) -> str:
        """
        Extract the first line of the docstring from a function.

        Args:
            func_node: AST FunctionDef or AsyncFunctionDef node

        Returns:
            First line of docstring, or "N/A" if no docstring
        """
        docstring = ast.get_docstring(func_node)
        if docstring:
            # Return first line only
            first_line = docstring.split('\n')[0].strip()
            return first_line if first_line else "N/A"
        return "N/A"
