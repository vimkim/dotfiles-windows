"""Herdr's newline-delimited JSON API over a native Windows named pipe."""

import ctypes
from ctypes import wintypes
import json
import msvcrt
import os
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


def request(socket_path, method, params, timeout=3):
    payload = {"id": "dotfiles", "method": method, "params": params}
    # The .sock file is a server identity marker, not a Unix domain socket.
    pipe_name = "\\\\.\\pipe\\" + str(socket_path)
    deadline = time.monotonic() + timeout
    while True:
        # Python's CRT open() can mask ERROR_PIPE_BUSY as EINVAL. Use the
        # native error so concurrent requests can retry only a busy pipe.
        handle = _create_file(pipe_name, 0xC0000000, 0, None, 3, 0, None)
        if handle != ctypes.c_void_p(-1).value:
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
            pipe = os.fdopen(descriptor, "r+b", buffering=0)
            break
        error = ctypes.get_last_error()
        if error != 231 or time.monotonic() >= deadline:
            raise ctypes.WinError(error)
        time.sleep(0.01)

    with pipe:
        data = json.dumps(payload, separators=(",", ":")).encode() + b"\n"
        while data:
            written = pipe.write(data)
            if not written:
                raise HerdrError(f"Herdr closed the connection during {method}")
            data = data[written:]
        handle = msvcrt.get_osfhandle(pipe.fileno())
        response_bytes = bytearray()
        while b"\n" not in response_bytes:
            if time.monotonic() >= deadline:
                raise HerdrError(f"timed out waiting for {method}")
            available = wintypes.DWORD()
            if not _peek(handle, None, 0, None, ctypes.byref(available), None):
                error = ctypes.get_last_error()
                if error in (109, 232, 233):
                    raise HerdrError(f"incomplete response to {method}")
                raise ctypes.WinError(error)
            if available.value:
                chunk = pipe.read(min(available.value, 64 * 1024))
                if not chunk:
                    raise HerdrError(f"incomplete response to {method}")
                response_bytes.extend(chunk)
                if len(response_bytes) > 16 * 1024 * 1024:
                    raise HerdrError(f"response to {method} exceeds 16 MiB")
            else:
                time.sleep(0.01)
    response = json.loads(response_bytes.split(b"\n", 1)[0])
    if response.get("id") != payload["id"]:
        raise HerdrError(f"unexpected response id for {method}")
    if "error" in response:
        raise HerdrError(response["error"].get("message", "Herdr API error"))
    return response["result"]
