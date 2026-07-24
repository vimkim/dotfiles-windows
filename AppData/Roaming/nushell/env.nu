# env.nu runs before config.nu is parsed, so parser-time modules can always
# point at an existing file.
let mise_path = ($nu.default-config-dir | path join "mise.nu")
if (which mise | is-not-empty) {
  ^mise activate nu | save --force $mise_path
} else {
  # An empty module keeps `use` parseable on a fresh machine.
  "" | save --force $mise_path
}
