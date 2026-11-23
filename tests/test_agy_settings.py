#!/usr/bin/env python3
"""Tests for Antigravity CLI (agy) dotfiles, modify template, statusline, and ay wrapper."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")

sys.path.insert(0, str(ROOT / "dot_gemini/antigravity-cli"))
sys.path.insert(0, str(ROOT / "dot_local/bin"))

import ay as ay_mod  # noqa: E402
import statusline as statusline_mod  # noqa: E402

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class AgyPstackModelsTest(unittest.TestCase):
    RULE_FILE = ROOT / "dot_gemini/config/rules/pstack-models.md"

    EXPECTED_ROLES = {
        "feature, refactoring": "inherit-parent",
        "bug-fix": "inherit-parent",
        "perf-issue": "inherit-parent",
        "hillclimb": "inherit-parent",
        "judgment and prose": "inherit-parent",
        "arena runners": "gemini-4-neon-high, claude-opus-5-5-high",
        "arena cross-judge pool": "claude-opus-5-5-high, gemini-4-neon-high",
        "swarm workers": "gemini-4-hydrogen-high",
        "interrogate reviewers": "gemini-4-neon-high, claude-opus-5-5-high",
    }

    def test_frontmatter_and_roles(self) -> None:
        lines = self.RULE_FILE.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "---")
        end_idx = lines.index("---", 1)
        frontmatter = dict(
            (line.partition(":")[0].strip(), line.partition(":")[2].strip())
            for line in lines[1:end_idx]
            if line.strip()
        )
        self.assertEqual(frontmatter.get("trigger"), "always_on")
        self.assertTrue(frontmatter.get("description"))

        roles = {}
        for line in lines[end_idx + 1 :]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            role, sep, val = stripped.partition(":")
            self.assertTrue(sep)
            roles[role.strip()] = val.strip()
        self.assertEqual(roles, self.EXPECTED_ROLES)


@unittest.skipUnless(CHEZMOI, "chezmoi required")
class ChezmoiModifyAgySettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="chezmoi-agy-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.dest = self.root / "dest"
        self.source.mkdir()
        self.dest.mkdir()
        self.config = self.root / "chezmoi.json"
        self.config.write_text(
            json.dumps(
                {
                    "destDir": str(self.dest),
                    "persistentState": str(self.root / "state.boltdb"),
                    "cacheDir": str(self.root / "cache"),
                }
            ),
            encoding="utf-8",
        )
        for rel in (
            "dot_codex/AGENTS.md",
            "dot_gemini/AGENTS.md.tmpl",
            "dot_gemini/config/skills.json.tmpl",
            "dot_gemini/antigravity-cli/modify_private_settings.json",
        ):
            dst = self.source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)

        self.base = [
            CHEZMOI,
            "--source",
            str(self.source),
            "--config",
            str(self.config),
            "--use-builtin-diff",
            "--no-pager",
        ]
        self.target = self.dest / ".gemini/antigravity-cli/settings.json"

    def run_chezmoi(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*self.base, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_fresh_install_writes_shared_settings(self) -> None:
        res = self.run_chezmoi("apply")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(data["altScreenMode"], "always")
        self.assertEqual(data["effort"], "high")
        self.assertEqual(data["model"], "Orchestrator (Neon)")
        self.assertEqual(data["toolPermission"], "always-proceed")
        self.assertEqual(data["statusLine"]["type"], "command")
        self.assertTrue(data["statusLine"]["command"].endswith(r"\.gemini\antigravity-cli\statusline.cmd"))
        self.assertNotIn("trustedWorkspaces", data)
        diff = self.run_chezmoi("diff", "--", str(self.target))
        self.assertEqual(diff.returncode, 0, diff.stderr)
        self.assertEqual(diff.stdout, "")

    def test_merges_shared_settings_while_preserving_local_keys(self) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.target.write_text(
            json.dumps(
                {
                    "trustedWorkspaces": [r"C:\Users\dhkim"],
                    "gcp": {"project": "demo"},
                    "effort": "low",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        res = self.run_chezmoi("apply", "--", str(self.target))
        self.assertEqual(res.returncode, 0, res.stderr)
        merged = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(merged["trustedWorkspaces"], [r"C:\Users\dhkim"])
        self.assertEqual(merged["gcp"], {"project": "demo"})
        self.assertEqual(merged["effort"], "high")
        self.assertEqual(merged["model"], "Orchestrator (Neon)")
        diff = self.run_chezmoi("diff", "--", str(self.target))
        self.assertEqual(diff.stdout, "")

    def test_invalid_or_non_object_json_fails_safely(self) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        for bad in ("{broken json", "[]", '"scalar"'):
            with self.subTest(bad=bad):
                self.target.write_text(bad, encoding="utf-8")
                res = self.run_chezmoi("diff", "--", str(self.target))
                self.assertNotEqual(res.returncode, 0)

    def test_agents_and_skills_templates_render(self) -> None:
        agents_target = self.dest / ".gemini/AGENTS.md"
        skills_target = self.dest / ".gemini/config/skills.json"
        res_agents = self.run_chezmoi("cat", "--", str(agents_target))
        self.assertEqual(res_agents.returncode, 0, res_agents.stderr)
        self.assertEqual(res_agents.stdout, (ROOT / "dot_codex/AGENTS.md").read_text(encoding="utf-8"))

        res_skills = self.run_chezmoi("cat", "--", str(skills_target))
        self.assertEqual(res_skills.returncode, 0, res_skills.stderr)
        skills = json.loads(res_skills.stdout)
        self.assertEqual(len(skills["entries"]), 1)
        self.assertTrue(skills["entries"][0]["path"].endswith(r"\.agents\skills"))


class AgyStatuslineTest(unittest.TestCase):
    def test_renders_model_context_quota_and_activity(self) -> None:
        payload = {
            "workspace": {"current_dir": r"C:\Users\example\gh\demo"},
            "model": {"display_name": "Gemini 4 Neon", "effort": "high"},
            "cycle_mode": "auto",
            "context_window": {
                "context_window_size": 1_000_000,
                "used_percentage": 25.4,
            },
            "quota": {
                "five_hour": {"remaining_fraction": 0.08, "reset_in_seconds": 3900},
                "weekly": {"remaining_fraction": 0.72, "reset_in_seconds": 90000},
                "ignored": {"disabled": True, "remaining_fraction": 0.0},
            },
            "subagents": [{"status": "running"}, {"status": "completed"}],
            "task_count": 2,
        }
        with (
            mock.patch.dict(os.environ, {"USERPROFILE": r"C:\Users\example"}, clear=False),
            mock.patch.object(statusline_mod, "run_git", return_value="feat/test"),
            mock.patch.object(statusline_mod, "lookup_pr_number", return_value="42"),
        ):
            rendered = strip_ansi(statusline_mod.render_statusline(payload, r"C:\fallback"))
        self.assertIn("Gemini 4 Neon (high) [auto]", rendered)
        self.assertIn(r"~\gh\demo (feat/test #42)", rendered)
        self.assertIn("ctx ███░░░░░░░ 25% 254k/1.0M", rendered)
        self.assertIn("5h 8% ·1h5m", rendered)
        self.assertIn("7d 72% ·1d1h", rendered)
        self.assertIn("Low quota (<10%)", rendered)
        self.assertIn("1ag 2bg", rendered)

    def test_invalid_payload_falls_back_to_dir_and_branch(self) -> None:
        with (
            mock.patch.dict(os.environ, {"USERPROFILE": r"C:\Users\example"}, clear=False),
            mock.patch.object(statusline_mod, "run_git", return_value="main"),
            mock.patch.object(statusline_mod, "lookup_pr_number", return_value=""),
        ):
            rendered = statusline_mod.render_statusline(None, r"C:\Users\example")
        self.assertEqual(rendered, "~ (main)")


class AyWrapperTest(unittest.TestCase):
    def test_help_and_version_and_passthrough(self) -> None:
        with mock.patch("sys.stdout") as fake_out:
            rc = ay_mod.main(["--help"])
        self.assertEqual(rc, 0)
        written = "".join(call.args[0] for call in fake_out.write.call_args_list)
        self.assertIn("agy --dangerously-skip-permissions", written)

        with (
            mock.patch.object(ay_mod, "find_agy", return_value=r"C:\bin\agy.exe"),
            mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "1.5.15\n", "")),
            mock.patch("builtins.print") as fake_print,
        ):
            self.assertEqual(ay_mod.main(["--version"]), 0)
            fake_print.assert_called_once_with(
                "ay: exec wrapper for agy --dangerously-skip-permissions (agy 1.5.15)"
            )

        with (
            mock.patch.object(ay_mod, "find_agy", return_value=r"C:\bin\agy.exe"),
            mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 7)) as run_mock,
        ):
            self.assertEqual(ay_mod.main(["--", "--help"]), 7)
            run_mock.assert_called_once_with(
                [r"C:\bin\agy.exe", "--dangerously-skip-permissions", "--help"],
                check=False,
            )

        with (
            mock.patch.object(ay_mod, "find_agy", return_value=r"C:\bin\agy.exe"),
            mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run_mock,
        ):
            self.assertEqual(ay_mod.main(["models", "--help"]), 0)
            run_mock.assert_called_once_with(
                [r"C:\bin\agy.exe", "--dangerously-skip-permissions", "models", "--help"],
                check=False,
            )


if __name__ == "__main__":
    unittest.main()
