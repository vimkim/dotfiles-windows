# Windows dotfiles

Windows-native configuration managed by
[chezmoi](https://www.chezmoi.io/). The sibling `dotfiles-linux` repository is
a reference only; paths, shell commands, credentials, and terminal behavior
remain Windows-specific here.

## Safe workflow

Edit the source repository, inspect one exact target, validate it, and apply
only that target:

```powershell
chezmoi diff -- "$HOME\AppData\Roaming\nushell\config.nu"
nu --no-config-file -c "nu-check .\AppData\Roaming\nushell\config.nu"
chezmoi apply -- "$HOME\AppData\Roaming\nushell\config.nu"
nu --login -c "exit"
```

Never use `chezmoi apply --force`, and do not run a broad apply when
`chezmoi status` reports target drift.

Common source-to-target mappings:

| Source | Target |
| --- | --- |
| `AppData/Roaming/nushell` | `%APPDATA%\nushell` |
| `AppData/Roaming/herdr/config.toml` | `%APPDATA%\herdr\config.toml` |
| `AppData/Roaming/zellij/config` | `%APPDATA%\zellij\config` |
| `Documents/PowerShell` | `%USERPROFILE%\Documents\PowerShell` |
| `dot_config` | `%USERPROFILE%\.config` |
| `dot_gitconfig` | `%USERPROFILE%\.gitconfig` |
| `dot_wezterm.lua` | `%USERPROFILE%\.wezterm.lua` |

## Herdr

The Linux Herdr keybindings, Catppuccin theme, expanded sidebar, and tab agent
indicators are ported to native Windows. New panes still use `nu.exe`; cursor
selection uses Herdr's Windows `auto` policy. Nushell starts one hidden tab-status
worker per session when Python is available. The helpers use Python's standard
library and Windows named pipes, with no Bash, WSL, or extra Python packages.

Python 3 must be available as `python` for tab indicators and workspace reordering.
The Nushell startup integration skips the Windows App Installer alias when no
actual Python is installed. Journals and logs live under
`%LOCALAPPDATA%\herdr-tab-status\<socket-hash>` (or `XDG_CACHE_HOME` when set).

Common shortcuts:

| Action | Shortcut |
| --- | --- |
| Workspace picker / new workspace | `Alt+w` / `Alt+c` |
| Previous / next workspace | `Alt+p` / `Alt+n`, or `Alt+Up` / `Alt+Down` |
| Select workspace | `Alt+1..9` |
| Move workspace up / down | `Alt+Shift+p` / `Alt+Shift+n`, or `Alt+Shift+Up` / `Alt+Shift+Down` |
| New / close tab | `Alt+t` / `Alt+x` |
| Previous / next tab | `Alt+h` / `Alt+i`, or `Alt+Left` / `Alt+Right` |
| Select tab | `Alt+Shift+1..9` |
| Move tab left / right | `Alt+Shift+h` / `Alt+Shift+i` |
| Split / zoom | `Alt+v` / `Alt+f` |
| Reload client config | `Ctrl+a`, then `Shift+r` |

Tab labels retain their original names and gain agent state and observed elapsed
time, such as `review [! Claude 3m]`. The sidebar shows tab/pane/agent counts and
up to 13 rows of tab summaries. `stop` restores names still owned by the reporter
and clears only its own sidebar metadata.

Inside an existing Herdr Nushell pane:

```nu
herdr-tab-status preview
herdr-tab-status start
herdr-tab-status stop
```

New panes start the reporter automatically. Reload the client config with the
shortcut above to pick up the sidebar and bindings without restarting the server.
When replacing a running reporter, stop it and wait for original names before
applying the changed helpers, then start it again.

Apply each helper separately, then `herdr.nu`, `config.nu`, and Herdr's
`config.toml`, using the exact deployed file targets. The helper sources are
`dot_local/bin/herdr_api.py`, `herdr_move_workspace.py`, `herdr_tab_status.py`,
`herdr-move-workspace.cmd`, and `herdr-tab-status.cmd`. Tests stay in the repository:

```powershell
python -X utf8 -m unittest tests.test_herdr_tab_status tests.test_herdr_move_workspace -q
$env:HERDR_CONFIG_PATH = "$PWD\AppData\Roaming\herdr\config.toml"
herdr config check
```

## Shell helpers

The shared directory picker is parent-first, then newest modification time first.
Its search matches directory names while size/time/link information stays visible.
Paths travel as JSON or NUL-delimited records so spaces, Unicode, and shell
characters survive selection. Cancelling a picker leaves the current directory
and editor unchanged.

| Command | Behavior |
| --- | --- |
| `c`, `cv`, `cl` | Pick an immediate child directory, then list it; an explicit path navigates directly. |
| `cz QUERY` | Use zoxide's interactive picker. Nu and both PowerShell profiles initialize zoxide when installed. |
| `cx QUERY` | Recursively pick a directory in the current tree. |
| `vc QUERY` | Pick and edit a file; searches one level by default. |
| `cf QUERY` | Recursively pick a file, then navigate to its containing directory. |
| `l`, `ll`, `ezam` | Detailed newest-first listing, automatically paged in a terminal when needed. |
| `ls-by-name`, `ls-by-size`, `ls-by-time`, `ls-by-extension` | Sorted detailed listings, including hidden entries. `-r` reverses each preset; `--no-pager` prints directly. |
| `ls-tree`, `ls-dirs`, `ls-files` | Two-level tree, directory-only, and file-only listing presets. |
| `ji`, `n`, `jj`, `nn`, `jc` | Pick a Just recipe and paste `just <recipe>` onto Nu's editable prompt. `ji`/`n` with arguments execute Just directly. |
| `ni` | Pick from `./.just/justfile` and paste the full Just command. |
| `find-project`, Nu's `fp` | Pick a project under `~/gh`, `~/temp`, or `~/tmp`; `fp` also navigates and lists. |
| Nu's `dv`, `dn` | Pick Git revisions and paste a Diffview or diff-pager command onto the prompt. |
| `git-diffview`, `git-diffnav` | Run the revision helpers directly; `-p` prints a runnable Nu command. |
| `re`, `rerun-on-enter` | Run a command again after Enter; `q` quits. |

In Nu, `cl --query NAME`, `vc --max-depth 3`, and
`cf --no-ignore --no-hidden` customize pickers. PowerShell uses `-Query`,
`-MaxDepth`, `-NoIgnore`, and `-NoHidden`. `vc` uses the configured `EDITOR`.
File previews use bat when available, with a bounded plain-text fallback.

Project search defaults to depth 3 and skips hidden/ignored directories.
`find-project --depth 5 QUERY` searches deeper. Set `FIND_PROJECT_ROOTS` to a
semicolon-separated list of absolute Windows paths to choose other roots.

Diffview requires Neovim's Diffview plugin. `dv -w` selects uncommitted changes;
`dv -3 BASE TARGET` uses the merge-base comparison. Revision names resolve to
commit IDs before becoming editor commands. `dn` uses diffnav when installed,
otherwise less; `GIT_DIFFNAV_PAGER` overrides the pager executable.

Python 3 is required for the shared pickers and listing presets. fd/fzf support
the pickers, eza/less support listings, and Just supports recipes. Startup remains
valid when optional tools are absent. The profiles prefer installed native
WinGet zoxide/Just packages to obsolete mise shims, changing only process PATH.
Generated `mise.nu` and `zoxide.nu` remain machine-local.

The `.cmd` entry points make helpers available in both shells. They call Python
or `nu --no-config-file` and require no Bash or WSL. In noninteractive Nu,
command-editing wrappers print the command instead of editing a prompt.

```powershell
python -X utf8 -m unittest tests.test_windows_helpers -q
```

## Dependencies

Package IDs are for `winget install --id <ID> --exact`. A missing recommended
or optional tool disables only the related integration.

| Tier | Tool | Preferred winget ID | Used by | Smoke test |
| --- | --- | --- | --- | --- |
| Required | chezmoi | `twpayne.chezmoi` | deployment | `chezmoi doctor` |
| Required | Git | `Git.Git` | shell helpers, prompt | `git --version` |
| Required | Nushell | `Nushell.Nushell` | primary shell | `nu -c "version"` |
| Required | Zellij | `Zellij.Zellij` | terminal workspace | `zellij --version` |
| Required | fzf | `junegunn.fzf` | interactive pickers | `fzf --version` |
| Required | Starship | `Starship.Starship` | prompt | `starship --version` |
| Recommended | mise | `jdx.mise` | runtime versions | `mise doctor` |
| Recommended | Atuin | `Atuinsh.Atuin` | shell history | `atuin --version` |
| Recommended | eza | `eza-community.eza` | listings | `eza --version` |
| Recommended | Just | `Casey.Just` | recipe helpers | `just --version` |
| Recommended | fd | `sharkdp.fd` | file pickers | `fd --version` |
| Recommended | ripgrep | `BurntSushi.ripgrep.MSVC` | search | `rg --version` |
| Recommended | Fastfetch | `Fastfetch-cli.Fastfetch` | interactive banner | `fastfetch --version` |
| Recommended | lazygit | `JesseDuffield.lazygit` | Git UI | `lazygit --version` |
| Optional | Delta | `dandavison.delta` | enhanced Git pager | `delta --version` |
| Optional | bat | `sharkdp.bat` | highlighted previews | `bat --version` |
| Optional | GitHub CLI | `GitHub.cli` | GitHub helpers | `gh --version` |
| Optional | Carapace | `rsteube.Carapace` | enhanced completion | `carapace --version` |
| Optional | Yazi | `sxyazi.yazi` | file manager | `yazi --version` |
| Optional | zoxide | `ajeetdsouza.zoxide` | directory jumping | `zoxide --version` |
| Optional | PSFzf | PowerShell Gallery | PowerShell fuzzy bindings | `Get-Module -ListAvailable PSFzf` |
| Optional | oh-my-posh | `JanDeDobbeleer.OhMyPosh` | alternate PowerShell prompt | `oh-my-posh version` |

The repository does not install packages during apply. Install only the
features you want, then use exact-target applies. Zellij's two pinned WebAssembly
plugins are the exception: chezmoi downloads them from their versioned release
URLs when the Zellij config directory is applied.

The retained Claude Zellij layouts treat the `claude` command as optional. If
Claude Code is absent, each Claude pane opens Nushell without emitting a
command-not-found error.
