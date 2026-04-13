# config.nu
#
# Installed by:
# version = "0.104.0"
#
# This file is used to override default Nushell settings, define
# (or import) custom commands, or run any other startup tasks.
# See https://www.nushell.sh/book/configuration.html
#
# This file is loaded after env.nu and before login.nu
#
# You can open this file in your default editor using:
# config nu
#
# See `help config nu` for more options
#
# You can remove these comments if you want or leave
# them for future reference.

# required for 'path add .../bin'
use std/util "path add"

$env.HOME = $env.USERPROFILE
$env.EDITOR = 'nvim'

mkdir ($nu.data-dir | path join "vendor/autoload")
starship init nu | save -f ($nu.data-dir | path join "vendor/autoload/starship.nu")

source ($nu.default-config-dir | path join eza.nu)
use ($nu.default-config-dir | path join mise.nu)

$env.config.rm.always_trash = true
$env.config.show_banner = false

# fzf-tab like completion
$env.config.completions = {
  case_sensitive: false
  algorithm: "fuzzy"
  external: {
    enable: true
  }
}

$env.config.buffer_editor = 'nvim'

$env.CMAKE_EXPORT_COMPILE_COMMANDS = 'ON'

if (which sccache | is-not-empty) {
  export-env {
    $env.RUSTC_WRAPPER = 'sccache'
  }
}

###############################################################################
# Hooks
###############################################################################

if (
  'PWD' not-in $env.config.hooks.env_change
) {
  $env.config.hooks.env_change.PWD = []
}

###############################################################################
# Sources
###############################################################################

source ($nu.default-config-dir | path join zellij.nu)
source ($nu.default-config-dir | path join alias.nu)

# Zellij tab name update on directory change
$env.config.hooks.env_change.PWD = (
  $env.config.hooks.env_change.PWD | append {|before after|
    zellij-update-tabname-git
  }
)

# c compiler error for nvim-treesitter
path add 'C:\msys64\mingw64\bin'

# claude code CLI
path add ($env.HOME | path join '.local' 'bin')

# winget-installed packages
# path add ($env.LOCALAPPDATA | path join "Microsoft" "WinGet" "Packages" "Atuinsh.Atuin_Microsoft.Winget.Source_8wekyb3d8bbwe")

source ~/.local/share/atuin/init.nu

###############################################################################
# Shell Startup Decoration
###############################################################################

if ("CLAUDE" not-in $env) { fastfetch }
