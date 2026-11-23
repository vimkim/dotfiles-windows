"""Herdr's newline-delimited JSON API over a native Windows named pipe."""

import ctypes
from ctypes import wintypes
import json
import msvcrt
import os
import threading
import time


class HerdrError(RuntimeError):
    pass


_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_peek = _kernel32.PeekNamedPipe
_peek.argtypes = (
    wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
)
_peek.restype = wintypes.BOOL
_create_file = _kernel32.CreateFileW
_create_file.argtypes = (
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
)
_create_file.restype = wintypes.HANDLE


def _open_pipe(socket_path, timeout=3):
    # The .sock file is a server identity marker, not a Unix domain socket.
    pipe_name = "\\\\.\\pipe\\" + str(socket_path)
    deadline = time.monotonic() + timeout
    while True:
        # Python's CRT open() can mask ERROR_PIPE_BUSY as EINVAL. Use the
        # native error so concurrent requests can retry only a busy pipe.
        handle = _create_file(pipe_name, 0xC0000000, 0, None, 3, 0, None)
        if handle != ctypes.c_void_p(-1).value:
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
            return os.fdopen(descriptor, "r+b", buffering=0)
        error = ctypes.get_last_error()
        if error != 231 or time.monotonic() >= deadline:
            raise ctypes.WinError(error)
        time.sleep(0.01)


class PipeStream:
    """Streaming newline-delimited JSON client over a Windows named pipe."""

    def __init__(self, socket_path, timeout=3):
        self._pipe = _open_pipe(socket_path, timeout=timeout)
        self._buffer = bytearray()
        self._closed = threading.Event()
        self._lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.close()

    def close(self):
        self._closed.set()
        with self._lock:
            pipe = self._pipe
            self._pipe = None
        if pipe is not None:
            try:
                pipe.close()
            except OSError:
                pass

    def send_json(self, payload, label="request"):
        data = json.dumps(payload, separators=(",", ":")).encode() + b"\n"
        with self._lock:
            pipe = self._pipe
            if pipe is None:
                raise HerdrError(f"Herdr closed the connection during {label}")
            while data:
                written = pipe.write(data)
                if not written:
                    raise HerdrError(f"Herdr closed the connection during {label}")
                data = data[written:]

    def read_line(self, timeout=None, limit=16 * 1024 * 1024, label="response"):
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            newline = self._buffer.find(b"\n")
            if newline != -1:
                line = bytes(self._buffer[: newline + 1])
                del self._buffer[: newline + 1]
                return line
            if len(self._buffer) > limit:
                raise HerdrError(f"response to {label} exceeds {limit} bytes")
            if self._closed.is_set():
                raise HerdrError(f"incomplete response to {label}")
            if deadline is not None and time.monotonic() >= deadline:
                raise HerdrError(f"timed out waiting for {label}")
            with self._lock:
                pipe = self._pipe
                if pipe is None:
                    raise HerdrError(f"incomplete response to {label}")
                handle = msvcrt.get_osfhandle(pipe.fileno())
                available = wintypes.DWORD()
                if not _peek(handle, None, 0, None, ctypes.byref(available), None):
                    error = ctypes.get_last_error()
                    if error in (109, 232, 233):
                        raise HerdrError(f"incomplete response to {label}")
                    raise ctypes.WinError(error)
                if available.value:
                    chunk = pipe.read(min(available.value, 64 * 1024))
                    if not chunk:
                        raise HerdrError(f"incomplete response to {label}")
                    self._buffer.extend(chunk)
                    if len(self._buffer) > limit + 1:
                        raise HerdrError(f"response to {label} exceeds {limit} bytes")
                    continue
            self._closed.wait(0.01)


def request(socket_path, method, params, timeout=3, limit=16 * 1024 * 1024, request_id="dotfiles"):
    payload = {"id": request_id, "method": method, "params": params}
    with PipeStream(socket_path, timeout=timeout) as stream:
        stream.send_json(payload, label=method)
        line = stream.read_line(timeout=timeout, limit=limit, label=method)
    response = json.loads(line)
    if not isinstance(response, dict) or response.get("id") != payload["id"]:
        raise HerdrError(f"unexpected response id for {method}")
    if "error" in response:
        error = response["error"]
        message = error.get("message", "Herdr API error") if isinstance(error, dict) else str(error)
        raise HerdrError(message)
    result = response.get("result")
    if not isinstance(result, dict):
        raise HerdrError(f"invalid response for {method}")
    return result
