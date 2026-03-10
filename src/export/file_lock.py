"""Advisory file locking for graph persistence.

Provides a context-manager that wraps ``fcntl.flock()`` on POSIX (with
a ``msvcrt`` fallback on Windows) so concurrent readers and writers of
``graph.json`` cooperate safely.

Usage::

    from export.file_lock import GraphFileLock

    # Exclusive lock for writing
    with GraphFileLock(path, exclusive=True):
        path.write_text(content)

    # Shared lock for reading
    with GraphFileLock(path, exclusive=False):
        data = path.read_text()
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


class LockTimeoutError(OSError):
    """Raised when a file lock cannot be acquired within the timeout."""


class GraphFileLock:
    """Advisory file lock (shared or exclusive) with timeout.

    Parameters
    ----------
    path:
        Path to the file to lock.  A companion ``.lock`` file is created
        in the same directory to avoid interfering with the data file.
    exclusive:
        ``True`` for an exclusive (write) lock, ``False`` for a shared
        (read) lock.
    timeout:
        Maximum seconds to wait for the lock.  ``0`` means non-blocking
        (fail immediately if the lock is held).
    """

    def __init__(
        self,
        path: Path | str,
        *,
        exclusive: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self._path = Path(path)
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        self._exclusive = exclusive
        self._timeout = timeout
        self._fd: int | None = None

    def acquire(self) -> None:
        """Acquire the advisory lock, blocking up to *timeout* seconds."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Open (or create) the lock file
        flags = os.O_RDWR | os.O_CREAT
        self._fd = os.open(str(self._lock_path), flags, 0o666)

        deadline = time.monotonic() + self._timeout
        poll_interval = 0.05  # 50 ms

        while True:
            try:
                self._try_lock()
                return  # success
            except OSError:
                if time.monotonic() >= deadline:
                    # Clean up fd before raising
                    os.close(self._fd)
                    self._fd = None
                    raise LockTimeoutError(
                        f"Could not acquire {'exclusive' if self._exclusive else 'shared'} "
                        f"lock on {self._path} within {self._timeout}s"
                    ) from None
                time.sleep(poll_interval)

    def release(self) -> None:
        """Release the advisory lock."""
        if self._fd is not None:
            try:
                self._try_unlock()
            finally:
                os.close(self._fd)
                self._fd = None

    def __enter__(self) -> GraphFileLock:
        self.acquire()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Platform-specific lock primitives
    # ------------------------------------------------------------------

    def _try_lock(self) -> None:
        """Non-blocking lock attempt.  Raises OSError if unavailable."""
        if sys.platform == "win32":
            self._try_lock_windows()
        else:
            self._try_lock_posix()

    def _try_unlock(self) -> None:
        if sys.platform == "win32":
            self._try_unlock_windows()
        else:
            self._try_unlock_posix()

    def _try_lock_posix(self) -> None:
        import fcntl

        flag = fcntl.LOCK_NB
        flag |= fcntl.LOCK_EX if self._exclusive else fcntl.LOCK_SH
        fcntl.flock(self._fd, flag)

    def _try_unlock_posix(self) -> None:
        import fcntl

        fcntl.flock(self._fd, fcntl.LOCK_UN)

    def _try_lock_windows(self) -> None:  # pragma: no cover
        import msvcrt

        # msvcrt.locking only supports exclusive locks
        msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)

    def _try_unlock_windows(self) -> None:  # pragma: no cover
        import msvcrt

        msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
