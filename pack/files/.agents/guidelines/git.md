# Git and Pull Request Guidance

**Document role**: Managed coding-agent guidance
**Sync destination**: `.agents/guidelines/git.md`

Follow repository-specific instructions and hosted settings first.

## Before Starting

When tooling is available:

- inspect the current branch and working tree;
- fetch and prune remotes;
- check relevant branches and open or recently merged pull requests.

Do not duplicate existing work or create a missing long-lived branch implicitly.

## Branches, Commits, and Pull Requests

- Use the repository's branching and naming conventions.
- Otherwise branch from the hosted default branch with a short lowercase kebab-case name.
- Keep commits focused and imperative.
- Keep PR titles and descriptions concise and use the repository template.
- Never force-push a long-lived branch, bypass protection, auto-merge, or approve your own PR.
- Do not include assistant, model, or tool names in repository history or release text.

If hosted tooling is unavailable, report the intended source branch, target, title, and validation without claiming a PR exists.
