#!/usr/bin/env python3
"""Exec wrapper that runs Antigravity CLI with permission prompts bypassed."""

from __future__ import annotations

import shutil
import subprocess
import sys

USAGE = """usage: ay [AGY_ARGS...]

Exec wrapper that runs Antigravity CLI with permission prompts bypassed:
  agy --dangerously-skip-permissions ...

Options:
  -h, --help     Show this help message and exit
  --version      Show wrapper info and the underlying agy version

Use "ay -- --help" or "ay -- --version" to pass those flags through to agy.
"""


def find_agy() -> str | None:
    return shutil.which("agy")


def print_version() -> None:
    agy_bin = find_agy()
    if agy_bin:
        try:
            result = subprocess.run(
                [agy_bin, "--version"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                first_line = result.stdout.splitlines()[0].strip()
                print(
                    f"ay: exec wrapper for agy --dangerously-skip-permissions (agy {first_line})"
                )
                return
        except OSError:
            pass
    print("ay: exec wrapper for agy --dangerously-skip-permissions (agy version unavailable)")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        if args[0] in ("-h", "--help"):
            sys.stdout.write(USAGE)
            return 0
        if args[0] == "--version":
            print_version()
            return 0
        if args[0] == "--":
            args = args[1:]

    agy_bin = find_agy()
    if not agy_bin:
        print("ay: agy was not found on PATH", file=sys.stderr)
        return 127

    try:
        completed = subprocess.run(
            [agy_bin, "--dangerously-skip-permissions", *args],
            check=False,
        )
        return completed.returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
