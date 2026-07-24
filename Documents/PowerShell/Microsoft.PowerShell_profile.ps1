# Shared Windows profile. PowerShell 7 is primary; Windows PowerShell loads this
# file from its small compatibility profile.

$env:EDITOR = if (Get-Command nvim -ErrorAction SilentlyContinue) { 'nvim' } else { 'notepad.exe' }
$env:VISUAL = $env:EDITOR

function Add-ProcessPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) { return }
    $entries = @($env:Path -split ';' | Where-Object { $_ })
    if ($entries -notcontains $Path) {
        $env:Path = "$Path;$env:Path"
    }
}

Add-ProcessPath (Join-Path $HOME '.local\bin')
Add-ProcessPath (Join-Path $env:LOCALAPPDATA 'mise\shims')

if (Get-Module -ListAvailable -Name PSReadLine) {
    try {
        Import-Module PSReadLine -ErrorAction Stop
        Set-PSReadLineOption -EditMode Emacs
        Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
    } catch {
        Write-Verbose "PSReadLine initialization skipped: $($_.Exception.Message)"
    }
}

if (Get-Module -ListAvailable -Name PSFzf) {
    try { Import-Module PSFzf -ErrorAction Stop } catch {
        Write-Verbose "PSFzf import skipped: $($_.Exception.Message)"
    }
}
if (Get-Command Set-PSFzfOption -ErrorAction SilentlyContinue) {
    Set-PSFzfOption -PSReadLineChordProvider 'ctrl+t' -PSReadLineChordReverseHistory 'ctrl+r'
}

if (Get-Command starship -ErrorAction SilentlyContinue) {
    try { Invoke-Expression (&starship init powershell) } catch {
        Write-Verbose "Starship initialization skipped: $($_.Exception.Message)"
    }
} elseif (Get-Command oh-my-posh -ErrorAction SilentlyContinue) {
    try { (&oh-my-posh init pwsh | Out-String) | Invoke-Expression } catch {
        Write-Verbose "oh-my-posh initialization skipped: $($_.Exception.Message)"
    }
}

if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    try {
        $hook = if ($PSVersionTable.PSVersion.Major -lt 6) { 'prompt' } else { 'pwd' }
        (&zoxide init --hook $hook powershell | Out-String) | Invoke-Expression
    } catch {
        Write-Verbose "zoxide initialization skipped: $($_.Exception.Message)"
    }
}

function Invoke-Editor { & $env:EDITOR @args }
Set-Alias -Name v -Value Invoke-Editor

function vc {
    if (-not (Get-Command fzf -ErrorAction SilentlyContinue)) {
        Write-Warning 'vc requires fzf.'
        return
    }
    $selected = Get-ChildItem -Force -File | Select-Object -ExpandProperty FullName | fzf --height 60% --reverse
    if ($selected) { & $env:EDITOR $selected }
}
Set-Alias -Name vv -Value vc

function chezd { Set-Location (Join-Path $HOME '.local\share\chezmoi') }
function temp { Set-Location (Join-Path $HOME 'temp') }
Set-Alias -Name tmp -Value temp

function nvimh { Set-Location (Join-Path $env:LOCALAPPDATA 'nvim') }
function nvimrc { & $env:EDITOR (Join-Path $env:LOCALAPPDATA 'nvim\init.lua') }
function Edit-Profile { & $env:EDITOR $PROFILE }

function gst { git status @args }
function gd { git diff @args }
function gb { git branch @args }
function gl { git log --graph --decorate --oneline @args }
function gloga { git log --graph --decorate --oneline --all @args }
function ga { git add @args }
function gcm { git commit -m @args }
function gp { git pull @args }
function gps { git push @args }
function gf { git fetch @args }
function gsw { git switch @args }
function gw { git worktree @args }
function gcd {
    $root = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $root) {
        Write-Warning 'Not inside a Git repository.'
        return
    }
    Set-Location $root
}

function Get-CommandInfo {
    Get-Command -All @args | Select-Object Name, Definition, CommandType, Source | Format-List
}
Set-Alias -Name which -Value Get-CommandInfo

function Invoke-List {
    if (Get-Command eza -ErrorAction SilentlyContinue) {
        eza --icons=auto --group-directories-first @args
    } else {
        Get-ChildItem -Force @args
    }
}
Set-Alias -Name l -Value Invoke-List
function ll {
    if (Get-Command eza -ErrorAction SilentlyContinue) {
        eza --icons=auto --group-directories-first -la @args
    } else {
        Get-ChildItem -Force @args | Format-Table
    }
}

function cl {
    param([Parameter(ValueFromPipeline = $true)][string]$Path)
    process {
        if ($Path) { Set-Location -LiteralPath $Path }
        Invoke-List
    }
}

function cx {
    if (-not (Get-Command fd -ErrorAction SilentlyContinue) -or
        -not (Get-Command fzf -ErrorAction SilentlyContinue)) {
        Write-Warning 'cx requires fd and fzf.'
        return
    }
    $selected = fd --type d --hidden --no-ignore | fzf --height 60% --reverse
    if ($selected) { Set-Location -LiteralPath $selected }
}

function ppath { $env:Path -split ';' }

$isInteractiveTopLevel = (
    $Host.Name -eq 'ConsoleHost' -and
    [Environment]::UserInteractive -and
    -not [Console]::IsInputRedirected -and
    -not [Console]::IsOutputRedirected -and
    -not $env:CI -and
    -not $env:CLAUDE -and
    -not $env:CODEX_HOME
)
if ($isInteractiveTopLevel -and (Get-Command fastfetch -ErrorAction SilentlyContinue)) {
    fastfetch
}
