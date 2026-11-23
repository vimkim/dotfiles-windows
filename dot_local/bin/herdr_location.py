#!/usr/bin/env python3

"""Print or copy the location of the invoking Herdr pane."""

import argparse
import base64
from dataclasses import dataclass
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import unicodedata

from herdr_api import HerdrError, request


class LocationError(Exception):
    pass


@dataclass(frozen=True)
class Location:
    workspace_name: str
    workspace_id: str
    tab_label: str
    tab_id: str
    pane_id: str

    def reference(self):
        return (
            f"{quoted(self.workspace_name)} ({self.workspace_id}), "
            f"tab {quoted(self.tab_label)} ({self.tab_id}), pane {self.pane_id}"
        )


def quoted(value):
    encoded = json.dumps(value, ensure_ascii=False)
    return "".join(
        json.dumps(char, ensure_ascii=True)[1:-1]
        if unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} else char
        for char in encoded
    )


def snapshot(socket_path):
    try:
        return request(
            socket_path,
            "session.snapshot",
            {},
            timeout=3,
            request_id="herdr-location",
        )["snapshot"]
    except (OSError, ValueError, KeyError, TypeError, HerdrError) as exc:
        raise LocationError(str(exc)) from exc


def locate(data, pane_id):
    def find(kind, field, value):
        entries = data[kind]
        if not isinstance(entries, list):
            raise LocationError(f"invalid {kind} in snapshot")
        matches = [entry for entry in entries if entry.get(field) == value]
        if len(matches) != 1:
            raise LocationError(f"{kind[:-1]} {quoted(value)} not found uniquely")
        return matches[0]

    pane = find("panes", "pane_id", pane_id)
    tab = find("tabs", "tab_id", pane["tab_id"])
    workspace = find("workspaces", "workspace_id", tab["workspace_id"])
    if pane["workspace_id"] != tab["workspace_id"]:
        raise LocationError("pane and tab belong to different workspaces")
    values = (
        workspace["label"],
        workspace["workspace_id"],
        tab["label"],
        tab["tab_id"],
        pane["pane_id"],
    )
    if not all(isinstance(value, str) and value for value in values):
        raise LocationError("location contains missing or invalid fields")
    if any(
        any(unicodedata.category(char).startswith("C") for char in value)
        for value in (values[1], values[3], values[4])
    ):
        raise LocationError("location contains invalid IDs")
    return Location(*values)


def fit(line, width):
    sizes = [
        0 if unicodedata.combining(char) else 2
        if unicodedata.east_asian_width(char) in "WF" else 1
        for char in line
    ]
    if sum(sizes) <= width:
        return line
    used = 0
    for index, columns in enumerate(sizes):
        if used + columns > width - 1:
            return line[:index] + "…"
        used += columns
    return line


def copy_text(value):
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    sys.stdout.write(f"\x1b]52;c;{encoded}\x07")
    sys.stdout.flush()
    clip_bin = shutil.which("clip.exe")
    if clip_bin and os.environ.get("HERDR_LOCATION_NO_CLIP") != "1":
        try:
            subprocess.run(
                [clip_bin],
                input=value.encode("utf-16-le"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass


def read_key():
    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        msvcrt.getwch()
        return ""
    return key


def popup(location=None, error=None, key_reader=read_key, copier=copy_text):
    if key_reader is read_key and (not sys.stdin.isatty() or not sys.stdout.isatty()):
        raise LocationError("popup requires a terminal")
    if error:
        print(f"herdr-location: {quoted(error)}\nPress q, Escape, or Enter to close.", flush=True)
    else:
        width = max(1, shutil.get_terminal_size((80, 24)).columns - 1)
        lines = [
            f"Workspace: {quoted(location.workspace_name)}",
            f"Workspace ID: {location.workspace_id}",
            f"Tab: {quoted(location.tab_label)}",
            f"Tab ID: {location.tab_id}",
            f"Pane: {location.pane_id}",
            "Enter/c: copy reference  p: pane  t: tab  w: workspace",
            "q/Esc: close",
        ]
        for line in lines:
            print(fit(line, width))
        sys.stdout.flush()
    while True:
        key = key_reader()
        if not key or key in ("q", "\x1b") or (error and key in ("\r", "\n")):
            return
        if not error:
            value = {
                "\r": location.reference(),
                "\n": location.reference(),
                "c": location.reference(),
                "p": location.pane_id,
                "t": location.tab_id,
                "w": location.workspace_id,
            }.get(key)
            if value is not None:
                copier(value)
                return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--popup", action="store_true", help="show location and copy options")
    args = parser.parse_args()
    try:
        socket_path = os.environ.get("HERDR_SOCKET_PATH")
        pane_id = os.environ.get("HERDR_ACTIVE_PANE_ID") or os.environ.get("HERDR_PANE_ID")
        if not socket_path:
            raise LocationError("HERDR_SOCKET_PATH is not set")
        if not pane_id:
            raise LocationError("HERDR_ACTIVE_PANE_ID and HERDR_PANE_ID are not set")
        location = locate(snapshot(socket_path), pane_id)
    except (LocationError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        message = str(exc) or "invalid snapshot"
        if args.popup:
            try:
                popup(error=message)
            except (LocationError, OSError) as terminal_error:
                print(f"herdr-location: {quoted(str(terminal_error))}", file=sys.stderr)
        else:
            print(f"herdr-location: {quoted(message)}", file=sys.stderr)
        return 1
    if args.popup:
        try:
            popup(location=location)
        except (LocationError, OSError) as exc:
            print(f"herdr-location: {quoted(str(exc))}", file=sys.stderr)
            return 1
    else:
        print(location.reference())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
