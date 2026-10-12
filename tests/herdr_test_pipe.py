"""Small byte-stream named-pipe server for Herdr's Windows protocol tests."""

import ctypes
from ctypes import wintypes
from pathlib import Path


_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


def api(name, args, result=wintypes.BOOL):
    function = getattr(_kernel32, name)
    function.argtypes = args
    function.restype = result
    return function


_create = api("CreateNamedPipeW", (wintypes.LPCWSTR, *([wintypes.DWORD] * 6), wintypes.LPVOID), wintypes.HANDLE)
_connect = api("ConnectNamedPipe", (wintypes.HANDLE, wintypes.LPVOID))
_disconnect = api("DisconnectNamedPipe", (wintypes.HANDLE,))
_close = api("CloseHandle", (wintypes.HANDLE,))
_flush = api("FlushFileBuffers", (wintypes.HANDLE,))
_create_file = api("CreateFileW", (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE), wintypes.HANDLE)
_read = api("ReadFile", (wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID))
_write = api("WriteFile", (wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID))


def file_is_closed(path):
    if not path.exists():
        return True
    handle = _create_file(str(path), 0x80000000, 0, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        if ctypes.get_last_error() == 32:
            return False
        raise ctypes.WinError(ctypes.get_last_error())
    _close(handle)
    return True


class PipeConnection:
    def __init__(self, handle):
        self.handle = handle
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        if not self.closed:
            self.closed = True
            _disconnect(self.handle)

    def makefile(self, _mode):
        return self

    def readline(self):
        line = bytearray()
        while b"\n" not in line:
            buffer = ctypes.create_string_buffer(65536)
            received = wintypes.DWORD()
            if not _read(self.handle, buffer, len(buffer), ctypes.byref(received), None):
                raise ctypes.WinError(ctypes.get_last_error())
            line.extend(buffer.raw[:received.value])
        return bytes(line)

    def write(self, data):
        while data:
            written = wintypes.DWORD()
            if not _write(self.handle, data, len(data), ctypes.byref(written), None):
                raise ctypes.WinError(ctypes.get_last_error())
            data = data[written.value:]

    def flush(self):
        if not _flush(self.handle):
            raise ctypes.WinError(ctypes.get_last_error())


class PipeListener:
    def __init__(self, path):
        self.path = Path(path)
        self.name = "\\\\.\\pipe\\" + str(path)
        self.handle = _create(self.name, 3, 0, 1, 65536, 65536, 0, None)
        if self.handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        self.path.write_text("test-server")

    def accept(self):
        if not _connect(self.handle, None) and ctypes.get_last_error() != 535:
            raise ctypes.WinError(ctypes.get_last_error())
        return PipeConnection(self.handle), None

    def wake(self):
        try:
            with open(self.name, "r+b", buffering=0):
                pass
        except OSError:
            pass

    def close(self):
        _close(self.handle)
