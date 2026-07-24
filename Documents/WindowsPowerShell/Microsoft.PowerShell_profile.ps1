# Keep Windows PowerShell compatible by loading the maintained PowerShell 7
# profile. The shared file intentionally uses syntax supported by 5.1.
$sharedProfile = Join-Path $HOME 'Documents\PowerShell\Microsoft.PowerShell_profile.ps1'
if (Test-Path -LiteralPath $sharedProfile) {
    . $sharedProfile
}
