# Issue Tracker: GitHub

Specs and tickets live in GitHub Issues in `vimkim/dotfiles-windows`.
Use an available GitHub integration or the optional native `gh` CLI with
`--repo vimkim/dotfiles-windows`. Check tool availability before calling it;
do not require GitHub CLI for local dotfile work. Keep long-running work status
and history in `work-tracker` when available, otherwise use the established
task notes; link relevant issues.

## Operations

Append `--repo vimkim/dotfiles-windows` to the commands below when using `gh`.
Perform writes only when authorized by the task or an explicitly invoked
workflow.

- Publish a spec or ticket: `gh issue create --title TITLE --body-file FILE`.
- Fetch a ticket and discussion: `gh issue view NUMBER --comments`.
- Read structured context: `gh issue view NUMBER --json number,title,body,comments,labels,state,assignees`.
- List open tickets: `gh issue list --state open --json number,title,body,labels,assignees`; filter by label when needed.
- Comment: `gh issue comment NUMBER --body-file FILE`.
- Apply or remove labels: `gh issue edit NUMBER --add-label LABEL` or `--remove-label LABEL`.
- Complete a ticket: `gh issue close NUMBER --reason completed`; use `--reason "not planned"` for declined work.

Use a temporary UTF-8 body file for multiline Markdown so actual newlines are
preserved. In PowerShell, write its contents with `Set-Content -LiteralPath
<body-file> -Encoding utf8` and pass the quoted path with `--body-file`.
Use the label mapping in `triage-labels.md`; inspect existing labels before
adding missing mapped labels.

## Parents and blockers

Create blocker tickets first. Use native parent and blocker relationships when
the available GitHub integration supports them. For CLI operations, inspect
the installed `gh issue create --help` and `gh issue edit --help` before using
relationship flags; do not assume the Linux CLI's flags are present on Windows.

If native relationships are unavailable, use `Part of #PARENT` and
`Blocked by: #BLOCKER, #BLOCKER` in the child body. A ticket is ready only when
every blocker is closed.

## Wayfinding

The map is one issue labelled `wayfinder:map`; children use
`wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or
`wayfinder:task`, with parent and blocker relationships as above.

Choose an open, unassigned child whose blockers are closed, in map order.
When authorized to claim it, use `gh issue edit NUMBER --add-assignee '@me'`
or the equivalent available integration. Resolve it by posting its answer,
closing it, and adding a short answer and issue link to the map's Decisions-so-far.

## Pull requests

Use issues as the request surface. GitHub issues and PRs share a number space.
Resolve ambiguous references with `gh pr view NUMBER`, falling back to
`gh issue view NUMBER`, or use the corresponding available integration.
