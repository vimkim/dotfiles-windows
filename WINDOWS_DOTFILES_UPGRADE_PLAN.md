# Windows Dotfiles Upgrade Plan

## Goal

Bring this Windows chezmoi repository up to the useful parts of
`../dotfiles-linux` while keeping Windows-native paths, terminal behavior, and
tooling. The Linux repository is a reference, not a file-for-file source.

The first outcome should be a reproducible, error-free shell and Zellij setup.
Cosmetic synchronization and optional applications come later.

## Audit snapshot

Audit date: 2026-07-24

Installed core versions:

- chezmoi 2.70.0
- Nushell 0.114.1
- Zellij 0.44.3
- Starship 1.24.2
- mise 2026.7.11
- Atuin 18.17.1

Important findings:

- `zellij setup --check` accepts the deployed config and confirms the Windows
  config/layout root is `%APPDATA%\Zellij\config`.
- The deployed Zellij tree has no managed plugins directory.
- All Windows layouts load `zjstatus.wasm` from
  `~/temp/zjstatus/zjstatus.wasm`, so they depend on an unmanaged local file.
- `config.kdl` also references
  `zellij-new-tab-next-to-current.wasm`, but no source or deployed plugin file
  exists.
- The Linux repository manages pinned `zjstatus` and vertical-tabs plugins
  through `.chezmoiexternal.toml`.
- Linux has newer Zellij session/layout selection and race-free asynchronous
  tab renaming in `private_dot_config/nushell/zellij.nu`.
- The Windows Nu config unconditionally imports or runs mise, eza, Atuin,
  Starship, and Fastfetch. Optional parser-time imports can prevent Nu from
  starting on a fresh machine.
- Starting the current PowerShell profile reports a missing
  `Set-PSFzfOption` command. The profile also mutates the persistent user
  `PATH` on every shell startup.
- Several Windows Nu aliases still point to Linux-only paths such as
  `~/.config/my-scripts/bin/*.sh`.
- The Alacritty config imports a Frappe theme that is not present in this
  repository; only the Mocha theme is managed.
- The Windows Git config lacks the useful editor/diff/merge defaults from
  Linux, but Linux credential-helper paths must not be copied.
- Before this plan was added, the source Git worktree was clean. The deployed
  chezmoi targets already had local drift in:
  - `.config/mise/config.toml`
  - Windows Terminal `settings.json`
  - Nushell `alias.nu`
  - Nushell `config.nu`

## Upgrade rules

1. Preserve the four locally modified targets before applying anything.
2. Never use `chezmoi apply --force`.
3. Do not run a broad `chezmoi apply`; apply and verify one target or one
   tightly related component at a time.
4. Do not copy `/home/...`, Linuxbrew, POSIX shell commands, X11/Wayland
   assumptions, or Linux credential helpers into Windows files.
5. Preserve recent Windows work, especially the corrected Zellij
   `config/layouts` location, native fonts, WSL launch choices, acrylic
   settings, and Windows-specific Claude layouts.
6. Treat optional commands as optional: a missing utility must disable only
   its integration, not break shell startup.
7. Split the implementation into reviewable commits and keep deployment
   separate from source changes.

## Phase 0: Make the repository and rollout safe

Files:

- `.chezmoiignore`
- `.gitignore`
- `README.md`
- optionally `AGENTS.md`

Tasks:

- Add `.chezmoiignore` entries for repository-only documents, including this
  plan, `README.md`, and `AGENTS.md`, so they are not installed into the home
  directory.
- Ignore Zellij runtime lock/heartbeat files and other generated caches.
- Document Windows prerequisites, source/target path mappings, and targeted
  apply examples.
- Save `chezmoi diff` for the four drifted targets and decide each hunk
  explicitly:
  - preserve the deployed change by bringing it into the source;
  - retain the source version intentionally; or
  - merge both.
- In particular, preserve the current Windows Terminal profile/GUID changes
  and resolve the mise `python` versus `rust` difference intentionally.
- Add repository guidance equivalent to the Linux safety rules: edit source
  files, apply exact targets, and never use a broad forced apply.

Validation:

- `chezmoi status` has only understood entries.
- `chezmoi diff` contains no surprise deletions.
- Repository documents do not appear in `chezmoi managed`.

## Phase 1: Repair and modernize Zellij

Reference:

- `../dotfiles-linux/private_dot_config/zellij`
- `../dotfiles-linux/private_dot_config/nushell/zellij.nu`
- `../dotfiles-linux/private_dot_config/my-scripts/bin/executable_zellij-attach-or-new.sh`

Files:

- `AppData/Roaming/zellij/config/.chezmoiexternal.toml`
- `AppData/Roaming/zellij/config/config.kdl`
- `AppData/Roaming/zellij/config/layouts/*.kdl`
- `AppData/Roaming/nushell/zellij.nu`
- `AppData/Roaming/nushell/alias.nu`

Tasks:

- Add a Windows Zellij external manifest rooted at the actual config directory.
- Pin and manage:
  - `zjstatus.wasm` v0.22.0;
  - `zellij-vertical-tabs.wasm` v0.1.0.
- Resolve `zellij-new-tab-next-to-current.wasm` instead of leaving a dangling
  reference:
  - pin a verified release artifact if one exists; or
  - remove the plugin binding and use built-in `NewTab`.
- Put all external plugins under one reproducible path such as
  `%APPDATA%\Zellij\config\plugins`, then update every KDL reference to it.
- Merge the current Zellij 0.44.3 normalized config structure from Linux while
  retaining Windows paths, commands, keybindings, and case conventions.
- Port the Linux tab-name improvements:
  - one `git rev-parse` call;
  - pane-ID-to-tab-ID lookup;
  - `job spawn` rename to avoid blocking and focus races;
  - a single final length cap suitable for the selected layout.
- Port `zs`/`zn` as a native Nu layout picker using
  `%APPDATA%\Zellij\config\layouts`.
- Replace the current `za` alias, which launches Linux Zellij through WSL, with
  a native Windows attach-or-new Nu command. Keep an explicitly named WSL
  alias only if that workflow is still wanted.
- Add the Linux `vtabs.kdl` layout as opt-in after its managed plugins work.
- Keep the Windows Claude layouts initially. Repoint their status plugin, test
  their `cmd`/`nu` commands, and remove a layout only after confirming it is
  unused.
- Remove stale empty `%APPDATA%\Zellij\layouts` state only after chezmoi no
  longer manages it and the corrected config layout directory is verified.

Validation:

- Targeted apply creates every referenced plugin automatically.
- `zellij setup --check` remains clean.
- `mycompact`, `vtabs`, and retained Claude layouts each start successfully.
- `zs`, `zn`, and `za` handle selection cancellation without an error.
- New named sessions use `--new-session-with-layout`, avoiding the
  “There is no active session” failure.
- Changing directories rapidly renames the correct tab without blocking Nu.
- No Zellij file refers to `~/temp`, `/home`, or an absent plugin.

## Phase 2: Make Nushell 0.114 robust and portable

Reference:

- `../dotfiles-linux/private_dot_config/nushell/AGENTS.md`
- `config.nu`, `env.nu`, `clip.nu`, `dir-history.nu`, and `completions.nu` in
  the Linux Nushell directory

Files:

- `AppData/Roaming/nushell/env.nu`
- `AppData/Roaming/nushell/config.nu`
- `AppData/Roaming/nushell/alias.nu`
- `AppData/Roaming/nushell/clip.nu`
- `AppData/Roaming/nushell/dir-history.nu`
- optionally `AppData/Roaming/nushell/completions.nu`
- `dot_config/atuin/config.toml`

Tasks:

- Add `env.nu` to generate `mise.nu` before `config.nu` is parsed. Generate an
  empty module when mise is absent so fresh installs remain parseable.
- For optional `source` and `use` targets, use parse-time `const` selection
  with an existing path or `null`, as documented by the Linux repository.
- Guard Starship generation, Atuin sourcing, Zellij status, Fastfetch, eza,
  sccache, and other optional integrations with command/path checks.
- Modularize the cross-platform clipboard helper. On native Windows, use
  `clip.exe`; retain Linux/WSL branches only if this same module is deliberately
  shared later.
- Port the improved directory-history module, including the 150-entry limit,
  stale-path pruning, forget, and trash modes. Verify trash behavior on
  Windows before enabling deletion shortcuts.
- Keep the Windows-native file picker implementation unless the Linux
  `file-picker.sh` dependency is also ported; do not add a shell-script alias
  that cannot run natively.
- Audit every alias:
  - remove obsolete Linux-only aliases;
  - adapt useful ones to Windows paths or Nu-native implementations;
  - guard optional tools;
  - use `.venv/Scripts/activate.nu` on Windows;
  - retain current Windows helpers such as `exec-nu`.
- Keep the current generated Atuin init compatible with Atuin 18.17.1, source
  it optionally, and port the useful non-secret Atuin preferences
  (`directory`, compact UI, inline height, `enter_accept`, sync records).
- Consider Carapace completion only after documenting/installing Carapace. The
  basic fuzzy completer must still work without it.

Validation:

- A normal Nu startup emits no error.
- Nu starts when each optional tool is individually absent.
- `mise`, Atuin Ctrl-R, directory history, clipboard copy, eza listing,
  Starship, and the Zellij directory hook work when installed.
- Search the Windows Nu tree for accidental `/home`, Linuxbrew, and
  `~/.config/my-scripts` references.

## Phase 3: Fix PowerShell startup

Files:

- `Documents/PowerShell/Microsoft.PowerShell_profile.ps1`
- `Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1`
- optionally a small shared profile script loaded by both

Tasks:

- Make PSReadLine and PSFzf initialization conditional:
  import modules if present, then call `Set-PSFzfOption` only if the command
  exists.
- Correct invalid or conflicting alias declarations, including
  `set alias vv='vc'`.
- Guard eza, fzf, fd, zoxide, oh-my-posh, Fastfetch, editors, and IDE commands.
- Stop writing the user-level environment `PATH` on every startup. Add the mise
  shim to the current process only when absent, or use supported mise
  activation.
- Avoid global `$ErrorActionPreference = "Stop"` for the whole interactive
  profile; use local error handling around initialization.
- Deduplicate Git aliases and shell helpers.
- Move dangerous convenience commands, especially reflog/prune helpers and
  “add/commit/push everything,” out of the default profile or give them names
  and confirmation behavior that make their risk explicit.
- Show Fastfetch only in an interactive top-level shell and suppress it in
  automation/agent sessions.
- Make PowerShell 7 the primary maintained profile. Keep Windows PowerShell
  compatible through a minimal shared loader rather than two diverging copies.

Validation:

- `pwsh -NoLogo -Command exit` succeeds without output or persistent changes.
- Windows PowerShell also starts without profile errors.
- Repeated shell launches do not grow the user `PATH`.
- The profile still loads when PSFzf, zoxide, or eza is missing.

## Phase 4: Synchronize core portable configuration

### Git

- Port `init.defaultBranch = main`, `core.editor = nvim`,
  `merge.conflictStyle = zdiff3`, verbose commits, and useful diff/merge tool
  settings.
- Preserve `core.autocrlf = input`.
- Install Delta before enabling it as the pager, or retain the built-in pager.
- Keep Windows Credential Manager/GitHub CLI credential handling. Never copy
  `/home/linuxbrew/.../gh auth git-credential`.

### Starship

- Port the visible Git commit module and other portable prompt improvements.
- Port CUBRID database/JAVA_HOME indicators only with Windows-compatible
  commands; do not copy the Linux Bash `when` expression unchanged.
- Keep initialization guarded in both Nu and PowerShell.

### WezTerm

- Keep the Windows WSL default program, launch menu, acrylic backdrop, fonts,
  and fallback fonts.
- Correct the GUI startup callback signature using the Linux version as the
  reference.
- Remove dead background-image code after preserving any still-used choice.
- Validate WSL domain names against the installed distributions instead of
  copying Linux terminal settings.

### Alacritty

- Make the imported Catppuccin flavor match a managed theme file.
- Express WSL launch as a Windows executable plus arguments rather than the
  ambiguous single string `wsl ~`.
- Keep Windows blur, maximization, font, and WSL environment propagation.

### Windows Terminal

- First merge the deployed GUID/profile and appearance drift into the source.
- Preserve machine-generated profile GUIDs deliberately; avoid replacing them
  with Linux terminal concepts.
- Validate JSON and launch every retained default/profile shortcut.

## Phase 5: Add selected high-value portable files

Candidates from Linux, in priority order:

1. `dot_fdignore`, adjusted so it does not hide useful Windows paths.
2. Atuin preferences described in Phase 2.
3. Fastfetch config, removing X11-only fields and adding Windows-relevant
   modules.
4. Lazygit config after Delta is installed; omit the Linux-only
   `lazygit-ai-commit.sh` command until it has a Windows implementation.
5. bat config and Catppuccin themes after bat is installed.
6. Yazi config only if Yazi is adopted on Windows.
7. Portable Claude/Codex guidance, with Windows paths substituted.

Do not copy Linux Codex approval policy, sandbox mode, trusted project paths,
Claude model selection, or broad permission settings automatically. Those are
security- and machine-specific choices and require a separate review.

## Phase 6: Document dependencies and bootstrap

Create a Windows dependency matrix:

- Required: chezmoi, Git, Nu, Zellij, fzf, Starship.
- Recommended: mise, Atuin, eza, fd, ripgrep, Fastfetch, lazygit.
- Optional by feature: Delta, bat, gh, Carapace, Yazi, zoxide, PSFzf,
  oh-my-posh.

For each tool, document:

- the preferred `winget` package ID;
- which config/alias uses it;
- whether absence is supported;
- one version or smoke-test command.

Prefer documentation or an idempotent bootstrap script. Do not silently
install packages during `chezmoi apply`.

## Phase 7: Final verification and commit sequence

Suggested commits:

1. `chore(chezmoi): add Windows safety metadata and docs`
2. `fix(zellij): manage plugins and repair Windows layouts`
3. `feat(nu): port robust optional integrations and session helpers`
4. `fix(powershell): make profile startup idempotent`
5. `chore(config): sync portable git and terminal improvements`
6. `docs: add Windows dependency and bootstrap guide`

For every commit:

- inspect `git diff --check`;
- validate only the affected application;
- inspect the exact `chezmoi diff` target;
- apply only that target after review;
- re-run the application smoke test;
- confirm `git status` and `chezmoi status`.

## Definition of done

- A fresh Windows machine can obtain every referenced Zellij plugin through
  chezmoi; no manual `~/temp` download is required.
- Native `za`, `zs`, and `zn` workflows work, and tab naming is race-free.
- Nu and PowerShell start cleanly with the recommended toolset and degrade
  gracefully when optional tools are absent.
- No startup file performs persistent environment mutation.
- No Windows-managed file contains an accidental Linux absolute path or
  invokes an unported Linux helper.
- Alacritty, WezTerm, Windows Terminal, Starship, Git, mise, and Atuin pass
  their component smoke tests.
- Existing local Windows Terminal, mise, and Nu changes have been explicitly
  preserved or intentionally superseded.
- Repository-only Markdown files are excluded from chezmoi deployment.
- The final `chezmoi diff` contains only reviewed changes, followed by
  targeted applies rather than a broad apply.
