# Windows Chezmoi Dotfiles

Edit chezmoi sources in the checkout selected by `dot_codex/AGENTS.md`, not
their deployed copies under `%USERPROFILE%`. Preserve unrelated source changes
and intentional target drift.

## Workflow

1. Inspect the branch, worktrees, and status; follow the Git workflow in
   `dot_codex/AGENTS.md`. Use the absolute task checkout with every chezmoi command.
2. Map each affected source to one absolute deployed file path. Before editing,
   inspect both files and run `chezmoi --source <absolute-task-checkout> diff --
   <absolute-target>`. Preserve intentional target changes in the source.
   For a new target, verify it is absent or preserve its existing contents before
   adding the source; chezmoi reports unmanaged targets as `not managed`.
3. Edit only the sources. Run focused application validation, review each target
   diff, and commit the task changes before requesting rebase and merge approval.
4. After every approved merge, apply every affected managed file from the merged
   source checkout: `chezmoi --source <absolute-merged-checkout> apply --
   <absolute-target>`, separately for each file. Merge approval authorizes this
   deployment. An explicit deployment request also authorizes exact-target apply
   from the task checkout; report which checkout was used.
5. Run the affected application's validation again and verify each target with
   `chezmoi --source <absolute-applied-checkout> diff -- <absolute-target>`.
   Inspect `chezmoi --source <absolute-applied-checkout> status`; resolve or report
   remaining differences while preserving unrelated drift.
6. Complete Git cleanup as specified in `dot_codex/AGENTS.md`. Report the checkout,
   branch, commit, checks, applied targets, and any remaining dirt or blockers.
   Completion requires all affected targets applied and verified, plus task cleanup.

Use one absolute file target per command. Never run `chezmoi apply --force`, a
broad apply, or an apply with directory/glob targets. Repository synchronization
requires an explicit request and does not authorize a broad apply. Push requires
a separate request.

If the configured diff command or pager is unavailable, use
`chezmoi --source <absolute-task-checkout> --use-builtin-diff --no-pager diff --
<absolute-target>` for review and verification. Do not depend on POSIX `cat`.

## Guidance sources

- Keep root `CLAUDE.md` identical to this file; both are repository-only guidance.
- Global guidance lives in `dot_codex/AGENTS.md`. Its targets are
  `%USERPROFILE%\.codex\AGENTS.md` and `%USERPROFILE%\.claude\CLAUDE.md`;
  validate and apply both separately. `dot_claude/CLAUDE.md.tmpl` includes that
  source, so edit only `dot_codex/AGENTS.md` for global guidance.
- Nushell guidance lives in `AppData/Roaming/nushell/AGENTS.md` and deploys to
  `%APPDATA%\nushell\AGENTS.md`. Its sibling `CLAUDE.md.tmpl` includes it;
  validate and apply `%APPDATA%\nushell\CLAUDE.md` separately too.
- Keep root guidance, `README.md`, `docs/`, and tests out of the deployed home.

## Windows compatibility

Use native Windows paths, tools, and credentials. Do not import Linux absolute
paths, Linuxbrew commands, POSIX-only helpers, or Linux credential helpers.
Guard optional commands so their absence cannot prevent Nushell or PowerShell
from starting. Follow the local Nushell guidance for parser-time imports.

For Markdown instruction changes, validate template rendering, shared copies,
and managed/ignored paths. For shell changes, validate the source and deployed
startup behavior with the actual application.

## Context

- Before codebase exploration, read `docs/agents/domain.md`.
- For specs, tickets, or triage, use GitHub Issues in `vimkim/dotfiles-windows`;
  first read `docs/agents/issue-tracker.md`.
- When assigning triage roles, read `docs/agents/triage-labels.md`.
