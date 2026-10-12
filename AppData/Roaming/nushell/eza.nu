# Set the EZA_COLORS environment variable
$env.EZA_COLORS = $"da=35;"

# Define common options as a list (local variable)
let eza_common_options = [
  --group-directories-last
  -aF
  --time-style=relative
]

# Define long options by appending to the common options
$env.EZA_LONG_OPTIONS = (
  $eza_common_options ++ [
    --long
    --git
    --color=always
  ]
)

# Define sort options
$env.EZA_SORT_MODIFIED = [
  --sort=modified
  -r
]

# Detailed newest-first listings; the helper pages only in a real terminal.
def --wrapped ezam [...args: string] {
  let helper = ($nu.home-dir | path join ".local" "bin" "listing.py")
  if (which eza | is-not-empty) and (which python | is-not-empty) and ($helper | path exists) {
    ^python -X utf8 $helper ls-by-time --no-user --no-permissions --icons=auto ...$args
  } else if (which eza | is-not-empty) {
    ^eza --all --long --sort=modified --reverse --icons=auto ...$args
  } else { ls ...$args }
}
def --wrapped ezaml [...args: string] { ezam ...$args }
alias ll = ezaml
