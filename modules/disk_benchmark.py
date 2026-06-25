"""Disk I/O benchmark suite (CrystalDiskMark-style).

Creates a temporary test file and measures four patterns against it:
sequential 1 MB read/write at queue depth 8, and random 4 KB read/write at
queue depth 32. Queue depth is emulated with a thread pool; sequential results
are reported in MB/s and random results in IOPS. The test file is removed on
completion.

I/O is buffered, so reads may be served from the OS page cache; pass
``exceed_ram=True`` to size the file beyond physical RAM and measure the real
drive instead of the cache.
"""
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor


class DiskBenchmark:
    """Runs the disk test battery against a temporary file.

    Args:
        target_dir: Directory in which the temporary test file is created.
        duration: Seconds to run each sub-test.
        file_size: Working-set size of the test file in bytes.
        seq_threads: Concurrent workers (queue depth) for sequential tests.
        rnd_threads: Concurrent workers (queue depth) for random tests.
        seq_block: Block size for sequential I/O.
        rnd_block: Block size for random I/O.
        exceed_ram: If True, grow ``file_size`` beyond RAM to defeat the
            page cache.
    """

    def __init__(self, target_dir=".", duration=10,
                 file_size=1 * 1024 * 1024 * 1024,
                 seq_threads=8, rnd_threads=32,
                 seq_block=1024 * 1024, rnd_block=4096,
                 exceed_ram=False):
        self.test_file = os.path.join(target_dir, "CDM_test.tmp")
        self.duration = duration
        # Intensity knobs:
        self.file_size = file_size      # working-set size on disk
        self.seq_threads = seq_threads  # queue depth for sequential test
        self.rnd_threads = rnd_threads  # queue depth for random test
        self.seq_block = seq_block      # sequential block size
        self.rnd_block = rnd_block      # random block size
        # When True, grow the test file beyond physical RAM so reads cannot
        # all be served from the OS page cache (measures the real drive).
        if exceed_ram:
            self.file_size = max(self.file_size, self._ram_busting_size())

    @staticmethod
    def _ram_busting_size():
        """A file size comfortably larger than physical RAM (best effort)."""
        try:
            import psutil
            total_ram = psutil.virtual_memory().total
        except Exception:
            total_ram = 8 * 1024 * 1024 * 1024  # assume 8 GB if unknown
        # 1.5x RAM ensures the page cache cannot hold the whole working set.
        return int(total_ram * 1.5)

    # ── File preparation ──────────────────────────────────────────────────────

    def _prepare_test_file(self):
        """Create the test file at the configured size if missing/too small.

        Writes 1 MB random chunks and ``fsync``s so the data is genuinely on
        disk before measurement begins.
        """
        if not os.path.exists(self.test_file) or \
                os.path.getsize(self.test_file) < self.file_size:
            chunk = os.urandom(1024 * 1024)
            with open(self.test_file, "wb") as f:
                for _ in range(self.file_size // (1024 * 1024)):
                    f.write(chunk)
                os.fsync(f.fileno())

    # ── Thread runner ─────────────────────────────────────────────────────────

    def _threaded_io(self, func, threads):
        """Run ``func`` on ``threads`` workers and return the summed throughput.

        Threads work here despite the GIL because file I/O releases it, which
        is what lets this emulate a deeper queue depth.
        """
        with ThreadPoolExecutor(max_workers=threads) as ex:
            futures = [ex.submit(func) for _ in range(threads)]
            total = sum(f.result() for f in futures)
        return total

    # ── SEQ 1M Q8T1 ───────────────────────────────────────────────────────────

    def seq_1m_q8t1(self, mode="write"):
        """Sequential large-block throughput in MB/s (summed across threads).

        Args:
            mode: ``"write"`` or ``"read"``.
        """
        block_size = self.seq_block
        data = os.urandom(block_size)

        def write_task():
            total_mb = 0
            start = time.perf_counter()
            with open(self.test_file, "r+b") as f:
                idx = 0
                while time.perf_counter() - start < self.duration:
                    offset = (idx * block_size) % (self.file_size - block_size)
                    f.seek(offset)
                    f.write(data)
                    idx += 1
                    total_mb += 1
                f.flush()
                os.fsync(f.fileno())
            elapsed = time.perf_counter() - start
            return total_mb / elapsed if elapsed > 1e-6 else 0.0

        def read_task():
            total_mb = 0
            start = time.perf_counter()
            with open(self.test_file, "rb") as f:
                idx = 0
                while time.perf_counter() - start < self.duration:
                    offset = (idx * block_size) % (self.file_size - block_size)
                    f.seek(offset)
                    f.read(block_size)
                    idx += 1
                    total_mb += 1
            elapsed = time.perf_counter() - start
            return total_mb / elapsed if elapsed > 1e-6 else 0.0

        task = write_task if mode == "write" else read_task
        raw = self._threaded_io(task, threads=self.seq_threads)  # MB/s summed
        return raw

    # ── RND 4K Q32T1 ──────────────────────────────────────────────────────────

    def rnd_4k_q32t1(self, mode="write"):
        """Random small-block throughput in IOPS (summed across threads).

        Seeks to a random block-aligned offset before each operation to stress
        the drive's random-access path.

        Args:
            mode: ``"write"`` or ``"read"``.
        """
        block_size = self.rnd_block
        data = os.urandom(block_size)

        def write_task():
            count = 0
            start = time.perf_counter()
            with open(self.test_file, "r+b") as f:
                while time.perf_counter() - start < self.duration:
                    pos = random.randint(
                        0, self.file_size // block_size - 1) * block_size
                    f.seek(pos)
                    f.write(data)
                    count += 1
                f.flush()
                os.fsync(f.fileno())
            elapsed = time.perf_counter() - start
            return count / elapsed if elapsed > 1e-6 else 0.0

        def read_task():
            count = 0
            start = time.perf_counter()
            with open(self.test_file, "rb") as f:
                while time.perf_counter() - start < self.duration:
                    pos = random.randint(
                        0, self.file_size // block_size - 1) * block_size
                    f.seek(pos)
                    f.read(block_size)
                    count += 1
            elapsed = time.perf_counter() - start
            return count / elapsed if elapsed > 1e-6 else 0.0

        task = write_task if mode == "write" else read_task
        return self._threaded_io(task, threads=self.rnd_threads)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def cleanup(self):
        """Delete the temporary test file, ignoring any removal errors."""
        if os.path.exists(self.test_file):
            try:
                os.remove(self.test_file)
            except Exception:
                pass

    def run_all(self, verbose=False):
        """Prepare the file, run all four I/O patterns, and always clean up.

        Returns a dict with sequential/random read/write results plus a
        combined ``iops`` figure. Cleanup runs even if a sub-test raises.
        """
        results = {}
        try:
            if verbose:
                print(
                    f"  Preparing {self.file_size // 1024 // 1024}MB Test File...")
            self._prepare_test_file()

            if verbose:
                print("  Running SEQ1M Q8T1 Write...")
            results["seq_write"] = self.seq_1m_q8t1(mode="write")

            if verbose:
                print("  Running SEQ1M Q8T1 Read...")
            results["seq_read"] = self.seq_1m_q8t1(mode="read")

            if verbose:
                print("  Running RND4K Q32T1 Write...")
            results["rand_write"] = self.rnd_4k_q32t1(mode="write")

            if verbose:
                print("  Running RND4K Q32T1 Read...")
            results["rand_read"] = self.rnd_4k_q32t1(mode="read")

            results["iops"] = results["rand_read"] + results["rand_write"]
        finally:
            self.cleanup()
        if verbose:
            print("  " + "="*50)
        return results

    @staticmethod
    def score(results):
        """Weighted disk score from sequential MB/s and random IOPS totals.

        (Mirrors the active scorer in scoring/scorer.py for standalone use.)
        """
        seq = (results.get("seq_read",  0) or 0) + \
            (results.get("seq_write", 0) or 0)
        rnd = (results.get("rand_read", 0) or 0) + \
            (results.get("rand_write", 0) or 0)
        return int(seq * 0.05 + rnd * 1.2)
