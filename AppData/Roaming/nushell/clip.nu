def clip [] {
  let input = $in
  if ($nu.os-info.name != "windows") {
    error make $"Unsupported OS for this Windows dotfiles module: ($nu.os-info.name)"
  }
  if (which clip.exe | is-empty) {
    error make "Windows clipboard command 'clip.exe' is unavailable"
  }
  $input | clip.exe
}
