"""Native Windows checks with real fd, fzf, eza, Just, Git, Nu, and PowerShell."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
BIN = REPO / "dot_local/bin"
NU = shutil.which("nu")
PLAIN = ["--no-user", "--no-permissions", "--no-filesize", "--no-time", "--color=never", "--icons=never"]


class WindowsHelperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="windows helpers 한글 ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.mock_bin = self.root / "bin"
        self.mock_bin.mkdir()
        packages = Path(os.environ["LOCALAPPDATA"]) / "Microsoft/WinGet/Packages"
        native = [str(path) for pattern in ["Casey.Just_*", "ajeetdsouza.zoxide_*"] for path in packages.glob(pattern)]
        self.env = {
            **os.environ, "PATH": os.pathsep.join([str(self.mock_bin), str(BIN), *native, os.environ["PATH"]]),
            "FZF_DEFAULT_OPTS": "", "_ZO_DATA_DIR": str(self.root / "zoxide"),
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        }
        self.env.pop("FZF_DEFAULT_OPTS_FILE", None)
        self.env.pop("GIT_DIFFNAV_PAGER", None)
        self.env.pop("FIND_PROJECT_ROOTS", None)

    def run_command(self, args, *, cwd=None, extra=None, stdin=None):
        environment = {**self.env, **(extra or {})}
        # Windows CreateProcess searches the parent's PATH before applying the
        # child's environment. Resolve test executables against the test PATH.
        args = [shutil.which(str(args[0]), path=environment["PATH"]) or args[0], *args[1:]]
        return subprocess.run(args, cwd=cwd or self.data, env=environment, input=stdin,
                              capture_output=True, encoding="utf-8", timeout=15)

    def python(self, name, *args, **kwargs):
        return self.run_command([sys.executable, "-X", "utf8", str(BIN / name), *map(str, args)], **kwargs)

    def nu(self, name, *args, **kwargs):
        return self.run_command([NU, "--no-config-file", str(BIN / name), *map(str, args)], **kwargs)

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def file(self, name, size=1, modified=100):
        path = self.data / name
        path.write_text("x" * size, encoding="utf-8")
        os.utime(path, (modified, modified))
        return path

    def directory(self, name, modified):
        path = self.data / name
        path.mkdir()
        os.utime(path, (modified, modified))
        return path

    def aliases(self, expression, *, extra=None):
        source = (REPO / "AppData/Roaming/nushell/alias.nu").read_text(encoding="utf-8")
        source = source.replace('const helper_bin = ($nu.home-dir | path join ".local" "bin")',
                                "const helper_bin = " + json.dumps(str(BIN), ensure_ascii=False))
        alias_file = self.root / "alias.nu"
        alias_file.write_text(source, encoding="utf-8")
        zoxide_init = self.root / "zoxide.nu"
        result = self.run_command(["zoxide", "init", "nushell"])
        zoxide_init.write_text(self.success(result), encoding="utf-8")
        code = f"source {json.dumps(str(zoxide_init), ensure_ascii=False)}; source {json.dumps(str(alias_file), ensure_ascii=False)}; {expression}"
        return self.run_command([NU, "--no-config-file", "-c", code], extra=extra)

    def git_repository(self):
        for args in [["init", "-q"], ["config", "user.name", "Helper Test"], ["config", "user.email", "test@example.invalid"]]:
            self.success(self.run_command(["git", *args]))
        self.file("tracked.txt", modified=100)
        self.success(self.run_command(["git", "add", "."]))
        self.success(self.run_command(["git", "commit", "-qm", "first"]))
        self.file("tracked.txt", size=2, modified=200)
        self.success(self.run_command(["git", "add", "."]))
        self.success(self.run_command(["git", "commit", "-qm", "second"]))

    def justfile(self):
        path = self.data / "justfile"
        path.write_text('set shell := ["cmd.exe", "/d", "/c"]\n\n[default]\nbuild:\n    @echo BUILD_EXECUTED\n\ntest-it:\n    @echo TEST_EXECUTED\n', encoding="utf-8")
        return path

    def test_directory_parent_first_then_modification_time(self):
        older = self.directory("older", 100)
        newer = self.directory("newer", 300)
        hidden = self.directory(".hidden", 200)
        paths = json.loads(self.success(self.python("dir_picker.py", "--list", "--json")))
        self.assertEqual(paths, [str(self.root), str(newer), str(hidden), str(older)])

    def test_directory_picker_searches_name_and_preserves_spaces_unicode(self):
        selected = self.directory("Target space & 한글", 100)
        result = self.python("dir_picker.py", "--json", extra={"FZF_DEFAULT_OPTS": "--filter=Target"})
        self.assertEqual(json.loads(self.success(result)), str(selected))
        result = self.python("dir_picker.py", "--json", extra={"FZF_DEFAULT_OPTS": "--filter=helpers"})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_directory_cancel_changes_no_cwd(self):
        self.directory("target", 100)
        result = self.aliases('c; print $env.PWD', extra={"FZF_DEFAULT_OPTS": "--filter=ABSENT"})
        self.assertEqual(self.success(result), str(self.data))

    def test_c_cv_and_direct_path_navigation(self):
        target = self.directory("target 한글", 100)
        for command in ["c", "cv", "cl"]:
            with self.subTest(command=command):
                result = self.aliases(f'{command} {json.dumps(str(target), ensure_ascii=False)}; print $env.PWD')
                self.assertEqual(self.success(result).splitlines()[-1], str(target))

    def test_file_recency_depth_and_control_flags(self):
        old = self.file("old.txt", modified=100)
        new = self.file("new space & 한글.txt", modified=300)
        hidden = self.file(".hidden", modified=200)
        nested = self.data / "nested"
        nested.mkdir()
        (nested / "deep.txt").touch()
        (self.data / ".git").mkdir()
        (self.data / ".git/secret").touch()
        paths = json.loads(self.success(self.python("file_picker.py", "--list", "--json", "--max-depth=1")))
        self.assertEqual(paths, [str(new), str(hidden), str(old)])
        paths = json.loads(self.success(self.python("file_picker.py", "--list", "--json", "--no-hidden")))
        self.assertIn(str(nested / "deep.txt"), paths)
        self.assertNotIn(str(hidden), paths)
        self.assertFalse(any("secret" in path for path in paths))

    def test_file_selection_and_cancel(self):
        target = self.file("Target space & 한글.txt")
        result = self.python("file_picker.py", "--json", extra={"FZF_DEFAULT_OPTS": "--filter=Target"})
        self.assertEqual(json.loads(self.success(result)), str(target))
        result = self.python("file_picker.py", "--json", extra={"FZF_DEFAULT_OPTS": "--filter=ABSENT"})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_file_ignore_override(self):
        self.file("ignored.txt")
        (self.data / ".ignore").write_text("ignored.txt\n", encoding="utf-8")
        normal = json.loads(self.success(self.python("file_picker.py", "--list", "--json")))
        override = json.loads(self.success(self.python("file_picker.py", "--list", "--json", "--no-ignore")))
        self.assertNotIn(str(self.data / "ignored.txt"), normal)
        self.assertIn(str(self.data / "ignored.txt"), override)

    def test_cf_changes_to_selected_files_parent(self):
        nested = self.data / "nested"
        nested.mkdir()
        (nested / "UniqueTarget.txt").touch()
        result = self.aliases('cf; print $env.PWD', extra={"FZF_DEFAULT_OPTS": "--filter=UniqueTarget"})
        self.assertEqual(self.success(result).splitlines()[-1], str(nested))

    def test_preview_fallback_uses_index_not_shell_file_path(self):
        path = self.file("content & 한글.txt")
        path.write_text("Readable content\n", encoding="utf-8")
        index = self.root / "preview.json"
        index.write_text(json.dumps([str(path)]), encoding="utf-8")
        self.assertIn("Readable content", self.success(self.python("file_picker.py", "--preview", index, "0")))

    def test_listing_sort_defaults_reverse_and_extension(self):
        self.file("a.txt", size=1, modified=300)
        self.file("z.py", size=100, modified=100)
        self.file(".hidden", size=10, modified=200)
        expected = {"ls-by-name": [".hidden", "a.txt", "z.py"], "ls-by-size": ["z.py", ".hidden", "a.txt"],
                    "ls-by-time": ["a.txt", ".hidden", "z.py"]}
        for name, names in expected.items():
            with self.subTest(name=name):
                normal = self.success(self.python("listing.py", name, *PLAIN)).splitlines()
                reverse = self.success(self.python("listing.py", name, *PLAIN, "-lr")).splitlines()
                self.assertEqual(normal, names)
                self.assertEqual(reverse, names[::-1])
        self.file("b.py")
        names = self.success(self.python("listing.py", "ls-by-extension", *PLAIN)).splitlines()
        self.assertLess(names.index("b.py"), names.index("z.py"))

    def test_listing_filters_tree_depth_and_no_truncation(self):
        nested = self.data / "one/two"
        nested.mkdir(parents=True)
        (nested / "deep").touch()
        self.file("file.txt")
        self.assertEqual(self.success(self.python("listing.py", "ls-dirs", *PLAIN)), "one")
        self.assertEqual(self.success(self.python("listing.py", "ls-files", *PLAIN)), "file.txt")
        self.assertNotIn("deep", self.success(self.python("listing.py", "ls-tree", *PLAIN)))
        self.assertIn("deep", self.success(self.python("listing.py", "ls-tree", *PLAIN, "--level=3")))
        for index in range(450):
            self.file(f"entry-{index:03}.txt")
        self.assertEqual(len(self.success(self.python("listing.py", "ls-by-name", *PLAIN)).splitlines()), 452)

    def test_listing_literal_option_filename(self):
        self.file("--no-pager")
        self.assertEqual(self.success(self.python("listing.py", "ls-by-name", *PLAIN, "--", "--no-pager")), "--no-pager")

    def test_just_selection_and_cancel_do_not_execute_recipe(self):
        file = self.justfile()
        selected = self.nu("just-pick-and-print.nu", "-f", file, "-d", self.data, extra={"FZF_DEFAULT_OPTS": "--filter=test-it"})
        self.assertEqual(self.success(selected), "test-it")
        cancelled = self.nu("just-pick-and-print.nu", "-f", file, "-d", self.data, extra={"FZF_DEFAULT_OPTS": "--filter=ABSENT"})
        self.assertEqual(self.success(cancelled), "")

    def test_n_jj_and_ni_print_editable_actual_just_commands(self):
        self.justfile()
        for command in ["n", "jj", "ji"]:
            self.assertEqual(self.success(self.aliases(command, extra={"FZF_DEFAULT_OPTS": "--filter=test-it"})), 'just "test-it"')
        nested = self.data / ".just"
        nested.mkdir()
        shutil.copyfile(self.data / "justfile", nested / "justfile")
        self.assertEqual(self.success(self.aliases("ni", extra={"FZF_DEFAULT_OPTS": "--filter=test-it"})),
                         'just -f "./.just/justfile" -d . "test-it"')
        self.assertIn("TEST_EXECUTED", self.success(self.aliases("n test-it")))

    def test_project_roots_depth_names_and_cancel(self):
        target = self.directory("ProjectTarget", 100)
        (target / "deep").mkdir()
        extra = {"FIND_PROJECT_ROOTS": str(self.data), "FZF_DEFAULT_OPTS": "--filter=ProjectTarget"}
        selected = self.nu("find-project.nu", "--json", "--depth=1", extra=extra)
        self.assertEqual(json.loads(self.success(selected)), str(target))
        extra["FZF_DEFAULT_OPTS"] = "--filter=deep"
        self.assertEqual(self.success(self.nu("find-project.nu", "--json", "--depth=1", extra=extra)), "")
        extra["FZF_DEFAULT_OPTS"] = "--filter=data"
        self.assertEqual(self.success(self.nu("find-project.nu", "--json", extra=extra)), "")

    def test_invalid_project_roots_and_depth(self):
        for args, extra in [(["--depth=0"], {}), ([], {"FIND_PROJECT_ROOTS": "C:relative"}),
                            ([], {"FIND_PROJECT_ROOTS": str(self.data) + ";"})]:
            self.assertNotEqual(self.nu("find-project.nu", *args, extra=extra).returncode, 0)

    def test_git_diffview_ranges_working_and_cancel(self):
        self.git_repository()
        base = self.success(self.run_command(["git", "rev-parse", "HEAD~1"]))
        target = self.success(self.run_command(["git", "rev-parse", "HEAD"]))
        command = self.success(self.nu("git-diffview.nu", "-p", "-3", "HEAD~1", "HEAD"))
        self.assertEqual(command, f'nvim -c "DiffviewOpen {base}...{target}"')
        self.assertEqual(self.success(self.nu("git-diffview.nu", "-p", "-w")), 'nvim -c "DiffviewOpen"')
        self.assertEqual(self.success(self.nu("git-diffview.nu", "-p", extra={"FZF_DEFAULT_OPTS": "--filter=ABSENT"})), "")

    def test_git_diffnav_graph_selection_and_printed_command(self):
        self.git_repository()
        command = self.success(self.nu("git-diffnav.nu", "-p", "HEAD~1", "HEAD"))
        self.assertEqual(command, 'git diff "HEAD~1" "HEAD" | ^"less" -FRX')
        selected = self.nu("git-diffnav.nu", "-p", extra={"FZF_DEFAULT_OPTS": "--filter=second"})
        self.assertIn("git diff", self.success(selected))
        self.assertNotEqual(self.nu("git-diffnav.nu", "-p", "ABSENT", "HEAD").returncode, 0)

    def test_rerun_help_and_missing_command(self):
        self.assertIn("command", self.success(self.nu("rerun-on-enter.nu", "--help")))
        self.assertNotEqual(self.nu("rerun-on-enter.nu").returncode, 0)

    def test_cz_uses_isolated_zoxide_database(self):
        target = self.directory("ZoxideTarget", 100)
        self.success(self.run_command(["zoxide", "add", str(target)]))
        result = self.aliases('cz ZoxideTarget; print $env.PWD', extra={"FZF_DEFAULT_OPTS": "--filter=ZoxideTarget"})
        self.assertEqual(self.success(result).splitlines()[-1], str(target))

    def test_powershell_c_cv_and_picker_cancel(self):
        target = self.directory("PowerShellTarget", 100)
        profile = REPO / "Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
        for command in ["c", "cv", "cl"]:
            code = f". '{profile}'; {command} '{target}'; (Get-Location).Path"
            self.assertEqual(self.success(self.run_command(["pwsh", "-NoProfile", "-Command", code])).splitlines()[-1], str(target))
        code = f". '{profile}'; c; (Get-Location).Path"
        result = self.run_command(["pwsh", "-NoProfile", "-Command", code], extra={"FZF_DEFAULT_OPTS": "--filter=ABSENT"})
        self.assertEqual(self.success(result).splitlines()[-1], str(self.data))

    def test_fresh_nushell_starts_without_optional_tools(self):
        task_home = self.root / "fresh home"
        config = task_home / "AppData/Roaming/nushell"
        config.mkdir(parents=True)
        for name in ["env.nu", "config.nu", "alias.nu", "eza.nu"]:
            shutil.copyfile(REPO / "AppData/Roaming/nushell" / name, config / name)
        extra = {"USERPROFILE": str(task_home), "HOME": str(task_home), "APPDATA": str(task_home / "AppData/Roaming"),
                 "LOCALAPPDATA": str(task_home / "AppData/Local"), "HERDR_ENV": "",
                 "PATH": str(Path(NU).parent) + os.pathsep + str(Path(os.environ["WINDIR"]) / "System32")}
        result = self.run_command([NU, "--env-config", str(config / "env.nu"), "--config", str(config / "config.nu"),
                                   "-c", 'print "STARTUP_OK"'], extra=extra)
        self.assertEqual(self.success(result), "STARTUP_OK")
        self.assertEqual(result.stderr, "")
        self.assertEqual((config / "mise.nu").read_text(encoding="utf-8"), "")
        self.assertEqual((config / "zoxide.nu").read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
