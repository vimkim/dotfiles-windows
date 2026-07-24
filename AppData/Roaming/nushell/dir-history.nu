let history_file = ($env.HOME | path join ".local" "share" "nu" "dirlog.json")

def _dir_history_init [] {
  if not ($history_file | path exists) {
    mkdir ($history_file | path dirname)
    [] | save --force $history_file
  }
}

def _dir_history_load [] {
  if not ($history_file | path exists) { return [] }
  try {
    open $history_file
      | default []
      | where {|dir| (($dir | describe) == "string") and (($dir | str trim) != "") }
  } catch {
    []
  }
}

def _dir_history_save [] {
  mkdir ($history_file | path dirname)
  $in | collect | uniq | take 150 | save --force $history_file
}

def _dir_history_forget [paths: list<string>] {
  if ($paths | is-empty) { return }
  let doomed = ($paths | each {|path| $path | path expand | str lowercase } | uniq)
  _dir_history_load
    | where {|dir| ($dir | path expand | str lowercase) not-in $doomed }
    | _dir_history_save
}

def _dir_history_pick [
  --multi (-m)
  --header: string = "Directory history (Enter=cd, Ctrl-C=cancel)"
] {
  let dirs = (_dir_history_load)
  if ($dirs | is-empty) { return [] }

  mut args = ["--height" "60%" "--reverse" "--ansi" "--header" $header]
  if $multi { $args = ($args | append "--multi") }

  let result = (
    $dirs
      | each {|line| $"(ansi blue)($line)(ansi reset)" }
      | str join (char nl)
      | ^fzf ...$args
      | complete
  )
  if $result.exit_code != 0 { return [] }

  $result.stdout
    | str trim
    | lines
    | each {|line| $line | ansi strip | str trim }
    | where {|line| $line != "" }
}

def _dir_history_prune [] {
  let before = (_dir_history_load)
  let kept = ($before | where {|dir| $dir | path exists })
  $kept | _dir_history_save
  print $"Pruned (($before | length) - ($kept | length)) stale path\(s\)."
}

def _dir_history_delete [dirs: list<string>] {
  if ($dirs | is-empty) { return }
  print "Selected for trash:"
  $dirs | each {|dir| print $"  ($dir)" }

  let answer = (input --numchar 1 $"Trash ($dirs | length) selected path\(s\)? [y/N] " | str lowercase | str trim)
  print ""
  if $answer != "y" {
    print "Delete cancelled."
    return
  }

  let cwd = ($env.PWD | path expand | str lowercase)
  let home = ($env.HOME | path expand | str lowercase)
  mut trashed = []
  mut forgotten = []
  mut skipped = []

  for dir in $dirs {
    if not ($dir | path exists) {
      $forgotten = ($forgotten | append $dir)
      continue
    }

    let full = ($dir | path expand | str lowercase)
    let drive_root = ($full | path parse | get parent)
    let contains_cwd = ($cwd == $full) or ($cwd | str starts-with $"($full)(char path_sep)")
    if ($full == $home) or ($full == $drive_root) or $contains_cwd {
      print $"Skipping protected/current path: ($dir)"
      $skipped = ($skipped | append $dir)
      continue
    }

    let result = try {
      rm --trash --recursive $dir
      { ok: true, msg: "" }
    } catch {|err|
      { ok: false, msg: $err.msg }
    }
    if $result.ok {
      $trashed = ($trashed | append $dir)
    } else {
      print $"Failed to trash: ($dir)"
      print $result.msg
      $skipped = ($skipped | append $dir)
    }
  }

  let remove = ($trashed | append $forgotten)
  if ($remove | is-not-empty) { _dir_history_forget $remove }
  print $"Trashed ($trashed | length); forgot ($forgotten | length) stale; skipped ($skipped | length)."
}

$env.config.hooks.env_change.PWD = (
  ($env.config.hooks.env_change.PWD? | default [])
    | append {|before after|
        _dir_history_init
        _dir_history_load | prepend $after | _dir_history_save
      }
)

def view-dir-history [] { _dir_history_load }
alias vh = view-dir-history

def --env cd-dir-history [
  --forget (-f)
  --delete (-d)
  --prune (-p)
] {
  _dir_history_init
  let mode_count = ([$forget $delete $prune] | where {|enabled| $enabled } | length)
  if $mode_count > 1 {
    print "Use only one of --forget, --delete, or --prune."
    return
  }
  if $prune { _dir_history_prune; return }

  let selected = if $forget {
    _dir_history_pick --multi --header "TAB=multi, Enter=forget selected"
  } else if $delete {
    _dir_history_pick --multi --header "TAB=multi, Enter=trash selected"
  } else {
    _dir_history_pick
  }

  if ($selected | is-empty) {
    print "No directory selected."
    return
  }
  if $forget { _dir_history_forget $selected; return }
  if $delete { _dir_history_delete $selected; return }

  let dir = ($selected | first)
  if ($dir | path exists) {
    cd $dir
  } else {
    _dir_history_forget [$dir]
    print $"Removed missing path from history: ($dir)"
  }
}

alias ch = cd-dir-history
alias chf = cd-dir-history --forget
alias chd = cd-dir-history --delete
alias chp = cd-dir-history --prune
