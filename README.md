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
nu -c "exit"
```

Never use `chezmoi apply --force`, and do not run a broad apply when
`chezmoi status` reports target drift.

Common source-to-target mappings:

| Source | Target |
| --- | --- |
| `AppData/Roaming/nushell` | `%APPDATA%\nushell` |
| `AppData/Roaming/zellij/config` | `%APPDATA%\zellij\config` |
| `Documents/PowerShell` | `%USERPROFILE%\Documents\PowerShell` |
| `dot_config` | `%USERPROFILE%\.config` |
| `dot_gitconfig` | `%USERPROFILE%\.gitconfig` |
| `dot_wezterm.lua` | `%USERPROFILE%\.wezterm.lua` |

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
