use picker-common.nu [checked pick-record quote-nu]

def --wrapped main [...args: string] {
  mut print_only = false
  mut refs = []
  for arg in $args {
    match $arg {
      "-p" | "--print" => { $print_only = true }
      "-h" | "--help" => { print "git-diffnav [-p] [BASE] [TARGET]"; return }
      _ => {
        if ($arg | str starts-with "-") { error make {msg: $"Unknown flag: ($arg)"} }
        $refs = ($refs | append $arg)
      }
    }
  }
  if ($refs | length) > 2 { error make {msg: "Expected at most two revisions."} }
  checked [git rev-parse --is-inside-work-tree] | ignore
  if ($refs | length) < 2 {
    let graph = (checked [git --no-pager log --graph --all --color=always '--format=%H %s'])
    let records = ($graph | lines | each {|line|
      let parsed = ($line | ansi strip | parse --regex '(?<hash>[0-9a-f]{40}) ')
      if ($parsed | is-not-empty) {
        {kind: git-commit, value: $parsed.0.hash, label: ($line | str replace $parsed.0.hash ($parsed.0.hash | str substring 0..7))}
      }
    } | compact)
    while ($refs | length) < 2 {
      let selected = (pick-record $records "" (if ($refs | is-empty) { "BASE> " } else { "TARGET> " }))
      if $selected == null { return }
      $refs = ($refs | append $selected.value)
    }
  }
  for ref in $refs { checked [git rev-parse --verify --end-of-options $"($ref)^{commit}"] | ignore }
  let pager = ($env.GIT_DIFFNAV_PAGER? | default (if (which diffnav | is-not-empty) { "diffnav" } else if (which less | is-not-empty) { "less" } else { "" }))
  let pager_args = if $pager == "less" { ["-FRX"] } else { [] }
  if $print_only {
    let suffix = if $pager == "" { "" } else { $" | ^(quote-nu $pager) ($pager_args | str join ' ')" }
    print $"git diff (quote-nu $refs.0) (quote-nu $refs.1)($suffix)"
  } else if $pager == "" { ^git --no-pager diff $refs.0 $refs.1 } else {
    ^git --no-pager diff $refs.0 $refs.1 | ^$pager ...$pager_args
  }
}
