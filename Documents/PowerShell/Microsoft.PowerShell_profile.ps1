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
$wingetPackages = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
Get-ChildItem -LiteralPath $wingetPackages -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(ajeetdsouza\.zoxide_|Casey\.Just_)' } |
    ForEach-Object { Add-ProcessPath $_.FullName }

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

if ($env:TERM -ne 'dumb' -and (Get-Command starship -ErrorAction SilentlyContinue)) {
    try { Invoke-Expression (&starship init powershell) } catch {
        Write-Verbose "Starship initialization skipped: $($_.Exception.Message)"
    }
} elseif ($env:TERM -ne 'dumb' -and (Get-Command oh-my-posh -ErrorAction SilentlyContinue)) {
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

function Get-PickedFile {
    param([string]$Query = '', [int]$MaxDepth = 0, [switch]$NoIgnore, [switch]$NoHidden)
    if (-not (Get-Command file-picker -ErrorAction SilentlyContinue) -or
        -not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Warning 'The file picker requires the managed helper and Python 3.'
        return
    }
    $pickerArgs = @('--json', "--query=$Query")
    if ($MaxDepth -gt 0) { $pickerArgs += @('--max-depth', "$MaxDepth") }
    if ($NoIgnore) { $pickerArgs += '--no-ignore' }
    if ($NoHidden) { $pickerArgs += '--no-hidden' }
    $selection = & file-picker @pickerArgs
    if ($LASTEXITCODE -eq 0 -and $selection) { $selection | ConvertFrom-Json }
}

function vc {
    param([string]$Query = '', [int]$MaxDepth = 1, [switch]$NoIgnore, [switch]$NoHidden)
    $selected = Get-PickedFile -Query $Query -MaxDepth $MaxDepth -NoIgnore:$NoIgnore -NoHidden:$NoHidden
    if ($selected) { & $env:EDITOR $selected }
}

function cf {
    param([string]$Query = '', [int]$MaxDepth = 0, [switch]$NoIgnore, [switch]$NoHidden)
    $selected = Get-PickedFile -Query $Query -MaxDepth $MaxDepth -NoIgnore:$NoIgnore -NoHidden:$NoHidden
    if ($selected) { cl ([IO.Path]::GetDirectoryName($selected)) }
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
    if ((Get-Command ls-by-time -ErrorAction SilentlyContinue) -and
        (Get-Command python -ErrorAction SilentlyContinue) -and
        (Get-Command eza -ErrorAction SilentlyContinue)) {
        ls-by-time --no-user --no-permissions --icons=auto @args
    } elseif (Get-Command eza -ErrorAction SilentlyContinue) {
        eza --all --long --sort=modified --reverse --icons=auto @args
    } else {
        Get-ChildItem -Force @args
    }
}
Set-Alias -Name l -Value Invoke-List
function ll {
    Invoke-List @args
}

function cl {
    param([Parameter(ValueFromPipeline = $true)][string]$Path, [string]$Query = '')
    process {
        if ($Path -and -not $PSBoundParameters.ContainsKey('Query')) {
            Set-Location -LiteralPath $Path
        } else {
            if (-not (Get-Command dir-picker -ErrorAction SilentlyContinue) -or
                -not (Get-Command python -ErrorAction SilentlyContinue)) {
                Write-Warning 'The directory picker requires the managed helper and Python 3.'
                return
            }
            $pickerArgs = @('--json', "--query=$Query")
            if ($Path) { $pickerArgs += @('--', $Path) }
            $selection = & dir-picker @pickerArgs
            if ($LASTEXITCODE -ne 0 -or -not $selection) { return }
            Set-Location -LiteralPath ($selection | ConvertFrom-Json)
        }
        Invoke-List
    }
}
Set-Alias -Name c -Value cl
Set-Alias -Name cv -Value cl

function cz {
    if (-not (Get-Command zi -ErrorAction SilentlyContinue)) {
        Write-Warning 'cz requires zoxide.'
        return
    }
    zi @args
    Invoke-List
}

function cx {
    param([string]$Query = '')
    if (-not (Get-Command fd -ErrorAction SilentlyContinue) -or
        -not (Get-Command fzf -ErrorAction SilentlyContinue)) {
        Write-Warning 'cx requires fd and fzf.'
        return
    }
    $selected = fd --type d --hidden --no-ignore --exclude .git | fzf --height 60% --reverse "--query=$Query"
    if ($LASTEXITCODE -eq 0 -and $selected) { cl $selected }
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
