use std/util "path add"

$env.HOME = ($env.USERPROFILE? | default $nu.home-dir)
$env.EDITOR = if (which nvim | is-not-empty) { "nvim" } else { "notepad.exe" }
$env.VISUAL = $env.EDITOR
$env.CMAKE_EXPORT_COMPILE_COMMANDS = "ON"

$env.config.show_banner = false
$env.config.rm.always_trash = true
$env.config.buffer_editor = $env.EDITOR
$env.config.completions = {
  case_sensitive: false
  algorithm: "fuzzy"
  external: { enable: true }
}

$env.config.hooks = ($env.config.hooks? | default {})
$env.config.hooks.env_change = ($env.config.hooks.env_change? | default {})
$env.config.hooks.env_change.PWD = (
  $env.config.hooks.env_change.PWD? | default []
)

const eza_init = if (($nu.default-config-dir | path join "eza.nu") | path exists) {
  ($nu.default-config-dir | path join "eza.nu")
} else { null }
source $eza_init

const alias_init = if (($nu.default-config-dir | path join "alias.nu") | path exists) {
  ($nu.default-config-dir | path join "alias.nu")
} else { null }
source $alias_init

const clip_init = if (($nu.default-config-dir | path join "clip.nu") | path exists) {
  ($nu.default-config-dir | path join "clip.nu")
} else { null }
source $clip_init

const history_init = if (($nu.default-config-dir | path join "dir-history.nu") | path exists) {
  ($nu.default-config-dir | path join "dir-history.nu")
} else { null }
source $history_init

const bookmark_init = if (($nu.default-config-dir | path join "bookmark.nu") | path exists) {
  ($nu.default-config-dir | path join "bookmark.nu")
} else { null }
source $bookmark_init

const zellij_init = if (($nu.default-config-dir | path join "zellij.nu") | path exists) {
  ($nu.default-config-dir | path join "zellij.nu")
} else { null }
source $zellij_init

const atuin_init = if ('~/.local/share/atuin/init.nu' | path expand | path exists) {
  '~/.local/share/atuin/init.nu'
} else { null }
source $atuin_init

const mise_module = if (($nu.default-config-dir | path join "mise.nu") | path exists) {
  ($nu.default-config-dir | path join "mise.nu")
} else { null }
use $mise_module

if (which sccache | is-not-empty) {
  $env.RUSTC_WRAPPER = "sccache"
}

let msys_bin = 'C:\msys64\mingw64\bin'
if ($msys_bin | path exists) { path add $msys_bin }

let local_bin = ($env.HOME | path join ".local" "bin")
if ($local_bin | path exists) { path add $local_bin }

$env.config.hooks.env_change.PWD = (
  $env.config.hooks.env_change.PWD
    | append {|before after| zellij-update-tabname-git }
)

let starship_autoload = ($nu.data-dir | path join "vendor" "autoload" "starship.nu")
mkdir ($starship_autoload | path dirname)
if (which starship | is-not-empty) {
  ^starship init nu | save --force $starship_autoload
} else if ($starship_autoload | path exists) {
  rm $starship_autoload
}

let agent_session = (
  ("CLAUDE" in $env)
  or ("CODEX_HOME" in $env)
  or (($env.CI? | default "") != "")
)
if $nu.is-interactive and (not $agent_session) and (which fastfetch | is-not-empty) {
  fastfetch
}
