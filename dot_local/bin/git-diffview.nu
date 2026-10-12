use picker-common.nu [checked pick-record quote-nu]

def --wrapped main [...args: string] {
  mut working = false
  mut print_only = false
  mut remotes = false
  mut dots = ".."
  mut refs = []
  for arg in $args {
    match $arg {
      "-w" | "--working" => { $working = true }
      "-p" | "--print" | "-n" | "--dry-run" => { $print_only = true }
      "-r" => { $remotes = true }
      "-3" => { $dots = "..." }
      "-2" => { $dots = ".." }
      "-h" | "--help" => { print "git-diffview [-p|-n] [-w] [-3|-2] [-r] [BASE] [COMPARE]"; return }
      _ => {
        if ($arg | str starts-with "-") { error make {msg: $"Unknown flag: ($arg)"} }
        $refs = ($refs | append $arg)
      }
    }
  }
  if ($refs | length) > 2 { error make {msg: "Expected at most two revisions."} }
  checked [git rev-parse --is-inside-work-tree] | ignore
  mut range = ""
  if not $working {
    let roots = if $remotes { [refs/heads refs/remotes] } else { [refs/heads] }
    let branches = (checked [git for-each-ref '--format=%(refname:short)' ...$roots] | lines | where {|ref| not ($ref | str ends-with '/HEAD') })
    let records = (["@working" "HEAD"] | append $branches | each {|ref| {kind: git-ref, value: $ref, label: $ref} })
    while ($refs | length) < 2 {
      let prompt = if ($refs | is-empty) { "BASE> " } else { "COMPARE> " }
      let selected = (pick-record $records "" $prompt)
      if $selected == null { return }
      $refs = ($refs | append $selected.value)
    }
    # Resolve refs to commits so a branch containing an Ex separator cannot
    # become an editor command. The resulting comparison is reproducible.
    let resolved = ($refs | each {|ref|
      if $ref == "@working" { "" } else { checked [git rev-parse --verify --end-of-options $"($ref)^{commit}"] | str trim }
    })
    $range = if "@working" in $refs { $resolved | where {|ref| $ref != "" } | str join "" } else { $resolved | str join $dots }
  }
  let ex_command = if $range == "" { "DiffviewOpen" } else { $"DiffviewOpen ($range)" }
  if $print_only { print $"nvim -c (quote-nu $ex_command)" } else { ^nvim -c $ex_command }
}
