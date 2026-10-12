const preview_script = path self picker-preview.nu

export def require [command: string] {
  if (which $command | is-empty) { error make {msg: $"($command) is required for this helper."} }
}

export def checked [args: list<string>] {
  let command = $args.0
  require $command
  let result = (do { ^$command ...($args | skip 1) } | complete)
  if $result.exit_code != 0 { error make {msg: ($result.stderr | str trim)} }
  $result.stdout
}

export def quote-nu [value: string] { $value | to json --raw }

export def pick-record [records: list<record>, query: string = "", prompt: string = "pick> ", --name-only] {
  require fzf
  if ($records | is-empty) { return null }
  let temporary = (mktemp --suffix .json)
  $records | save --force $temporary
  let rows = ($records | enumerate | each {|row|
    let label = ($row.item.label | str replace --all (char nl) " " | str replace --all (char cr) " ")
    $"($row.index)(char tab)($label)"
  } | str join (char nl))
  # Generated indices enter cmd.exe. Ref names and paths remain JSON data.
  let preview = $'"($nu.current-exe)" --no-config-file "($preview_script)" "($temporary)" {1}'
  mut args = ["--ansi" "--no-multi" "--no-print-query" "--no-expect" "--no-sort" "--height=60%" "--reverse"
    "--delimiter" (char tab) "--with-nth=2.." "--accept-nth=1" "--query" $query "--prompt" $prompt
    "--with-shell=cmd.exe /d /c" "--preview" $preview "--preview-window=right:60%,wrap" "--bind=ctrl-/:toggle-preview"]
  if $name_only { $args = ($args | append "--nth=1") }
  let result = try {
    $rows | ^fzf ...$args | complete
  } catch {|error|
    rm --force --permanent $temporary
    error make {msg: $error.msg}
  }
  rm --force --permanent $temporary
  if $result.exit_code in [1 130] { return null }
  if $result.exit_code != 0 { error make {msg: ($result.stderr | str trim)} }
  let index = ($result.stdout | str trim | into int)
  if $index < 0 or $index >= ($records | length) { error make {msg: "fzf returned an invalid selection."} }
  $records | get $index
}
