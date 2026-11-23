"""Multi-instance byte-stream named-pipe server for Herdr's Windows protocol tests."""

import ctypes
from ctypes import wintypes
from pathlib import Path
import threading


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

_PIPE_UNLIMITED_INSTANCES = 255
_INVALID_HANDLE = ctypes.c_void_p(-1).value


def file_is_closed(path):
    if not path.exists():
        return True
    handle = _create_file(str(path), 0x80000000, 0, None, 3, 0, None)
    if handle == _INVALID_HANDLE:
        if ctypes.get_last_error() == 32:
            return False
        raise ctypes.WinError(ctypes.get_last_error())
    _close(handle)
    return True


class PipeConnection:
    def __init__(self, handle):
        self.handle = handle
        self.closed = False
        self._lock = threading.Lock()
        self._buffer = bytearray()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def close(self):
        with self._lock:
            if self.closed:
                return
            self.closed = True
            _disconnect(self.handle)
            _close(self.handle)

    def makefile(self, _mode):
        return self

    def readline(self):
        while b"\n" not in self._buffer:
            buffer = ctypes.create_string_buffer(65536)
            received = wintypes.DWORD()
            if not _read(self.handle, buffer, len(buffer), ctypes.byref(received), None):
                error = ctypes.get_last_error()
                if error in (109, 232, 233):
                    return b""
                raise ctypes.WinError(error)
            if received.value == 0:
                return b""
            self._buffer.extend(buffer.raw[:received.value])
        newline = self._buffer.index(b"\n")
        line = bytes(self._buffer[: newline + 1])
        del self._buffer[: newline + 1]
        return line

    def write(self, data):
        with self._lock:
            if self.closed:
                raise OSError("pipe connection closed")
            while data:
                written = wintypes.DWORD()
                if not _write(self.handle, data, len(data), ctypes.byref(written), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                data = data[written.value:]

    def flush(self):
        with self._lock:
            if self.closed:
                return
            if not _flush(self.handle):
                raise ctypes.WinError(ctypes.get_last_error())


class PipeListener:
    def __init__(self, path):
        self.path = Path(path)
        self.name = "\\\\.\\pipe\\" + str(path)
        self.closed = False
        self._lock = threading.Lock()
        self._pending_handle = self._new_instance()
        self.path.write_text("test-server")

    def _new_instance(self):
        handle = _create(
            self.name,
            3,  # PIPE_ACCESS_DUPLEX
            0,  # PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT
            _PIPE_UNLIMITED_INSTANCES,
            65536,
            65536,
            0,
            None,
        )
        if handle == _INVALID_HANDLE:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def accept(self):
        with self._lock:
            if self.closed:
                raise OSError("listener closed")
            handle = self._pending_handle
            self._pending_handle = None
        if handle is None:
            handle = self._new_instance()
        if not _connect(handle, None) and ctypes.get_last_error() != 535:
            error = ctypes.get_last_error()
            _close(handle)
            raise ctypes.WinError(error)
        with self._lock:
            if not self.closed:
                # Immediately open the next server instance so concurrent
                # clients (e.g. events.subscribe + session.snapshot) never block.
                self._pending_handle = self._new_instance()
        return PipeConnection(handle), None

    def wake(self):
        try:
            with open(self.name, "r+b", buffering=0):
                pass
        except OSError:
            pass

    def close(self):
        with self._lock:
            self.closed = True
            handle = self._pending_handle
            self._pending_handle = None
        if handle is not None:
            _close(handle)
