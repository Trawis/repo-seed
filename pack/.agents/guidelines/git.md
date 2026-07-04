# Git and Pull Request Guidance

**Document role**: Managed coding-agent guidance

**Sync destination**: `.agents/guidelines/git.md`

## Select the Repository Model

Follow the repository's project-specific instructions first.

- GitHub Flow uses one long-lived `main` or `master` branch. Normal work uses `feature/*` and targets the long-lived branch.
- Git Flow uses `main` plus `develop`. Normal work uses `feature/*` and targets `develop`; releases and urgent production fixes use repository-approved release or hotfix branches.
- When no model is documented, prefer GitHub Flow for libraries, documentation, templates, and solo repositories; use Git Flow only for applications that clearly maintain a separate integration branch.

Do not create a `develop` branch in a GitHub Flow repository.

## Preflight

Before creating a branch or pull request when tools are available:

- fetch and prune remotes;
- inspect the current branch and working tree;
- check existing local and remote branches;
- check open and recently merged pull requests.

Do not duplicate work that is already open or merged.

## Branches and Pull Requests

- Use lowercase kebab-case branch names.
- Use `feature/<short-description>` for normal work.
- Do not include usernames, dates, vague suffixes, or assistant/model names.
- Keep commits focused and use imperative messages.
- Create or propose a pull request when hosted review is available.
- Never auto-merge, bypass branch protection, approve your own pull request, or force-push a long-lived branch.
- Use concise PR titles and the repository's PR template.

If hosted tooling is unavailable, report the intended source branch, target branch, title, and validation instead of claiming a PR exists.
