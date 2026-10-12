def --wrapped main [...command: string] {
  if ($command | is-empty) { error make {msg: "Usage: rerun-on-enter COMMAND [ARG ...]"} }
  if $command.0 in ["--help" "-h"] { print "Usage: rerun-on-enter command [arg ...]"; return }
  let executable = $command.0
  loop {
    do --ignore-errors { ^$executable ...($command | skip 1) }
    let code = ($env.LAST_EXIT_CODE? | default 0)
    print $"Finished with exit code ($code)."
    if ((input "Enter to run again, q to quit: ") | str lowercase) == "q" { break }
  }
}
