"""
GitHub CLI integration for posting issues.
"""

import logging
import os

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from utils.process_runner import ProcessRunner

from core.data_models import GitHubIssue


class GitHubPoster:
    """
    GitHub CLI wrapper for posting issues with preview and confirmation.
    """

    def __init__(self, repo_url: str | None = None):
        """
        Initialize GitHub poster.

        Args:
            repo_url: GitHub repository URL (optional, uses current repo if None)
        """
        self.repo_url = repo_url
        self.console = Console()

    def format_preview(self, issue: GitHubIssue) -> str:
        """
        Create a rich terminal preview of the issue.

        Args:
            issue: GitHubIssue object

        Returns:
            Formatted preview string
        """
        preview_parts = [
            f"## Title: {issue.title}",
            "",
            f"**Classification:** {issue.classification}",
            f"**Labels:** {', '.join(issue.labels)}",
            f"**Workflow:** {issue.workflow} model_set {issue.model_set}",
            "",
            "---",
            "",
            issue.body
        ]

        return "\n".join(preview_parts)

    def post_issue(self, issue: GitHubIssue, confirm: bool = True) -> int:
        """
        Post issue to GitHub via gh CLI with automatic REST API fallback.

        Attempts to use GraphQL API (gh CLI) first, but automatically falls back
        to REST API if GraphQL rate limit is exhausted.

        Args:
            issue: GitHubIssue object to post
            confirm: If True, show preview and request confirmation

        Returns:
            Issue number of created issue

        Raises:
            RuntimeError: If both GraphQL and REST API fail
        """
        logger = logging.getLogger(__name__)

        # Validate gh CLI is available
        if not self._validate_gh_cli():
            raise RuntimeError(
                "GitHub CLI (gh) is not installed or not authenticated. "
                "Please install gh CLI and run 'gh auth login'."
            )

        # Show preview if confirmation is requested
        if confirm:
            self._show_preview(issue)
            response = input("\nPost this issue to GitHub? (y/n): ").strip().lower()
            if response not in ["y", "yes"]:
                self.console.print("[yellow]Issue posting cancelled.[/yellow]")
                raise RuntimeError("User cancelled issue posting")

        # Ensure labels exist before creating issue (works for both APIs)
        if issue.labels:
            self._ensure_labels_exist(issue.labels)

        # Prepare gh command for GraphQL attempt
        cmd = ["gh", "issue", "create"]
        cmd.extend(["--title", issue.title])
        cmd.extend(["--body", issue.body])

        if issue.labels:
            cmd.extend(["--label", ",".join(issue.labels)])

        if self.repo_url:
            cmd.extend(["--repo", self.repo_url])

        # Try GraphQL API first (gh CLI)
        try:
            result = self._execute_gh_command(cmd)

            # Extract issue number from result
            # gh CLI returns the issue URL like: https://github.com/owner/repo/issues/123
            issue_url = result.strip()
            issue_number = int(issue_url.split("/")[-1])

            logger.info(f"Created GitHub issue via GraphQL: {issue_url}")
            self.console.print(f"[green]✓ Issue created (GraphQL): {issue_url}[/green]")
            return issue_number

        except Exception as e:
            error_str = str(e).lower()

            # Detect rate limit errors from GraphQL API
            if "rate limit" in error_str or "api rate limit exceeded" in error_str:
                logger.warning(
                    f"GraphQL API rate limit hit, falling back to REST API: {e}"
                )
                self.console.print(
                    "[yellow]⚠️  GraphQL rate limit exhausted, using REST API fallback...[/yellow]"
                )

                try:
                    return self._post_issue_via_rest(issue)
                except Exception as rest_error:
                    raise RuntimeError(
                        f"Failed with both GraphQL and REST APIs. "
                        f"GraphQL: {str(e)} | REST: {str(rest_error)}"
                    ) from rest_error

            # Other errors - don't fallback, just propagate
            raise RuntimeError(f"Failed to post issue to GitHub: {str(e)}") from e

    def _ensure_labels_exist(self, labels: list):
        """
        Ensure all labels exist in the repository, create them if they don't.

        Args:
            labels: List of label names to ensure exist
        """
        # Get existing labels
        try:
            cmd = ["gh", "label", "list", "--json", "name"]
            if self.repo_url:
                cmd.extend(["--repo", self.repo_url])

            result = self._execute_gh_command(cmd)
            import json
            existing_labels = {label["name"] for label in json.loads(result)}

            # Create missing labels
            for label in labels:
                if label not in existing_labels:
                    self._create_label(label)

        except Exception as e:
            # If we can't check labels, log warning but don't fail
            # The issue creation will proceed and fail gracefully if labels don't exist
            self.console.print(f"[yellow]Warning: Could not verify labels: {str(e)}[/yellow]")

    def _create_label(self, label: str):
        """
        Create a label in the repository.

        Args:
            label: Label name to create
        """
        # Define colors for common label types
        label_colors = {
            "feature": "0e8a16",  # Green
            "bug": "d73a4a",      # Red
            "chore": "fbca04",    # Yellow
        }

        color = label_colors.get(label, "ededed")  # Default gray

        try:
            cmd = ["gh", "label", "create", label, "--color", color]
            if self.repo_url:
                cmd.extend(["--repo", self.repo_url])

            self._execute_gh_command(cmd)
            self.console.print(f"[green]✓ Created label: {label}[/green]")

        except Exception as e:
            # If label creation fails, warn but don't fail the whole operation
            self.console.print(f"[yellow]Warning: Could not create label '{label}': {str(e)}[/yellow]")

    def _show_preview(self, issue: GitHubIssue):
        """
        Display rich preview of the issue in terminal.

        Args:
            issue: GitHubIssue to preview
        """
        preview = self.format_preview(issue)

        # Display with rich
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(preview),
            title="[bold blue]GitHub Issue Preview[/bold blue]",
            border_style="blue"
        ))

    def _execute_gh_command(self, cmd: list) -> str:
        """
        Execute a gh CLI command.

        Args:
            cmd: Command list to execute

        Returns:
            Command output

        Raises:
            RuntimeError: If command fails
        """
        # Extract gh args (remove 'gh' prefix if present)
        args = cmd[1:] if cmd[0] == "gh" else cmd

        result = ProcessRunner.run_gh_command(args)

        if not result.success:
            error_msg = result.stderr if result.stderr else f"Command failed with code {result.returncode}"
            raise RuntimeError(f"GitHub CLI command failed: {error_msg}")

        return result.stdout

    def _validate_gh_cli(self) -> bool:
        """
        Validate that gh CLI is installed and authenticated.

        Returns:
            True if gh CLI is ready, False otherwise
        """
        # Check if gh is installed
        version_result = ProcessRunner.run_gh_command(["--version"])
        if not version_result.success:
            return False

        # Check if authenticated
        auth_result = ProcessRunner.run_gh_command(["auth", "status"])
        return auth_result.success

    def _get_github_token(self) -> str:
        """
        Get GitHub authentication token for REST API calls.

        Priority:
        1. GITHUB_PAT environment variable (explicit configuration)
        2. GH_TOKEN environment variable (alternative)
        3. Extract from gh CLI (gh auth token command)

        Returns:
            GitHub personal access token

        Raises:
            RuntimeError: If no token available
        """
        # Try environment variables first (explicit configuration)
        token = os.getenv("GITHUB_PAT") or os.getenv("GH_TOKEN")
        if token:
            return token

        # Try extracting from gh CLI
        try:
            result = ProcessRunner.run_gh_command(["auth", "token"])
            if result.success and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass

        raise RuntimeError(
            "No GitHub token available. Set GITHUB_PAT environment variable "
            "or authenticate with 'gh auth login'"
        )

    def _post_issue_via_rest(self, issue: GitHubIssue) -> int:
        """
        Post issue using GitHub REST API (fallback when GraphQL exhausted).

        This method provides a fallback when the GraphQL API rate limit is exhausted.
        Uses httpx for HTTP requests following existing codebase patterns.

        Args:
            issue: GitHubIssue object to post

        Returns:
            Issue number of created issue

        Raises:
            RuntimeError: If REST API call fails
        """
        import httpx

        logger = logging.getLogger(__name__)

        try:
            # Get authentication token
            token = self._get_github_token()

            # Get repository information
            repo_info = self.get_repo_info()
            owner = repo_info['owner']['login']
            repo_name = repo_info['name']

            # Prepare REST API request
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            payload = {
                "title": issue.title,
                "body": issue.body,
            }

            # Add labels if provided
            if issue.labels:
                payload["labels"] = issue.labels

            # Make REST API request (synchronous, following existing patterns)
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

            # Parse response
            issue_data = response.json()
            issue_number = issue_data['number']
            issue_url = issue_data['html_url']

            logger.info(f"Created GitHub issue via REST API: {issue_url}")
            self.console.print(f"[green]✓ Issue created (REST API): {issue_url}[/green]")

            return issue_number

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = f": {e.response.json().get('message', '')}"
            except Exception:
                pass
            raise RuntimeError(
                f"GitHub REST API returned {e.response.status_code}{error_detail}"
            ) from e
        except httpx.TimeoutException as e:
            raise RuntimeError("GitHub REST API request timed out") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to connect to GitHub REST API: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to post issue via REST API: {str(e)}") from e

    def issue_exists(self, issue_number: int) -> bool:
        """
        Check if a GitHub issue exists.

        Args:
            issue_number: Issue number to check

        Returns:
            True if issue exists, False otherwise
        """
        try:
            cmd = ["gh", "issue", "view", str(issue_number), "--json", "number"]
            if self.repo_url:
                cmd.extend(["--repo", self.repo_url])

            result = self._execute_gh_command(cmd)
            return bool(result.strip())
        except Exception:
            # If command fails (issue not found, rate limit, etc.), assume doesn't exist
            return False

    def get_repo_info(self) -> dict:
        """
        Get information about the current/specified repository.

        Returns:
            Dictionary with repository information

        Raises:
            RuntimeError: If unable to get repo info
        """
        try:
            cmd = ["gh", "repo", "view", "--json", "name,owner,url"]
            if self.repo_url:
                cmd.append(self.repo_url)

            result = self._execute_gh_command(cmd)

            import json
            return json.loads(result)

        except Exception as e:
            raise RuntimeError(f"Failed to get repository info: {str(e)}") from e
