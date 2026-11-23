#!/usr/bin/env python3
"""Tests for Windows Herdr helpers: herdr_attention, herdr_location, herdr_label_agents."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

from tests.herdr_test_pipe import PipeListener

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / "dot_local/bin"
sys.path.insert(0, str(BIN_DIR))

import herdr_label_agents  # noqa: E402
import herdr_location  # noqa: E402


class MultiWorkspaceHerdrServer:
    def __init__(self, path: Path):
        self.path = path
        self.snapshot = {
            "workspaces": [
                {"workspace_id": "w1", "label": "work-1"},
                {"workspace_id": "w2", "label": "work-2"},
                {"workspace_id": "w3", "label": "work-3"},
            ],
            "tabs": [
                {"tab_id": "w1:t1", "workspace_id": "w1", "label": "main"},
                {"tab_id": "w2:t1", "workspace_id": "w2", "label": "busy-claude"},
                {"tab_id": "w3:t1", "workspace_id": "w3", "label": "ready"},
            ],
            "panes": [
                {"pane_id": "w1:p1", "workspace_id": "w1", "tab_id": "w1:t1"},
                {"pane_id": "w2:p1", "workspace_id": "w2", "tab_id": "w2:t1"},
                {"pane_id": "w3:p1", "workspace_id": "w3", "tab_id": "w3:t1"},
                {"pane_id": "w3:p2", "workspace_id": "w3", "tab_id": "w3:t1"},
            ],
            "agents": [
                {"workspace_id": "w1", "tab_id": "w1:t1", "pane_id": "w1:p1", "agent": "codex", "agent_status": "working"},
                {"workspace_id": "w2", "tab_id": "w2:t1", "pane_id": "w2:p1", "agent": "claude", "agent_status": "idle"},
                {"workspace_id": "w3", "tab_id": "w3:t1", "pane_id": "w3:p1", "agent": "codex", "agent_status": "idle"},
                {"workspace_id": "w3", "tab_id": "w3:t1", "pane_id": "w3:p2", "agent": "claude", "agent_status": "blocked"},
            ],
        }
        self.pane_reads = {
            "w2:p1": "────\n❯ \n────\n⏵⏵ accept edits · 2 background agents\n",
        }
        self.focused = []
        self.stop = threading.Event()
        self.listener = PipeListener(path)
        self.thread = threading.Thread(target=self.serve, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.stop.set()
        if self.thread.is_alive():
            self.listener.wake()
        self.thread.join(timeout=2)
        self.listener.close()

    def serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.listener.accept()
            except OSError:
                return
            if self.stop.is_set():
                conn.close()
                return
            with conn:
                line = conn.readline()
                if not line:
                    continue
                payload = json.loads(line)
                method = payload["method"]
                params = payload["params"]
                if method == "session.snapshot":
                    result = {"snapshot": copy.deepcopy(self.snapshot)}
                elif method == "agent.read":
                    tid = params["target"]
                    result = {"read": {"pane_id": tid, "text": self.pane_reads.get(tid, "")}}
                elif method == "agent.get":
                    tid = params["target"]
                    agent = next(a for a in self.snapshot["agents"] if a["pane_id"] == tid)
                    result = {"agent": copy.deepcopy(agent)}
                elif method == "agent.focus":
                    self.focused.append(params["target"])
                    result = {"ok": True}
                else:
                    result = {}
                conn.write(json.dumps({"id": payload["id"], "result": result}).encode() + b"\n")
                conn.flush()


class HerdrAttentionAndLocationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="herdr-helpers-")
        self.addCleanup(self.temp.cleanup)
        self.server = MultiWorkspaceHerdrServer(Path(self.temp.name) / "herdr.sock")
        self.server.__enter__()
        self.addCleanup(self.server.__exit__, None, None, None)

    def test_attention_skips_busy_claude_and_prefers_blocked_pane(self):
        env = {
            **os.environ,
            "HERDR_SOCKET_PATH": str(self.server.path),
            "HERDR_ACTIVE_WORKSPACE_ID": "w1",
        }
        res = subprocess.run(
            [sys.executable, "-X", "utf8", str(BIN_DIR / "herdr_attention.py"), "next", "--json"],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["data"]["selected"]["pane"]["pane_id"], "w3:p2")
        self.assertEqual(self.server.focused, ["w3:p2"])

    def test_attention_list_reports_claude_busy_reason(self):
        env = {**os.environ, "HERDR_SOCKET_PATH": str(self.server.path)}
        res = subprocess.run(
            [sys.executable, "-X", "utf8", str(BIN_DIR / "herdr_attention.py"), "list", "--json"],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        decisions = {
            d["pane"]["pane_id"]: d
            for d in json.loads(res.stdout)["data"]["decisions"]
        }
        self.assertFalse(decisions["w2:p1"]["eligible"])
        self.assertEqual(decisions["w2:p1"]["reason"], "claude_busy")
        self.assertTrue(decisions["w3:p2"]["eligible"])

    def test_location_cli_and_popup_copy(self):
        env = {
            **os.environ,
            "HERDR_SOCKET_PATH": str(self.server.path),
            "HERDR_ACTIVE_PANE_ID": "w3:p2",
        }
        res = subprocess.run(
            [sys.executable, "-X", "utf8", str(BIN_DIR / "herdr_location.py")],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), '"work-3" (w3), tab "ready" (w3:t1), pane w3:p2')

        loc = herdr_location.locate(self.server.snapshot, "w3:p2")
        copied = []
        herdr_location.popup(location=loc, key_reader=lambda: "p", copier=copied.append)
        self.assertEqual(copied, ["w3:p2"])

    def test_label_agents_labels_only_unnamed_panes(self):
        def fake_read(*args):
            if args == ("agent", "list"):
                return {
                    "agents": [
                        {"pane_id": "w1:p1", "name": "codex"},
                        {"pane_id": "w1:p2", "name": "claude"},
                        {"pane_id": "w1:p3", "name": "agy"},
                    ]
                }
            if args == ("pane", "get", "w1:p1"):
                return {"pane": {"label": ""}}
            if args == ("pane", "get", "w1:p2"):
                return {"pane": {"label": "custom"}}
            if args == ("pane", "get", "w1:p3"):
                return {"pane": {"label": "agy"}}
            raise AssertionError(args)

        with (
            mock.patch.dict(os.environ, {"HERDR_ENV": "1"}, clear=False),
            mock.patch.object(herdr_label_agents, "read", side_effect=fake_read),
            mock.patch("subprocess.run") as run_mock,
            mock.patch("builtins.print"),
        ):
            herdr_label_agents.main()
        run_mock.assert_called_once_with(
            ["herdr", "pane", "rename", "w1:p1", "codex"],
            check=True,
            stdout=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    unittest.main()
