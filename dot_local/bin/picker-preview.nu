def main [index_file: path, index: int] {
  let item = (open $index_file | get $index)
  match $item.kind {
    "recipe" => { ^just -f $item.justfile -d $item.justdir --color always --show $item.value }
    "git-ref" => {
      if $item.value == "@working" { ^git --no-pager diff HEAD --stat } else {
        ^git --no-pager log --oneline --graph --decorate --color=always -n 30 $item.value --
      }
    }
    "git-commit" => { ^git --no-pager show --color=always --stat -p $item.value -- }
    "directory" => { ls -a $item.value | first 100 | table }
  }
}
