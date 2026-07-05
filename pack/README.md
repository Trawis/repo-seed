# Repo Seed Pack

Package-only instructions for the downloadable documentation pack. This file and `LICENSE` are included in the archive but are never synchronized into target repositories.

## First Sync

From the directory containing the extracted `pack/` folder:

```bash
python pack/files/scripts/sync-docs.py \
  --target /path/to/project \
  --profile app \
  --dry-run
```

Choose `minimal`, `library`, `app`, `game`, or `full`. Add only the scaffolding you need:

```text
--scaffold-project-files
--scaffold-github-templates
--scaffold-editorconfig
```

Review the dry-run output, commit or back up the target repository, then rerun without `--dry-run`. Managed guidance and templates are overwritten; existing project-owned files are preserved.

## Update an Existing Project

Use the sync script already copied into the target with a newer extracted pack:

```bash
python scripts/sync-docs.py \
  --source /path/to/extracted/pack \
  --target . \
  --profile app \
  --dry-run
```

For complete documentation, visit [repo-seed on GitHub](https://github.com/Trawis/repo-seed).

## License

This pack is distributed under the MIT License. See `LICENSE`.
