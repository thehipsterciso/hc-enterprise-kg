"""Tests for advisory file locking."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from export.file_lock import GraphFileLock, LockTimeoutError


class TestGraphFileLock:
    """Core lock semantics."""

    def test_exclusive_lock_acquires_and_releases(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")
        with GraphFileLock(target, exclusive=True):
            assert target.exists()
        # Lock file created as companion
        assert (tmp_path / "graph.json.lock").exists()

    def test_shared_lock_acquires_and_releases(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")
        with GraphFileLock(target, exclusive=False):
            assert target.exists()

    def test_multiple_shared_locks_allowed(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")
        lock1 = GraphFileLock(target, exclusive=False)
        lock2 = GraphFileLock(target, exclusive=False)
        lock1.acquire()
        lock2.acquire()  # Should not block
        lock2.release()
        lock1.release()

    def test_exclusive_blocks_exclusive(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")
        lock1 = GraphFileLock(target, exclusive=True)
        lock1.acquire()

        # Second exclusive lock should timeout quickly
        with pytest.raises(LockTimeoutError):
            GraphFileLock(target, exclusive=True, timeout=0.1).acquire()

        lock1.release()

    def test_exclusive_blocks_shared(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")
        lock1 = GraphFileLock(target, exclusive=True)
        lock1.acquire()

        # Shared lock should timeout when exclusive is held
        with pytest.raises(LockTimeoutError):
            GraphFileLock(target, exclusive=False, timeout=0.1).acquire()

        lock1.release()

    def test_lock_released_on_exception(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")

        with pytest.raises(ValueError, match="test error"), GraphFileLock(target, exclusive=True):
            raise ValueError("test error")

        # Lock should be released — another exclusive lock should succeed
        with GraphFileLock(target, exclusive=True, timeout=0.1):
            pass

    def test_lock_creates_parent_dirs(self, tmp_path: Path):
        target = tmp_path / "a" / "b" / "graph.json"
        with GraphFileLock(target, exclusive=True):
            pass
        assert (tmp_path / "a" / "b" / "graph.json.lock").exists()

    def test_timeout_zero_fails_immediately(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("{}")
        lock1 = GraphFileLock(target, exclusive=True)
        lock1.acquire()

        start = time.monotonic()
        with pytest.raises(LockTimeoutError):
            GraphFileLock(target, exclusive=True, timeout=0).acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5  # Should fail fast

        lock1.release()


class TestFileLockConcurrency:
    """Thread-based concurrency tests."""

    def test_exclusive_serializes_writes(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("0")
        results: list[int] = []

        def writer(value: int) -> None:
            with GraphFileLock(target, exclusive=True):
                current = int(target.read_text())
                time.sleep(0.05)  # Simulate work
                target.write_text(str(current + value))
                results.append(value)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(1, 4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # All 3 writers completed
        assert len(results) == 3
        # Final value should be 1+2+3=6 (serialized, no race)
        assert int(target.read_text()) == 6

    def test_shared_allows_concurrent_reads(self, tmp_path: Path):
        target = tmp_path / "graph.json"
        target.write_text("test data")
        read_count = 0
        lock = threading.Lock()

        def reader() -> None:
            nonlocal read_count
            with GraphFileLock(target, exclusive=False):
                _ = target.read_text()
                time.sleep(0.05)
                with lock:
                    read_count += 1

        threads = [threading.Thread(target=reader) for _ in range(3)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        elapsed = time.monotonic() - start

        assert read_count == 3
        # Concurrent reads should complete in ~50ms, not 150ms
        assert elapsed < 0.3


class TestLockTimeoutError:
    """LockTimeoutError exception behavior."""

    def test_is_os_error_subclass(self):
        assert issubclass(LockTimeoutError, OSError)

    def test_message_includes_path(self, tmp_path: Path):
        target = tmp_path / "test.json"
        target.write_text("{}")
        lock = GraphFileLock(target, exclusive=True)
        lock.acquire()

        try:
            with pytest.raises(LockTimeoutError, match="test.json"):
                GraphFileLock(target, exclusive=True, timeout=0).acquire()
        finally:
            lock.release()
