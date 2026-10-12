# Global Agent Guidance

## Working preferences

- Clarify only ambiguities that change the outcome, scope, or risk; resolve
  routine, reversible details with stated assumptions. Honor existing session
  authorization without requesting the same approval again.
- For work expected to last at least 30 minutes, cross sessions, use parallel
  agents, or wait on an external queue, use `work-tracker` when available.
  Otherwise, keep concise task notes with progress, blockers, and next steps in
  the repository's established location; do not require an unavailable skill.

## Windows environment

This is native Windows. Use PowerShell or Nushell and Windows-native tools.
Resolve home and application directories with `%USERPROFILE%`, `%APPDATA%`, and
`%LOCALAPPDATA%` (PowerShell: `$env:USERPROFILE`, `$env:APPDATA`, and
`$env:LOCALAPPDATA`; Nushell: `$nu.home-dir`, `$env.APPDATA`, and
`$env.LOCALAPPDATA`). Quote paths containing spaces and pass paths as arguments.
Treat these examples as shell-specific syntax, not interchangeable expressions.

Do not assume Bash, WSL, X11, Linuxbrew, POSIX helpers, or Linux credential
helpers are available. Prefer native tools and existing Windows credentials.
Guard optional commands, imports, and integrations so shell startup still
succeeds when they are absent. In Nushell, `source` and `use` resolve at parse
time; a runtime `if` cannot guard a missing import.

Use headless automation for background work. When starting background helpers
with PowerShell `Start-Process`, use `-WindowStyle Hidden` unless the user asks
for an interactive window. Use interactive Windows applications when needed
for the user's task.

Use native PowerShell file operations with `-LiteralPath` for moves and deletes.
Before recursive cleanup, verify the resolved absolute target stays within the
intended workspace or explicitly named directory. Do not pipe computed paths
into another shell's deletion or move commands.

## Git workflow

1. Inspect the current branch, worktrees, and status. Preserve unrelated user
   changes throughout.
2. Choose the checkout by the starting branch:
   - `main`, `develop`, or `feature/*`: create or reuse a sibling task worktree
     with a separate topic branch based on that branch. Record the starting
     branch as the merge destination. Quote absolute Windows worktree paths.
   - Any other named branch: work directly in the current checkout; do not
     create another worktree. For later integration, use the repository's
     documented or agreed destination.
   - Detached HEAD: preserve the current commit and create a named task branch;
     establish the destination before integration.
3. Run focused checks, inspect the diff, and commit all meaningful task changes
   before review; local task commits are authorized. Stage only task files;
   ignore only disposable outputs with narrow `.gitignore` rules. Report the
   checkout, branch, commit, checks, limitations, and unrelated dirt.
4. Request one approval to rebase onto the current local destination branch and
   fast-forward merge locally, unless that integration is already explicitly
   authorized. Push requires a separate explicit request. Deployment requires
   an explicit request unless repository guidance already authorizes it as part
   of merge approval.
5. After approval, verify the destination checkout is clean and on the expected
   branch. Rebase the task branch, resolve conflicts, inspect the diff, and run
   proportionate checks. Ask again only when uncertain about the result or a
   failure's impact; report understood failures. Merge with
   `git merge --ff-only <rebased-task-commit>`. If the destination advances,
   repeat under the same approval.
6. After every successful rebase and fast-forward merge, complete repository
   post-merge steps (including deployment), then clean up: verify the task tip
   is included in the destination and preserve valuable uncommitted or ignored
   files. From outside the merged linked task worktree, run
   `git worktree remove <absolute-task-worktree>`, then safely delete the task
   branch with `git branch -d <task-branch>`. Close task-owned processes or shells
   holding Windows file handles if needed; report an obstacle rather than
   forcing removal. Clean up only this task's worktree and branch, without
   force. Finish with a clean destination checkout. Remote branch deletion
   requires an explicit request.

Grilling sessions or errors may leave work uncommitted; report the remaining
changes and next step.

## Task context

- Daily or weekly planning: use `daily-schedule` and `work-tracker` when
  available. Use an existing Windows schedule directory, such as
  `%USERPROFILE%\temp\todays-schedule` if present; resolve its actual location
  instead of assuming the Linux server's directory.
- CUBRID tasks: if `%USERPROFILE%\my-cubrid\CUBRID.md` exists, read it first;
  its personal policies override conflicting repository guidance. If the
  Windows checkout uses another location, resolve that location instead of
  requiring an absent file.
