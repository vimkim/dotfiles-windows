# config.nu
#
# Installed by:
# version = "0.104.0"
#
# This file is used to override default Nushell settings, define
# (or import) custom commands, or run any other startup tasks.
# See https://www.nushell.sh/book/configuration.html
#
# This file is loaded after env.nu and before login.nu
#
# You can open this file in your default editor using:
# config nu
#
# See `help config nu` for more options
#
# You can remove these comments if you want or leave
# them for future reference.

# required for 'path add .../bin'
use std/util "path add"

$env.HOME = $env.USERPROFILE
$env.EDITOR = 'nvim'

mkdir ($nu.data-dir | path join "vendor/autoload")
starship init nu | save -f ($nu.data-dir | path join "vendor/autoload/starship.nu")

alias fzfm = fzf --height 60% --reverse

source ($nu.default-config-dir | path join eza.nu)
use ($nu.default-config-dir | path join mise.nu)

$env.config.rm.always_trash = true
$env.config.show_banner = false

# fzf-tab like completion
$env.config.completions = {
  case_sensitive: false
  algorithm: "fuzzy"
  external: {
    enable: true
  }
}

$env.config.buffer_editor = 'nvim'

$env.CMAKE_EXPORT_COMPILE_COMMANDS = 'ON'

if (which sccache | is-not-empty) {
  export-env {
    $env.RUSTC_WRAPPER = 'sccache'
  }
}

###############################################################################
# cd & ls
###############################################################################

alias ze = wsl -- SHELL=nu.exe /home/linuxbrew/.linuxbrew/bin/zellij

alias l = ezam
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
alias na = commandline edit (just.nu -f ~/.config/my-scripts/justfile -d . | str trim)
alias nae = nvim ~/.config/my-scripts/justfile

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

def clip [] {
  if ($nu.os-info.name == "linux") {
    if (which wl-copy | is-empty) and (which xclip | is-empty) {
      print "Error: neither 'xclip' nor 'wl-copy' is installed"
    } else {
      $in | xclip -selection clipboard
    }
  } else if (open /proc/version | str contains "microsoft") {
    $in | clip.exe
  } else if ($nu.os-info.name == "windows") {
    $in | clip.exe
  } else if ($nu.os-info.name == "macos") {
    $in | pbcopy
  } else {
    print "Unsupported OS"
  }
}

alias x = commandline edit (~/.config/my-scripts/bin/autorun.sh | str trim)
alias xe = nvim ~/.config/my-scripts/bin/autorun.sh

###############################################################################
# Directory History
###############################################################################

let history_file = ($env.HOME | path join ".local" "share" "nu" "dirlog.json")

if (
  'PWD' not-in $env.config.hooks.env_change
) {
  $env.config.hooks.env_change.PWD = []
}


$env.config.hooks.env_change.PWD = (
  $env.config.hooks.env_change.PWD | append {|before after|
    # ensure directory & file exist
    if not ($history_file | path exists) {
      mkdir ($history_file | path dirname)
      [] | save --force $history_file
    }
    open $history_file
    | collect # gather into a list
    | prepend $after # new $after at index 0
    | uniq # de‐duplicate (keeps first occurrence)
    | take 60 # keep most recent 60
    | save --force $history_file
  }
)

def view-dir-history [] {
  if ($history_file | path exists) {
    open $history_file
  } else {
    print "No directory history found."
  }
}
alias vh = view-dir-history

def --env cd-dir-history [] {
  if not ($history_file | path exists) {
    print "No directory history found."
    return
  }

  let dir = (open $history_file | to text | fzfm)
  if $dir == "" {
    print "No directory selected."
    return
  }

  if ($dir | path exists) {
    cl $dir
  } else {
    # Remove the missing path from the history file
    open $history_file
    | collect
    | where { $in != $dir }
    | save --force $history_file

    print $"Removed missing path from history: ($dir)"
  }
}
alias ch = cd-dir-history

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
alias ali = nvim ~/.local/share/chezmoi/private_dot_config/nushell/alias.nu
alias c = cl
alias cc = claude
alias cla = claude
alias co = claude
alias cx = cl (fd -H -I -t d | fzfm)
alias activate = overlay use .venv/bin/activate.nu
alias dea = deactivate
alias chez = chezmoi
alias chezd = cl $"($env.HOME)/.local/share/chezmoi"
alias conf = cl ~/.config/
alias confd = cl ~/.config/
alias fda = fd -H -I
alias ff = fastfetch
alias fmake = fzf-make
alias fm = fzf-make
alias ghc = ~/.config/my-scripts/bin/github-clone-confirm.sh
alias ghcf = ~/.config/my-scripts/bin/gh-clone-fuzzy.sh
alias ghcu = ~/.config/my-scripts/bin/git-clone-user.sh
alias ghpr = do { gh pr view --json url -q .url }
alias gfpa = git fetch --all --prune
alias gl = ~/.config/my-scripts/bin/git-log.sh
alias glf = ~/.config/my-scripts/bin/git-log-find.sh
alias gloga = with-env {GL_OPS: "--all"} { git-log.sh }
alias gst = git status
alias gsw = git switch
alias h = cl ..

def he [cmd?: string] {
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
alias ii = explorer
alias je = nvim ./justfile

def lf [...file: string] {
    eza ...($file | default []) -a -l --icons=always --color=always --sort=modified --only-files --show-symlinks | less -rXFS
}

alias lj = lazyjj
alias lz = lazygit
alias lzd = lazydocker
alias nvimh = cl '~/AppData/Local/nvim/'

def --env mc [dir: string] {
  mkdir $dir
  cl $dir
}

alias mycub = cl ~/my-cubrid/
alias ppath = echo $env.Path
alias rga = rg --hidden --no-ignore
alias rgall = rg --hidden --no-ignore
alias rgf = rgf.sh
alias sl = l
alias prof = nvim $"($env.HOME)/.local/share/chezmoi/AppData/Roaming/nushell/config.nu"
alias t = just default
alias ts = tspin
alias todo = nvim ~/.todo.md
alias v = nvim
alias w = which
alias wa = which -a
alias ze = zellij
alias zs = zellij -s
alias zshrc = nvim ~/.local/share/chezmoi/dot_zshrc

alias za = do { wsl -- SHELL=nu.exe /home/linuxbrew/.linuxbrew/bin/zellij }

source ($nu.default-config-dir | path join bookmark.nu)
source ($nu.default-config-dir | path join zellij.nu)

alias ba = bm add
alias bd = bm del
alias bl = bm list

# Zellij tab name update on directory change
$env.config.hooks.env_change.PWD = (
  $env.config.hooks.env_change.PWD | append {|before after|
    zellij-update-tabname-git
  }
)

# c compiler error for nvim-treesitter
path add 'C:\msys64\mingw64\bin'

# winget-installed packages
# path add ($env.LOCALAPPDATA | path join "Microsoft" "WinGet" "Packages" "Atuinsh.Atuin_Microsoft.Winget.Source_8wekyb3d8bbwe")

source ~/.local/share/atuin/init.nu

###############################################################################
# Shell Startup Decoration
###############################################################################

if ("CLAUDE" not-in $env) { fastfetch }
