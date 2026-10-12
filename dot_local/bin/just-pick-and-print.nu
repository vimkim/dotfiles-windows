use picker-common.nu [checked pick-record]

def main [--justfile (-f): path = "./justfile", --justdir (-d): path = "."] {
  if not ($justfile | path exists) { error make {msg: $"Justfile not found: ($justfile)"} }
  if not ($justdir | path exists) { error make {msg: $"Directory not found: ($justdir)"} }
  let file = ($justfile | path expand)
  let directory = ($justdir | path expand)
  let dump = (checked [just -f $file -d $directory --dump --dump-format json] | from json)
  let defaults = ($dump.recipes | values | where {|recipe| 'default' in $recipe.attributes } | get name)
  let other = (checked [just -f $file -d $directory --summary --unsorted] | split row " " | where {|name| $name != "" and $name not-in $defaults })
  let records = ($defaults | append $other | each {|name|
    {kind: recipe, value: $name, label: $name, justfile: $file, justdir: $directory}
  })
  let selected = (pick-record $records "" "just> ")
  if $selected != null { print $selected.value }
}
