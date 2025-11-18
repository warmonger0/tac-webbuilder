# Create Pull Request

Based on the `Instructions` below, take the `Variables` follow the `Run` section to create a pull request. Then follow the `Report` section to report the results of your work.

## Variables

adw_id: $1

## Instructions

- **IMPORTANT: Read `.adw-context.json` from the worktree root** to get pre-computed data:
  - `branch_name` - current branch to push
  - `changed_files` - list of modified files
  - `commits` - commit history (array of {sha, message})
  - `plan_file` - implementation plan file path
  - `issue` - GitHub issue data (number, title, body, type)
- DO NOT run `git diff` or `git log` commands - all info is pre-computed
- Generate a pull request title in the format: `<issue_type>: #<issue_number> - <issue_title>`
- The PR body should include:
  - A summary section with the issue context
  - Link to the implementation `plan_file` from context
  - Reference to the issue (Closes #<issue_number>)
  - ADW tracking ID
  - A checklist of what was done
  - A summary of key changes made
- Extract issue number, type, and title from the issue data in context
- Examples of PR titles:
  - `feat: #123 - Add user authentication`
  - `bug: #456 - Fix login validation error`
  - `chore: #789 - Update dependencies`
  - `test: #1011 - Test xyz`
- Don't mention Claude Code in the PR body - let the author get credit for this.

## Run

1. Review pre-computed data from context file (changed_files, commits already available)
2. Run `git push -u origin {branch_name}` to push the branch (use branch_name from context)
3. Set GH_TOKEN environment variable from GITHUB_PAT if available, then run `gh pr create --title "<pr_title>" --body "<pr_body>" --base main` to create the PR
4. Capture the PR URL from the output

## Report

Return ONLY the PR URL that was created (no other text)