/**
 * GitHub Integration Configuration
 *
 * This module provides centralized configuration for GitHub integration,
 * including repository URLs and helper functions for generating issue/PR URLs.
 */

import type { GitHubConfig } from './types';

/**
 * Get GitHub repository owner from environment variable or default
 */
function getRepoOwner(): string {
  return import.meta.env.VITE_GITHUB_REPO_OWNER || 'warmonger0';
}

/**
 * Get GitHub repository name from environment variable or default
 */
function getRepoName(): string {
  return import.meta.env.VITE_GITHUB_REPO_NAME || 'tac-webbuilder';
}

/**
 * Build the full repository URL
 */
function getRepoUrl(): string {
  const owner = getRepoOwner();
  const name = getRepoName();
  return `https://github.com/${owner}/${name}`;
}

/**
 * Get the full URL for a specific issue
 * @param issueNumber - The issue number
 * @returns Full GitHub issue URL
 */
function getIssueUrl(issueNumber: number): string {
  return `${getRepoUrl()}/issues/${issueNumber}`;
}

/**
 * Get the full URL for a specific pull request
 * @param prNumber - The pull request number
 * @returns Full GitHub pull request URL
 */
function getPullRequestUrl(prNumber: number): string {
  return `${getRepoUrl()}/pull/${prNumber}`;
}

/**
 * GitHub configuration object
 */
export const githubConfig: GitHubConfig = {
  /** GitHub repository owner username */
  REPO_OWNER: getRepoOwner(),

  /** GitHub repository name */
  REPO_NAME: getRepoName(),

  /** Full repository URL */
  REPO_URL: getRepoUrl(),

  /** Issues URL template */
  ISSUES_URL: `${getRepoUrl()}/issues`,

  /** Pull requests URL template */
  PULLS_URL: `${getRepoUrl()}/pulls`,

  /** Helper function to get issue URLs */
  getIssueUrl,

  /** Helper function to get PR URLs */
  getPullRequestUrl,
};

/**
 * Default export for convenient importing
 */
export default githubConfig;
