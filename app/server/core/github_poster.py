"""
GitHub CLI integration for posting issues.
"""

import subprocess
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from core.data_models import GitHubIssue


class GitHubPoster:
    """
    GitHub CLI wrapper for posting issues with preview and confirmation.
    """

    def __init__(self, repo_url: Optional[str] = None):
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
        Post issue to GitHub via gh CLI.

        Args:
            issue: GitHubIssue object to post
            confirm: If True, show preview and request confirmation

        Returns:
            Issue number of created issue

        Raises:
            RuntimeError: If gh CLI is not available or posting fails
        """
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

        # Prepare gh command
        cmd = ["gh", "issue", "create"]

        # Add title
        cmd.extend(["--title", issue.title])

        # Add body
        cmd.extend(["--body", issue.body])

        # Add labels
        if issue.labels:
            cmd.extend(["--label", ",".join(issue.labels)])

        # Add repo if specified
        if self.repo_url:
            cmd.extend(["--repo", self.repo_url])

        # Execute command
        try:
            result = self._execute_gh_command(cmd)

            # Extract issue number from result
            # gh CLI returns the issue URL like: https://github.com/owner/repo/issues/123
            issue_url = result.strip()
            issue_number = int(issue_url.split("/")[-1])

            self.console.print(f"[green]✓ Issue created: {issue_url}[/green]")
            return issue_number

        except Exception as e:
            raise RuntimeError(f"Failed to post issue to GitHub: {str(e)}")

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
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"GitHub CLI command failed: {error_msg}")

    def _validate_gh_cli(self) -> bool:
        """
        Validate that gh CLI is installed and authenticated.

        Returns:
            True if gh CLI is ready, False otherwise
        """
        try:
            # Check if gh is installed
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True
            )

            # Check if authenticated
            subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                check=True
            )

            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
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
            raise RuntimeError(f"Failed to get repository info: {str(e)}")
