alias fzfm = fzf --height 60% --reverse

###############################################################################
# cd & ls
###############################################################################

def --wrapped l [...args] {
  if (which eza | is-not-empty) {
    eza --icons=auto --group-directories-first ...$args
  } else {
    ls ...$args
  }
}
def --env cl [
  dir?: string # Optional argument
] {
  let target_dir = if $dir != null {
    $dir
  } else {
    ls -a | where type in ['dir' 'symlink'] | sort-by modified -r | get name | to text | fzfm
  }

  if $target_dir != null {
    cd $target_dir
    l
  } else {
    print "No directory selected."
  }
}

def vc [query?: string] {
  let file = (
    ls -a
    | where type in ['file' 'symlink']
    | sort-by modified -r
    | get name
    | str join (char nl)
    | fzfm --query ($query | default "")
  )

  if $file != "" {
    nvim $file
  }
}

def --env cf [query?: string] {
  let selected = (
    fd --type f --type l --no-ignore --hidden --follow
    | fzfm --query ($query | default "")
  )

  if $selected != null and ($selected | str trim) != "" {
    cd ($selected | path dirname)
  }
}

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
    if (not ("./justfile" | path exists)) { return [] }
    just -f ./justfile -d . --summary | split row ' ' | where { $in != "" }
}

# n: no args → fzf + paste to edit line; with args → execute just directly
def --env --wrapped n [...args: string@"nu-complete just-recipes"] {
    if ($args | is-empty) {
        commandline edit (just.nu -f ./justfile -d . | str trim)
    } else {
        just -f ./justfile -d . ...$args
    }
}

alias j = just
alias jj = just --choose
alias nn = just --choose
alias jc = just --choose
alias je = nvim ./justfile
alias ne = je
alias ni = commandline edit (just.nu -f ./.just/justfile -d . | str trim)
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
alias cx = cl (fd -H -I -t d | fzfm)
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
      eza ...($file | default []) -a -l --icons=always --color=always --sort=modified --only-files --show-symlinks
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
