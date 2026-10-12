#!/usr/bin/env python3

"""Move the active Herdr workspace one position up or down."""

import os
import sys

from herdr_api import HerdrError, request


def fail(message: str) -> None:
    print(f"herdr-move-workspace: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"up", "down"}:
        fail("usage: herdr-move-workspace up|down")

    socket_path = os.environ.get("HERDR_SOCKET_PATH")
    workspace_id = os.environ.get("HERDR_ACTIVE_WORKSPACE_ID") or os.environ.get("HERDR_WORKSPACE_ID")
    if not socket_path:
        fail("HERDR_SOCKET_PATH is not set")
    if not workspace_id:
        fail("HERDR_ACTIVE_WORKSPACE_ID is not set")

    snapshot_result = request(
        socket_path, "session.snapshot", {}
    )
    workspaces = snapshot_result["snapshot"]["workspaces"]

    current_index = next(
        (
            index
            for index, workspace in enumerate(workspaces)
            if workspace["workspace_id"] == workspace_id
        ),
        None,
    )
    if current_index is None:
        fail(f"active workspace {workspace_id!r} was not found")

    if sys.argv[1] == "up":
        if current_index == 0:
            return
        insert_index = current_index - 1
    else:
        if current_index == len(workspaces) - 1:
            return
        insert_index = current_index + 2

    request(
        socket_path,
        "workspace.move",
        {"workspace_id": workspace_id, "insert_index": insert_index},
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, HerdrError) as error:
        fail(str(error))
