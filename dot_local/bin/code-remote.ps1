# Get SSH hosts, pipe to fzf, and use the selection to launch VS Code
$selectedHost = (Get-Content "$env:USERPROFILE\.ssh\config" |
    Select-String -Pattern "^\s*Host\s+" |
    ForEach-Object { $_.Line.Trim() -replace "Host ", "" } |
    Where-Object { $_ -notmatch "\*|\?" } |
    Out-String).Trim() |
    fzf --height 40% --reverse |
    Out-String

# Remove any trailing whitespace/newlines
$selectedHost = $selectedHost.Trim()

# If a host was selected, launch VS Code
if ($selectedHost) {
    Write-Host "Connecting to $selectedHost..."
    # Launch VS Code with remote SSH connection
    code --remote ssh-remote+$selectedHost
}
