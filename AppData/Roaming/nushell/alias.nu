alias fzfm = fzf --height 60% --reverse

###############################################################################
# cd & ls
###############################################################################

const helper_bin = ($nu.home-dir | path join ".local" "bin")

# JSON keeps selected paths separate from display metadata and shell syntax.
def _helper_pick [script: string, args: list<string>] {
  if (which python | is-empty) { error make {msg: "This picker requires Python 3."} }
  let result = (do { ^python -X utf8 ($helper_bin | path join $script) ...$args } | complete)
  if $result.exit_code in [1 130] { return null }
  if $result.exit_code != 0 { error make {msg: ($result.stderr | str trim)} }
  if ($result.stdout | str trim | is-empty) { return null }
  $result.stdout | from json
}

def _helper_command [script: string, args: list<string>] {
  let result = (do { ^nu --no-config-file ($helper_bin | path join $script) ...$args } | complete)
  if $result.exit_code != 0 { error make {msg: ($result.stderr | str trim)} }
  $result.stdout | str trim
}

def _helper_paste [command: string] {
  if $command == "" { return }
  if $nu.is-interactive { commandline edit $command } else { print $command }
}

def --wrapped l [...args: string] {
  let helper = ($helper_bin | path join "listing.py")
  if (which eza | is-not-empty) and (which python | is-not-empty) and ($helper | path exists) {
    ^python -X utf8 $helper ls-by-time --no-user --no-permissions --icons=auto ...$args
  } else if (which eza | is-not-empty) {
    ^eza --all --long --sort=modified --reverse --icons=auto ...$args
  } else { ls ...$args }
}

def --env cl [dir?: string, --query: string] {
  let target = if $dir != null and $query == null { $dir } else {
    _helper_pick "dir_picker.py" ["--json" $"--query=($query | default '')" "--" ($dir | default ".")]
  }
  if $target == null { return }
  cd $target
  l
}

alias cv = cl

def --env cz [...args: string] {
  if (which zoxide | is-empty) { error make {msg: "cz requires zoxide."} }
  zi ...$args
  l
}

def _file_selection [query: string, max_depth: any, no_ignore: bool, no_hidden: bool] {
  mut args = ["--json" $"--query=($query)"]
  if $max_depth != null { $args = ($args | append ["--max-depth" ($max_depth | into string)]) }
  if $no_ignore { $args = ($args | append "--no-ignore") }
  if $no_hidden { $args = ($args | append "--no-hidden") }
  _helper_pick "file_picker.py" $args
}

def vc [query: string = "", --max-depth: int = 1, --no-ignore, --no-hidden] {
  let file = (_file_selection $query $max_depth $no_ignore $no_hidden)
  if $file != null {
    let editor = ($env.EDITOR? | default "notepad.exe")
    ^$editor $file
  }
}

def --env cf [query: string = "", --max-depth: int, --no-ignore, --no-hidden] {
  let file = (_file_selection $query $max_depth $no_ignore $no_hidden)
  if $file != null { cl ($file | path dirname) }
}

def --env fp [--depth (-d): int = 3, ...query: string] {
  let output = (_helper_command "find-project.nu" ["--json" "--depth" ($depth | into string) ...$query])
  if $output != "" { cl ($output | from json) }
}

def --env --wrapped dv [...args: string] { _helper_paste (_helper_command "git-diffview.nu" ["-p" ...$args]) }
def --env --wrapped dn [...args: string] { _helper_paste (_helper_command "git-diffnav.nu" ["-p" ...$args]) }
alias re = rerun-on-enter

# Jump to the root directory of the current Git repository
def --env __git_root [] {
  let root = (git rev-parse --show-toplevel | str trim)
  if $root == "" {
    print $"Not inside a Git repository \(pwd: ($env.PWD)\)"
  } else {
    cd $root
  }
}

# Convenience alias: `gr` => go to git root
alias gr = __git_root
alias gcd = __git_root

###############################################################################
# Just
###############################################################################

# Custom completer for just recipes
def "nu-complete just-recipes" [] {
    if (not ("./justfile" | path exists)) or (which just | is-empty) { return [] }
    just -f ./justfile -d . --summary | split row ' ' | where { $in != "" }
}

# Pick a recipe, then edit/paste the actual just command for history.
def --env --wrapped ji [...args: string@"nu-complete just-recipes"] {
  if ($args | is-not-empty) { ^just -f ./justfile -d . ...$args; return }
  let recipe = (_helper_command "just-pick-and-print.nu" ["-f" "./justfile" "-d" "."])
  if $recipe != "" { _helper_paste $"just ($recipe | to json --raw)" }
}
alias n = ji
alias j = just
alias jj = ji
alias nn = ji
alias jc = ji
alias je = nvim ./justfile
alias ne = je

def --env ni [] {
  let file = "./.just/justfile"
  let recipe = (_helper_command "just-pick-and-print.nu" ["-f" $file "-d" "."])
  if $recipe != "" { _helper_paste $"just -f ($file | to json --raw) -d . ($recipe | to json --raw)" }
}
alias nie = nvim ./.just/justfile

alias n1 = just n1
alias n2 = just n2
alias n3 = just n3
alias n4 = just n4
alias n5 = just n5
alias n6 = just n6
alias n7 = just n7
alias n8 = just n8
alias n9 = just n9

alias nb = just nb
alias nbr = just build-run
alias nc = just nc
alias nd = just nd
alias ns = just ns
alias np = just np
alias nt = just nt
alias nl = just nl

###############################################################################
# Yazi
###############################################################################
def --env y [...args] {
  let tmp = (mktemp -t "yazi-cwd.XXXXXX")
  yazi ...$args --cwd-file $tmp
  let cwd = (open $tmp)
  if $cwd != "" and $cwd != $env.PWD {
    cd $cwd
  }
  rm -fp $tmp
}

$env.config.keybindings = (
  $env.config.keybindings | append {
    name: yazi_ctrl_y
    modifier: control
    keycode: char_y
    mode: emacs
    event: {
      send: executehostcommand
      cmd: "y"
    }
  }
)

###############################################################################
# Misc Aliases in Alphabetical Order
###############################################################################

alias ai = claude
alias ali = nvim ($nu.default-config-dir | path join alias.nu)
alias c = cl
alias cc = claude
alias cla = claude
alias co = claude
def --env cx [query: string = ""] {
  if (which fd | is-empty) or (which fzf | is-empty) { error make {msg: "cx requires fd and fzf."} }
  let selected = (do { ^fd -H -I -t d --exclude .git | ^fzf --height=60% --reverse --query=$query } | complete)
  if $selected.exit_code == 0 and ($selected.stdout | str trim | is-not-empty) { cl ($selected.stdout | str trim) }
}
alias activate = overlay use .venv/Scripts/activate.nu
alias dea = deactivate
alias chez = chezmoi
alias chezd = cl $"($env.HOME)/.local/share/chezmoi"
alias conf = cl ~/.config/
alias confd = cl ~/.config/
alias fda = fd -H -I
alias ff = fastfetch
alias fmake = fzf-make
alias fm = fzf-make
# Refresh PATH when replacing Nu on Windows. Unlike Linux, Windows has no
# exec(2), so a new shell otherwise inherits the current process's stale PATH.
def exec-nu [] {
  exec powershell.exe -NoProfile -Command '
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = [Environment]::ExpandEnvironmentVariables($machine + ";" + $user)
    nu
  '
}
alias ghpr = do { gh pr view --json url -q .url }
alias gfpa = git fetch --all --prune
alias gl = git log --graph --decorate --oneline
alias gloga = git log --graph --decorate --oneline --all
alias gst = git status
alias gsw = git switch
alias h = cl ..

def he [cmd?: string] {
    if (which bat | is-empty) {
        if ($cmd | is-empty) { $in } else { ^$cmd --help }
        return
    }
    if ($cmd | is-empty) {
        # no argument: act as a pipe filter
        bat -p -l help
    } else {
        let help_output = (do { ^$cmd --help } | complete | get stdout | str trim)
        if ($help_output | is-empty) {
            print $"No help available for: ($cmd)"
        } else {
            $help_output | bat -p -l help
        }
    }
}

alias hg = hgrep
alias i = cl
alias ii = explorer.exe
alias je = nvim ./justfile

def lf [...file: string] {
    if (which eza | is-not-empty) {
      l --only-files ...$file
    } else {
      ls ...($file | default [])
    }
}

alias lz = lazygit
alias nvimh = cl '~/AppData/Local/nvim/'

def --env mc [dir: string] {
  mkdir $dir
  cl $dir
}

alias mycub = cl ~/my-cubrid/
alias ppath = echo $env.Path
alias rga = rg --hidden --no-ignore
alias rgall = rg --hidden --no-ignore
alias sl = l
alias prof = nvim $"($env.HOME)/.local/share/chezmoi/AppData/Roaming/nushell/config.nu"
alias t = just default
alias ts = tspin
alias todo = nvim ~/.todo.md
alias v = nvim
alias w = which
alias wa = which -a
alias ze = zellij
alias ba = bm add
alias bd = bm del
alias bl = bm list
