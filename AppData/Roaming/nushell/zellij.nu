def zellij-update-tabname-git [] {
  if ("ZELLIJ" not-in $env) {
    return
  }

  let current_dir = (pwd)
  mut tab_name = if ($current_dir == $env.HOME) {
    "~"
  } else {
    $current_dir | path parse | get stem
  }

  # One git process returns the work-tree flag and effective repository root.
  let git_info = try {
    git rev-parse --is-inside-work-tree --show-superproject-working-tree --show-toplevel
      | lines
  } catch {
    []
  }

  if ($git_info | length) >= 2 {
    let git_root = ($git_info | get 1)
    let repo_name = ($git_root | path parse | get stem)

    if (($git_root | str lowercase) != ($current_dir | str lowercase)) {
      let pwd_name = ($current_dir | path parse | get stem)
      $tab_name = $"($repo_name):($pwd_name)"
    } else {
      $tab_name = $repo_name
    }
  }

  let tab_name = ($tab_name | str substring 0..<27)
  let tab_id = try {
    let pane_id = $env.ZELLIJ_PANE_ID
    zellij action list-panes --tab
      | lines
      | skip 1
      | where ($it | str contains $"terminal_($pane_id)")
      | first
      | split row -r "\\s\\s+"
      | get 0
      | into int
  } catch {
    null
  }

  job spawn {
    if $tab_id != null {
      zellij action rename-tab --tab-id $tab_id $tab_name
    } else {
      zellij action rename-tab $tab_name
    }
  } | ignore
}

def _zellij-layouts [] {
  let layout_dir = (
    $env.APPDATA
    | path join "zellij" "config" "layouts"
  )

  if not ($layout_dir | path exists) {
    return []
  }

  let glob_dir = ($layout_dir | str replace --all '\' '/')
  glob $"($glob_dir)/*.kdl"
    | path parse
    | get stem
    | sort
}

def _zellij-pick-layout [] {
  let layouts = (_zellij-layouts)
  if ($layouts | is-empty) {
    print "No Zellij layouts found."
    return null
  }

  let result = (
    $layouts
    | str join (char nl)
    | ^fzf --height 60% --reverse --header "Select layout for new Zellij session"
    | complete
  )

  if $result.exit_code != 0 {
    return null
  }

  let chosen = ($result.stdout | str trim)
  if ($chosen | is-empty) { null } else { $chosen }
}

def zellij-new [name?: string] {
  let chosen = (_zellij-pick-layout)
  if $chosen == null {
    print "No layout selected."
    return
  }

  if ($name | is-not-empty) {
    zellij -s $name --new-session-with-layout $chosen
  } else {
    zellij --new-session-with-layout $chosen
  }
}

def zs [name?: string] { zellij-new $name }
def zn [name?: string] { zellij-new $name }

def za [layout?: string] {
  if ("ZELLIJ" in $env) {
    print "Already inside Zellij."
    return
  }

  let sessions_result = (zellij list-sessions --short | complete)
  let sessions = if $sessions_result.exit_code == 0 {
    $sessions_result.stdout | lines | where {|name| ($name | str trim) != "" }
  } else {
    []
  }

  if ($sessions | is-not-empty) {
    let selected = (
      $sessions
      | str join (char nl)
      | ^fzf --height 60% --reverse --header "Attach to Zellij session"
      | complete
    )

    if $selected.exit_code != 0 or ($selected.stdout | str trim | is-empty) {
      print "No session selected."
      return
    }

    zellij attach ($selected.stdout | str trim)
    return
  }

  let chosen_layout = if ($layout | is-not-empty) { $layout } else { _zellij-pick-layout }
  if $chosen_layout == null {
    print "No layout selected."
    return
  }

  let session_name = (
    sys host
    | get hostname
    | str substring 0..<4
    | str lowercase
  )
  zellij -s $session_name --new-session-with-layout $chosen_layout
}

def zv [] { za vtabs }
