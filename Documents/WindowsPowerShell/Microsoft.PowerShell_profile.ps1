# git branch -m main test

# emacs keybinding such as ctrl-w
$ErrorActionPreference = "Stop" # this will stop the script on error

# This makes ctrl+w not work
#set-psreadlineoption -editmode vi

# Alt (Esc) + f, b moves the cursor forward and backward by a word.
Set-PSReadLineOption -editmode Emacs

# enables bash-like autocompletion. Default: ctrl + space
# This must be below Set-PSReadLineOption -editmode. Otherwise not work...
Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete
# In order to accept a weird auto suggestion called 'predictive intellisense', press either right arrow or ctrl+f.

# How to use backward search (ctrl + r):
# ctrl r: ReverseSearchHistory
# ctrl s: ForwardSearchHistory

set-alias v nvim

function nvprofile() {
    nvim $home/AppData/Local/nvim/init.vim
}

function nvimh() {
    cd $home/AppData/Local/nvim/
}

function nvimrc() {
    nvim $home/AppData/Local/nvim/init.lua
}

function nvconfig() {
    cd $env:LOCALAPPDATA/nvim/
}

function chezd() {
    cd $home/.local/share/chezmoi/
}

function temp() {
    cd $home/temp
}

set-alias tmp temp

function gst() { git status }

function gad() { git add @args }

function gcm() { git commit @args }

function which() { get-command -all @args }

#function x() { python main.py }
function x() {
    if (Test-Path main.py) {
        python main.py @args
    }
    elseif (Test-Path main.js) {
        node main.js @args
    }
}

function algo() {
    cd "$githubPath\algorithms\"
}

function r() { python @args }

function mc() { mkdir @args ; cd @args }

function co() { code @args }

function profile() {
    nvim $profile
}

function profiledir() {
    cd "$home\Documents\WindowsPowerShell\"
}

# No use. It requires admin previlege anyway...
function ln ($target, $link) {
    new-item -path $link -itemtype SymbolicLink -value $target
}

function dotfiles() {
    set-location "$home\Documents\Github\dotfiles"
}

function diffBinary() {
    fc.exe @args;
}

### CG hw 3 begin ###

$githubPath = "$home/Documents/github"

function cg() {
    set-location "$githubPath/cg-hw3"
}

function hw() {
    set-location "$githubPath/cg-hw3"
}

function ppt() {
    ii C:\Users\kimdh\Documents\ku4-1\cg\hw3.pptx
}

### CG hw 2 end ###


### cl begin ###

function _ls { Get-ChildItem @args -Force | format-wide -property name -column 5 }

Set-Alias l _ls
Set-Alias -Name ls -Value _ls -Option AllScope

function ll { Get-ChildItem }

function _cd {
    # for pipelines to work
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        $_cd_paths
    )
    if ($null -eq $_cd_paths) {
        Set-Location $home
    }
    else {
        Set-Location $_cd_paths
    }
    #if ($args.count -eq 0){
    #    Set-Location $home
    #}
    #else{
    #    Set-Location @args
    #}
}

Set-Alias -Name cd -Value _cd -Option AllScope
function cl {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline)]
        $_cd_paths
    )
    If ($null -ne $_cd_paths) {
        _cd $_cd_paths
    }
    _ls
}

function c { cl @args; }
### cl end ###


### baekjoon begin ###
function cpm {
    cat main.py | clip
}

function cppy {
    cat main.py | clip
}

function cpcpp {
    cat main.cpp | clip
}

function mco($dir) {
    mkdir $dir ; code $dir
}

function prepare($dir) {
    if (Test-Path -Path $dir) {
        "Path already exists!"
        return
    }
    mkdir $dir;
    # copy-item -Path "$env:userprofile\Documents\Github\algorithms\template\*" -Destination $dir -recurse
    copy-item -Path "$env:userprofile\Documents\Github\algorithms\template\main.py" -Destination $dir -recurse
}

function play($dir) {
    #new-item $dir/main.py;
    #new-item $dir/i2;
    prepare $dir
    cd $dir;
    code -r .
    code --goto main.py:23:4
    #code --goto main.cpp:70:4
}

function compete($dir) {
    mkdir $dir;
    cd $dir;
    prepare A;
    prepare B;
    prepare C;
    prepare D;
    prepare E;
    prepare F;
}
function cz {
    zoxide query -l | fzf | cl
}


# Do not forget the .fdignore setting
function cx { fd --type d | fzf | cl }
function vcx { set-location ; fd --type d | fzf | cl }



# Import the Chocolatey Profile that contains the necessary code to enable
# tab-completions to function for `choco`.
# Be aware that if you are missing these lines from your profile, tab completion
# for `choco` will not function.
# See https://ch0.co/tab-completion for details.
$ChocolateyProfile = "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
if (Test-Path($ChocolateyProfile)) {
  Import-Module "$ChocolateyProfile"
}

oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/hunk.omp.json" | Invoke-Expression # This must be in front of any prompt modification such as pipenv.
