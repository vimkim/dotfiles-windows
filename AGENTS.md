# Windows chezmoi repository guidance

This directory is the chezmoi source repository. Edit files here, not their
deployed copies under `%USERPROFILE%`.

When changing a managed file:

1. Inspect `chezmoi diff -- <exact-target>` and preserve intentional target
   drift in the source.
2. Change the corresponding source file.
3. Run the affected application's validation.
4. Apply only the exact target with `chezmoi apply -- <exact-target>`.
5. Run the validation again and inspect `chezmoi status`.

Never run `chezmoi apply --force`. Do not use a broad `chezmoi apply` while
managed targets have local changes. Do not import Linux absolute paths,
Linuxbrew commands, POSIX-only helpers, or Linux credential helpers into
Windows configuration.

Optional commands must be guarded so their absence cannot prevent Nushell or
PowerShell from starting.
