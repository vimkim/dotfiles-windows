# env.nu runs before config.nu is parsed, so parser-time modules can always
# point at an existing file.
use std/util "path add"
let local_appdata = ($env.LOCALAPPDATA? | default ($nu.home-dir | path join "AppData" "Local"))
let winget_packages = ($local_appdata | path join "Microsoft" "WinGet" "Packages")
if ($winget_packages | path exists) {
  for directory in (ls $winget_packages | where type == "dir" | get name | where {|path|
    let name = ($path | path basename)
    ($name | str starts-with "ajeetdsouza.zoxide_") or ($name | str starts-with "Casey.Just_")
  }) { path add $directory }
}

let mise_path = ($nu.default-config-dir | path join "mise.nu")
if (which mise | is-not-empty) {
  ^mise activate nu | save --force $mise_path
} else {
  # An empty module keeps `use` parseable on a fresh machine.
  "" | save --force $mise_path
}

# Generate before config.nu is parsed. Keep an empty module when zoxide is
# absent or initialization fails, so optional tools cannot break startup.
let zoxide_path = ($nu.default-config-dir | path join "zoxide.nu")
let zoxide_init = if (which zoxide | is-not-empty) {
  let result = (do { ^zoxide init nushell } | complete)
  if $result.exit_code == 0 { $result.stdout } else { "" }
} else { "" }
$zoxide_init | save --force $zoxide_path
