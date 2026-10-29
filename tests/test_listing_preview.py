"""Exercise Windows previews with real eza, deterministic terminal sizes, and wrappers."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
BIN = REPO / "dot_local/bin"
PLAIN = ["--no-user", "--no-permissions", "--no-filesize", "--no-time",
         "--no-git", "--classify=never", "--color=never", "--icons=never"]
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")


@unittest.skipUnless(shutil.which("eza"), "requires eza")
class ListingPreviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="listing space & 한글 ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def entries(self, count, suffix=""):
        for index in range(count):
            path = self.root / f"entry-{index:03}{suffix}"
            if index % 2:
                path.touch()
            else:
                path.mkdir()
            os.utime(path, (100 + index, 100 + index))

    def listing(self, name="ls-one-page", *args, terminal=False, rows=12, columns=60):
        if terminal:
            # Keep the real eza process; control only the terminal reported to
            # the helper so wrapping and overflow expectations stay reproducible.
            code = (
                "import os, runpy, sys; "
                "sys.stdout.isatty = lambda: True; "
                f"os.get_terminal_size = lambda fd=1: os.terminal_size(({columns}, {rows})); "
                f"sys.argv = {[str(BIN / 'listing.py'), name, *PLAIN, *map(str, args)]!r}; "
                f"runpy.run_path({str(BIN / 'listing.py')!r}, run_name='__main__')"
            )
            command = [sys.executable, "-X", "utf8", "-c", code]
        else:
            command = [sys.executable, "-X", "utf8", str(BIN / "listing.py"), name, *PLAIN, *map(str, args)]
        return subprocess.run(command, cwd=self.root, capture_output=True, encoding="utf-8", timeout=15)

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_terminal_grid_caps_height_and_keeps_global_newest_prefix(self):
        self.entries(450)
        for rows in (12, 20, 40):
            with self.subTest(rows=rows):
                output = self.success(self.listing(terminal=True, rows=rows))
                lines = output.splitlines()
                self.assertEqual(len(lines), rows * 7 // 10)
                names = re.findall(r"entry-\d{3}", "\n".join(lines[:-1]))
                self.assertEqual(len(names), 4 * (len(lines) - 1))
                self.assertEqual(sorted(names, reverse=True),
                                 [f"entry-{i:03}" for i in range(449, 449 - len(names), -1)])
                self.assertTrue(all(len(line) <= 60 for line in lines[:-1]))
                self.assertEqual(lines[-1], f"... {450 - len(names)} entries skipped. Run ls-full or lsf to view all.")
        reverse = self.success(self.listing("ls-one-page", "--reverse", terminal=True))
        self.assertIn("entry-000", reverse)
        self.assertNotIn("entry-449", reverse)

    def test_unicode_colors_hyperlinks_and_wrapped_notice(self):
        self.entries(100, " two  spaces 界")
        output = self.success(self.listing("ls-one-page", "--color=always", "--hyperlink",
                                           terminal=True, columns=160))
        self.assertIn("\x1b[", output)
        self.assertIn("\x1b]8;", output)
        plain = ANSI.sub("", output)
        lines = plain.splitlines()
        names = re.findall(r"entry-\d{3}", "\n".join(lines[:-1]))
        self.assertLessEqual(len(lines), 8)
        self.assertGreater(len(names), 7)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(sorted(names, reverse=True),
                         [f"entry-{i:03}" for i in range(99, 99 - len(names), -1)])
        self.assertEqual(plain.count("two  spaces 界"), len(names))
        self.assertIn(f"... {100 - len(names)} entries skipped.", lines[-1])
        narrow = self.success(self.listing(terminal=True, columns=20))
        self.assertLessEqual(sum(max(1, (len(line) + 19) // 20) for line in narrow.splitlines()), 8)

    def test_pipes_full_and_no_pager_are_complete(self):
        self.entries(450)
        expected = [f"entry-{i:03}" for i in range(449, -1, -1)]
        for name in ("ls-one-page", "ls-full", "lsf"):
            with self.subTest(name=name):
                self.assertEqual(self.success(self.listing(name)).splitlines(), expected)
        for name in ("ls-one-page", "ls-full", "lsf"):
            args = ("--no-pager",) if name == "ls-one-page" else ()
            output = self.success(self.listing(name, *args, terminal=True))
            self.assertEqual(len(re.findall(r"entry-\d{3}", output)), 450)
            self.assertNotIn("skipped", output)
        for name in ("ls-one-page", "ls-full", "lsf"):
            result = subprocess.run([str(BIN / f"{name}.cmd"), *PLAIN, str(self.root)],
                                    capture_output=True, encoding="utf-8", timeout=15)
            self.assertEqual(self.success(result).splitlines(), expected)

    def test_hidden_entries_short_listing_and_error_status(self):
        self.entries(3)
        hidden = self.root / ".hidden 한글"
        hidden.touch()
        os.utime(hidden, (500, 500))
        output = self.success(self.listing(terminal=True, columns=20))
        self.assertIn(hidden.name, output)
        self.assertNotIn("skipped", output)
        for name in ("ls-one-page", "ls-full", "lsf"):
            missing = self.listing(name, self.root / "absent", terminal=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("absent", missing.stderr)

    def test_nushell_l_sl_and_powershell_l_use_the_preview(self):
        self.entries(12)
        alias_source = (REPO / "AppData/Roaming/nushell/alias.nu").read_text(encoding="utf-8")
        alias_source = alias_source.replace('const helper_bin = ($nu.home-dir | path join ".local" "bin")',
                                            "const helper_bin = " + json.dumps(str(BIN), ensure_ascii=False))
        aliases = self.root / "aliases.nu"
        aliases.write_text(alias_source, encoding="utf-8")
        for command in ("l", "sl"):
            code = f"source {json.dumps(str(aliases), ensure_ascii=False)}; {command} " + " ".join(PLAIN)
            result = subprocess.run(["nu", "--no-config-file", "-c", code], cwd=self.root,
                                    capture_output=True, encoding="utf-8", timeout=15)
            names = [line for line in self.success(result).splitlines() if line.startswith("entry-")]
            self.assertEqual(names, [f"entry-{i:03}" for i in range(11, -1, -1)])
        profile = REPO / "Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
        environment = {**os.environ, "PATH": str(BIN) + os.pathsep + os.environ["PATH"]}
        for shell in ("pwsh", "powershell"):
            code = f". '{profile}'; l " + " ".join(PLAIN)
            result = subprocess.run([shell, "-NoProfile", "-Command", code], cwd=self.root, env=environment,
                                    capture_output=True, encoding="utf-8", timeout=20)
            names = [line for line in self.success(result).splitlines() if line.startswith("entry-")]
            self.assertEqual(names, [f"entry-{i:03}" for i in range(11, -1, -1)])


if __name__ == "__main__":
    unittest.main()
