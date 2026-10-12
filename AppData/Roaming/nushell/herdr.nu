# New Herdr panes share one background reporter per session. Python is optional;
# skip Windows' App Installer alias when no actual Python is installed.
if (($env.HERDR_ENV? | default "") == "1") and (($env.HERDR_SOCKET_PATH? | default "") != "") {
  let python = (which python | where {|cmd| not ($cmd.path | str contains '\Microsoft\WindowsApps\') })
  let reporter = ($nu.home-dir | path join ".local" "bin" "herdr_tab_status.py")
  if ($python | is-not-empty) and ($reporter | path exists) {
    let executable = ($python | first | get path)
    try { do { ^$executable -X utf8 $reporter start } | complete | ignore } catch { }
  }
}
