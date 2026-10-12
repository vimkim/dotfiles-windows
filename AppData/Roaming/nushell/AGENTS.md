# Windows Nushell Configuration Guidance

Edit the chezmoi source file, not the deployed configuration. On native Windows,
Nushell normally stores its configuration in `%APPDATA%\nushell`; use
`$nu.default-config-dir` inside Nushell to resolve its actual default directory.
Do not import the Linux Nushell configuration location.

In Nushell, `source` and `use` are parser-time keywords. Any file they reference
must exist when `config.nu` is parsed. Do not guard them with runtime conditions
or reference optional files directly; select an existing file (or `null`) at
parse time instead.

For an optional sourced file, use a `const` whose value is decided while parsing:

```nu
const optional_init = if (($nu.default-config-dir | path join 'optional.nu') | path exists) {
  $nu.default-config-dir | path join 'optional.nu'
} else {
  null
}
source $optional_init
```

Use the same pattern with `use $optional_module` for optional modules. Nushell
treats a `null` target as a no-op. This pattern is verified with Nushell 0.114.1.
For a custom `--config` file outside the default directory, resolve its intended
import directory explicitly. Guard optional executables with `which` before
calling them. Generated integration files remain machine-local unless the
repository explicitly manages them.

Before changing a managed file, inspect `chezmoi --source <absolute-task-checkout>
diff -- <absolute-target>` and preserve intentional target drift in the source.
Validate before applying, apply one absolute file target, then validate again
and inspect `chezmoi status`. Never use `chezmoi apply --force` or a broad apply.
If the configured diff tool or pager is missing, add `--use-builtin-diff
--no-pager` to the chezmoi diff command.

For configuration changes, run the equivalent of these PowerShell commands,
using the actual task checkout and deployed target:

```powershell
$taskCheckout = (Get-Location).Path
nu --no-config-file -c 'nu-check .\AppData\Roaming\nushell\config.nu'
chezmoi --source $taskCheckout apply -- "$env:APPDATA\nushell\config.nu"
nu --login -c 'exit'
```

For these Markdown instructions, validate rendered contents and shared copies.
`CLAUDE.md.tmpl` includes this `AGENTS.md`; edit only this source, then apply
`%APPDATA%\nushell\AGENTS.md` and `%APPDATA%\nushell\CLAUDE.md` separately.
