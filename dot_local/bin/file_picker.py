"""Pick a file with fd/fzf, sorted by modification time, on native Windows."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from dir_picker import display_size, display_text


def file_choices(root, max_depth=None, hidden=True, no_ignore=False):
    fd = shutil.which("fd")
    if not fd:
        raise RuntimeError("fd is required")
    args = [fd, "--type", "f", "--type", "l", "--follow", "--absolute-path",
            "--exclude", ".git", "--exclude", ".jj", "--print0"]
    if max_depth is not None:
        args += ["--max-depth", str(max_depth)]
    if hidden:
        args.append("--hidden")
    if no_ignore:
        args.append("--no-ignore")
    result = subprocess.run([*args, ".", str(root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    choices = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = Path(os.fsdecode(raw))
        try:
            if path.is_file():
                choices.append((str(path), path.stat()))
        except OSError:
            continue
    return sorted(choices, key=lambda item: (-item[1].st_mtime_ns, item[0].casefold()))


def preview(index_file, index):
    path = Path(json.loads(Path(index_file).read_text(encoding="utf-8"))[int(index)])
    bat = shutil.which("bat")
    if bat:
        return subprocess.call([bat, "--color=always", "--style=numbers", "--line-range=:150", "--", str(path)])
    with path.open("rb") as stream:
        data = stream.read(32 * 1024)
    if b"\0" in data:
        print("Binary file")
    else:
        for line in data.decode("utf-8", errors="replace").splitlines()[:150]:
            print("".join(char for char in line if char.isprintable() or char == "\t"))
    return 0


def pick_file(choices, query=""):
    fzf = shutil.which("fzf")
    if not fzf:
        raise RuntimeError("fzf is required")
    if not choices:
        return 1, None
    rows = []
    for index, (path, stat) in enumerate(choices):
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        rows.append(f"{index}\t{display_size(stat.st_size):>8}  {modified}  {display_text(path)}")
    descriptor, index_file = tempfile.mkstemp(prefix="file-picker-", suffix=".json")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump([path for path, _stat in choices], stream)
        # Only a generated numeric index enters the shell; file paths stay in JSON.
        preview_command = subprocess.list2cmdline(
            [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--preview", index_file, "{1}"]
        )
        result = subprocess.run(
            [fzf, "--read0", "--print0", "--no-multi", "--no-print-query", "--no-expect",
             "--ansi", "--delimiter=\t", "--with-nth=2..", "--accept-nth=1", "--no-sort",
             "--height=60%", "--reverse", "--query=" + query,
             "--with-shell=" + os.environ.get("COMSPEC", "cmd.exe") + " /d /c",
             "--preview=" + preview_command, "--preview-window=right:60%,wrap"],
            input=b"".join(row.encode("utf-8") + b"\0" for row in rows), stdout=subprocess.PIPE,
        )
        if result.returncode:
            return result.returncode, None
        index = result.stdout.removesuffix(b"\0").decode("utf-8")
        if not index.isdecimal() or int(index) >= len(choices):
            raise RuntimeError("fzf returned an invalid selection")
        return 0, choices[int(index)][0]
    finally:
        Path(index_file).unlink(missing_ok=True)


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--preview":
        return preview(sys.argv[2], sys.argv[3])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--query", default="")
    parser.add_argument("--max-depth", type=int)
    parser.add_argument("--no-ignore", action="store_true")
    parser.add_argument("--no-hidden", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true", help="list ordered paths without opening fzf")
    args = parser.parse_args()
    if args.max_depth is not None and args.max_depth < 1:
        parser.error("max-depth must be positive")
    root = Path(os.path.abspath(os.path.expanduser(args.directory)))
    choices = file_choices(root, args.max_depth, not args.no_hidden, args.no_ignore)
    if args.list:
        paths = [path for path, _stat in choices]
        print(json.dumps(paths) if args.json else "\n".join(paths))
        return 0
    status, selected = pick_file(choices, args.query)
    if status:
        return status
    print(json.dumps(selected) if args.json else selected)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"file-picker: {error}", file=sys.stderr)
        raise SystemExit(2)
