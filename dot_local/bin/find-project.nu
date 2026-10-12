use picker-common.nu [checked pick-record]

def main [--depth (-d): int = 3, --json, ...query: string] {
  if $depth < 1 { error make {msg: "Depth must be positive."} }
  let explicit = ($env.FIND_PROJECT_ROOTS? != null)
  let configured = if $explicit {
    if (($env.FIND_PROJECT_ROOTS | describe) == "string") { $env.FIND_PROJECT_ROOTS | split row ";" } else { $env.FIND_PROJECT_ROOTS }
  } else { [($nu.home-dir | path join gh) ($nu.home-dir | path join temp) ($nu.home-dir | path join tmp)] }
  mut roots = []
  for root in $configured {
    if $explicit and (($root | str trim) == "") { error make {msg: "FIND_PROJECT_ROOTS contains an empty root."} }
    if $explicit and not ($root =~ '^[A-Za-z]:[\\/]|^\\\\|^~[\\/]') {
      error make {msg: $"Project root must be absolute or start with ~: ($root)"}
    }
    let absolute = ($root | path expand)
    if ($absolute | path type) == "dir" { $roots = ($roots | append $absolute) } else if $explicit {
      error make {msg: $"Project root is not a directory: ($root)"}
    }
  }
  if ($roots | is-empty) { error make {msg: "No usable project roots."} }
  let records = ($roots | uniq | each {|root|
    checked [fd --type d --min-depth "1" --max-depth ($depth | into string) --absolute-path . $root]
      | lines | each {|path|
        let absolute = ($path | path expand)
        {kind: directory, value: $absolute, label: $"($absolute | path basename)(char tab)($absolute)"}
      }
  } | flatten | uniq-by value)
  let selected = (pick-record $records ($query | str join " ") "project> " --name-only)
  if $selected != null { print (if $json { $selected.value | to json --raw } else { $selected.value }) }
}
