# Git and Pull Request Guidance

**Document role**: Managed coding-agent guidance

**Sync destination**: `.agents/guidelines/git.md`

## Select the Target Branch

Follow the repository's project-specific instructions first.

For normal work:

1. Target `develop` when it exists.
2. Otherwise target `dev` when it exists.
3. Otherwise target `main` or `master`.

Do not create a missing integration branch as a side effect of ordinary work. Use release or hotfix branches only when the repository explicitly documents them.

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
