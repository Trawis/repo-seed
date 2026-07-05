# Git and Pull Request Guidance

**Document role**: Managed coding-agent guidance

**Sync destination**: `.agents/guidelines/git.md`

## Select the Target Branch

Follow the repository's project-specific instructions first.

Use the hosted default branch when the repository does not document a different integration branch. Do not infer Git Flow, trunk-based development, release branches, or hotfix branches from branch names alone. Do not create a missing long-lived branch as a side effect of ordinary work.

## Preflight

Before creating a branch or pull request when tools are available:

- fetch and prune remotes;
- inspect the current branch and working tree;
- check existing local and remote branches;
- check open and recently merged pull requests.

Do not duplicate work that is already open or merged.

## Branches and Pull Requests

- Follow the repository's branch naming convention.
- When none exists, use a short lowercase kebab-case name with a meaningful category such as `feature/`, `fix/`, or `docs/`.
- Do not include usernames, dates, vague suffixes, or assistant/model names.
- Keep commits focused and use imperative messages.
- Create or propose a pull request when hosted review is available.
- Never auto-merge, bypass branch protection, approve your own pull request, or force-push a long-lived branch.
- Use concise PR titles and the repository's PR template.

If hosted tooling is unavailable, report the intended source branch, target branch, title, and validation instead of claiming a PR exists.
