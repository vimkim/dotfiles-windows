#!/usr/bin/env python3
"""Antigravity CLI (agy) status line for native Windows.

Reads agy's session JSON payload on stdin and renders:
model (+ effort/mode), cwd + git branch (+ cached GitHub PR number),
context window usage/size, quota remaining + reset countdown, and active
subagent/background task counts when nonzero.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

PR_CACHE_TTL_SECONDS = 600
GIT_TIMEOUT_SECONDS = 0.3
GH_TIMEOUT_SECONDS = 10.0

R = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
GRN = "\033[32m"
YEL = "\033[33m"
RED = "\033[31m"
CYA = "\033[36m"
SEP = f"{DIM}│{R}"

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def clamp_pct(value: int) -> int:
    return max(0, min(100, value))


def pct_color(percent: int) -> str:
    if percent < 50:
        return GRN
    if percent < 80:
        return YEL
    return RED


def human(count: int) -> str:
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count // 1_000}k"
    return str(count)


def dur_short(seconds: int) -> str:
    if seconds <= 0:
        return "now"
    if seconds >= 86400:
        days, rem = divmod(seconds, 86400)
        hours = rem // 3600
        return f"{days}d{hours}h" if hours > 0 else f"{days}d"
    if seconds >= 3600:
        hours, rem = divmod(seconds, 3600)
        minutes = rem // 60
        return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"
    minutes = max(1, seconds // 60)
    return f"{minutes}m"


def short_bucket(name: str) -> str:
    text = re.sub(r"-weekly$", "-7d", name)
    text = text.replace("weekly", "7d")
    text = re.sub(r"five[-_]?hour", "5h", text)
    text = re.sub(r"5[-_]?hour", "5h", text)
    return text


def shorten_home(path_str: str) -> str:
    home = os.environ.get("USERPROFILE") or str(Path.home())
    if not home:
        return path_str
    norm_path = os.path.normcase(os.path.normpath(path_str))
    norm_home = os.path.normcase(os.path.normpath(home))
    if norm_path == norm_home:
        return "~"
    prefix = norm_home.rstrip("\\/") + os.sep
    if norm_path.startswith(prefix):
        rel = os.path.normpath(path_str)[len(os.path.normpath(home).rstrip("\\/")):]
        return "~" + rel
    return path_str


def run_git(cwd: str, *args: str) -> str:
    git_bin = shutil.which("git")
    if not git_bin or not os.path.isdir(cwd):
        return ""
    try:
        res = subprocess.run(
            [git_bin, "-C", cwd, "--no-optional-locks", *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
            creationflags=NO_WINDOW,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return res.stdout.strip() if res.returncode == 0 else ""


def cache_root() -> Path:
    base = (
        os.environ.get("XDG_CACHE_HOME")
        or os.environ.get("LOCALAPPDATA")
        or str(Path.home() / "AppData" / "Local")
    )
    return Path(base) / "agy-statusline"


def pr_cache_file(repo_top: str, branch: str) -> Path:
    digest = hashlib.sha256(f"{repo_top}|{branch}".encode("utf-8")).hexdigest()[:16]
    return cache_root() / f"pr-{digest}"


def refresh_pr_cache(repo_top: str, branch: str, cache_path: Path) -> None:
    gh_bin = shutil.which("gh")
    pr = ""
    if gh_bin and os.path.isdir(repo_top):
        try:
            res = subprocess.run(
                [gh_bin, "pr", "view", branch, "--json", "number", "-q", ".number"],
                cwd=repo_top,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=GH_TIMEOUT_SECONDS,
                creationflags=NO_WINDOW,
                check=False,
            )
            if res.returncode == 0:
                pr = res.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pr = ""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(f"{int(time.time())} {pr}\n", encoding="utf-8")
    except OSError:
        pass


def lookup_pr_number(cwd: str, git_branch: str) -> str:
    if not git_branch or git_branch.startswith("detached@"):
        return ""
    if not shutil.which("gh"):
        return ""
    repo_top = run_git(cwd, "rev-parse", "--show-toplevel")
    if not repo_top:
        return ""

    cache_path = pr_cache_file(repo_top, git_branch)
    now = int(time.time())
    cached_at = 0
    cached_pr = ""
    if cache_path.is_file():
        try:
            parts = cache_path.read_text(encoding="utf-8").strip().split(" ", 1)
            if parts and parts[0].isdigit():
                cached_at = int(parts[0])
            if len(parts) > 1:
                cached_pr = parts[1].strip()
        except OSError:
            pass

    if now - cached_at >= PR_CACHE_TTL_SECONDS:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(f"{now} {cached_pr}\n", encoding="utf-8")
            subprocess.Popen(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(Path(__file__).resolve()),
                    "--refresh-pr",
                    repo_top,
                    git_branch,
                    str(cache_path),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW | DETACHED_PROCESS,
                close_fds=True,
            )
        except OSError:
            pass

    return cached_pr


def render_statusline(payload: dict | None, fallback_cwd: str) -> str:
    data = payload if isinstance(payload, dict) else {}
    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    cwd = workspace.get("current_dir") or data.get("cwd") or fallback_cwd
    if not isinstance(cwd, str) or not cwd:
        cwd = fallback_cwd

    dir_display = shorten_home(cwd)
    git_branch = run_git(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not git_branch:
        short_sha = run_git(cwd, "rev-parse", "--short", "HEAD")
        if short_sha:
            git_branch = f"detached@{short_sha}"
    pr_number = lookup_pr_number(cwd, git_branch)

    if payload is None:
        fallback = dir_display
        if git_branch:
            suffix = f"{git_branch} #{pr_number}" if pr_number else git_branch
            fallback += f" ({suffix})"
        return fallback

    model_obj = data.get("model") if isinstance(data.get("model"), dict) else {}
    model_name = model_obj.get("display_name") or model_obj.get("id") or "?"
    model_name = str(model_name)
    effort = model_obj.get("effort") or ""
    effort = str(effort) if isinstance(effort, str) else ""
    mode = data.get("cycle_mode") or ""
    mode = str(mode) if isinstance(mode, str) else ""

    model_disp = model_name
    if effort and effort.lower() not in model_name.lower():
        model_disp += f" ({effort})"

    out = f"{BOLD}{model_disp}{R}"
    if mode == "plan":
        out += f" {YEL}[plan]{R}"
    elif mode == "auto":
        out += f" {GRN}[auto]{R}"
    elif mode == "accept-edits":
        out += f" {CYA}[edits]{R}"
    elif mode:
        out += f" {DIM}[{mode}]{R}"

    dir_seg = f"{CYA}{dir_display}{R}"
    branch_disp = f"{git_branch} #{pr_number}" if (git_branch and pr_number) else git_branch
    if branch_disp:
        dir_seg += f" {DIM}({branch_disp}){R}"
    out += f" {SEP} {dir_seg}"

    ctx = data.get("context_window") if isinstance(data.get("context_window"), dict) else {}
    ctx_size_raw = ctx.get("context_window_size")
    ctx_size = int(ctx_size_raw) if is_number(ctx_size_raw) and ctx_size_raw > 0 else None
    used_pct_raw = ctx.get("used_percentage")
    ctx_pct = clamp_pct(int(math.floor(used_pct_raw))) if is_number(used_pct_raw) else None
    if ctx_size is not None and is_number(used_pct_raw):
        used_tok: int | None = int(math.floor(ctx_size * used_pct_raw / 100.0))
    elif is_number(ctx.get("total_input_tokens")):
        used_tok = int(math.floor(ctx["total_input_tokens"]))
    else:
        used_tok = None

    if ctx_pct is not None:
        color = pct_color(ctx_pct)
        filled = min(10, (ctx_pct + 5) // 10)
        bar = "█" * filled + "░" * (10 - filled)
        seg = f"{color}ctx {bar} {ctx_pct}%{R}"
        if used_tok is not None and ctx_size is not None:
            seg += f" {DIM}{human(used_tok)}/{human(ctx_size)}{R}"
        out += f" {SEP} {seg}"
    elif ctx_size is not None:
        out += f" {SEP} {GRN}ctx ░░░░░░░░░░ 0%{R} {DIM}0/{human(ctx_size)}{R}"

    quota_raw = data.get("quota") if isinstance(data.get("quota"), dict) else {}
    buckets = []
    for key, val in quota_raw.items():
        if not isinstance(val, dict) or val.get("disabled"):
            continue
        reset_raw = val.get("reset_in_seconds")
        sort_reset = reset_raw if is_number(reset_raw) else 999_999_999
        reset_sec = int(math.floor(reset_raw)) if is_number(reset_raw) and reset_raw > 0 else None
        if is_number(val.get("remaining_fraction")):
            pct_rem = clamp_pct(int(round(val["remaining_fraction"] * 100)))
            buckets.append((sort_reset, key, short_bucket(key), "frac", pct_rem, reset_sec))
        elif is_number(val.get("remaining_amount")):
            amt = int(math.floor(val["remaining_amount"]))
            buckets.append((sort_reset, key, short_bucket(key), "amt", amt, reset_sec))
    buckets.sort(key=lambda item: (item[0], item[1]))

    low_quota = False
    for _, _, q_label, q_kind, q_val, q_reset in buckets:
        if not q_label:
            continue
        if q_kind == "frac":
            used_pct = 100 - q_val
            color = pct_color(used_pct)
            seg = f"{color}{q_label} {q_val}%{R}"
            if q_val < 10:
                low_quota = True
        else:
            seg = f"{CYA}{q_label} {q_val}{R}"
        if q_reset is not None:
            seg += f" {DIM}·{dur_short(q_reset)}{R}"
        out += f" {SEP} {seg}"

    if low_quota:
        out += f" {SEP} {RED}Low quota (<10%){R}"

    subagents = data.get("subagents") if isinstance(data.get("subagents"), list) else []
    run_ag = sum(1 for item in subagents if isinstance(item, dict) and item.get("status") == "running")
    task_raw = data.get("task_count")
    task_count = int(math.floor(task_raw)) if is_number(task_raw) and task_raw > 0 else 0
    active = []
    if run_ag > 0:
        active.append(f"{run_ag}ag")
    if task_count > 0:
        active.append(f"{task_count}bg")
    if active:
        out += f" {SEP} {DIM}{' '.join(active)}{R}"

    return out


def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "--refresh-pr":
        refresh_pr_cache(sys.argv[2], sys.argv[3], Path(sys.argv[4]))
        return 0

    raw = sys.stdin.read()
    payload: dict | None = None
    if raw.strip():
        try:
            decoded = json.loads(raw.lstrip("\ufeff"))
            if isinstance(decoded, dict):
                payload = decoded
        except json.JSONDecodeError:
            payload = None

    sys.stdout.write(render_statusline(payload, os.getcwd()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
