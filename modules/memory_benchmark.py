import time
import os
import gc
from array import array


# Baseline alloc block size; alloc throughput is normalized to it so the
# metric (and score) is invariant to the alloc_size intensity knob.
BASE_ALLOC_SIZE = 1024 * 1024


class MemoryBenchmark:
    def __init__(self, duration=5, seq_buf_size=512 * 1024 * 1024,
                 rand_buf_size=256 * 1024 * 1024,
                 copy_chunk=256 * 1024 * 1024,
                 alloc_size=1024 * 1024):
        self.duration = duration
        # Intensity knobs (raise to exceed caches / move more bytes):
        self.seq_buf_size = seq_buf_size    # sequential bandwidth buffer
        self.rand_buf_size = rand_buf_size  # random-access buffer (latency)
        self.copy_chunk = copy_chunk        # bytes per memoryview copy
        self.alloc_size = alloc_size        # bytes per alloc/free cycle
        self._alloc_factor = self.alloc_size / BASE_ALLOC_SIZE

    # ── Sequential bandwidth ──────────────────────────────────────────────────

    def seq_bandwidth(self):
        """MB/s of raw memory read/write using bytearray copies."""
        BUF_SIZE = self.seq_buf_size
        buf = bytearray(os.urandom(BUF_SIZE))
        total_bytes = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            # write pass
            buf2 = bytearray(BUF_SIZE)
            buf2[:] = buf
            # read pass
            _ = buf2[0]
            total_bytes += BUF_SIZE * 2  # write + read
            del buf2
        elapsed = time.perf_counter() - start
        del buf
        if elapsed < 1e-6:
            return 0.0
        return (total_bytes / elapsed) / (1024 ** 2)

    # ── Random access speed ───────────────────────────────────────────────────

    def random_latency(self):
        """Dependent-load reads/s over a buffer sized to exceed CPU cache.

        Uses pointer chasing (each read's result selects the next index) so
        the CPU cannot trivially prefetch, over a buffer larger than the
        last-level cache so the loads actually hit main memory. The index
        table is filled with a large prime stride (coprime to the slot
        count) which is O(n) to build yet scatters accesses across pages.
        """
        slots = max(1024, self.rand_buf_size // 8)  # 8 bytes per 'q' entry
        # Large prime stride keeps successive accesses far apart (many pages),
        # defeating simple sequential prefetch without an expensive shuffle.
        stride = 1572869 % slots or 1
        # buf[i] = (i + stride) % slots, built at C speed via concatenation.
        buf = array('q', range(stride, slots))
        buf.extend(range(0, stride))

        idx = 0
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            # Unrolled to amortize the Python loop overhead per dependent load.
            idx = buf[idx]
            idx = buf[idx]
            idx = buf[idx]
            idx = buf[idx]
            idx = buf[idx]
            idx = buf[idx]
            idx = buf[idx]
            idx = buf[idx]
            count += 8
        elapsed = time.perf_counter() - start
        return count / elapsed if elapsed > 1e-6 else 0.0

    # ── Memory copy speed ─────────────────────────────────────────────────────

    def copy_speed(self):
        """GB/s of memoryview-based copy."""
        CHUNK = self.copy_chunk
        src = bytearray(CHUNK)
        dst = bytearray(CHUNK)
        total = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            mv_src = memoryview(src)
            mv_dst = memoryview(dst)
            mv_dst[:] = mv_src
            total += CHUNK
        elapsed = time.perf_counter() - start
        return (total / elapsed) / (1024 ** 3) if elapsed > 1e-6 else 0.0

    # ── Allocation stress ─────────────────────────────────────────────────────

    def alloc_stress(self):
        """Alloc+free cycles per second."""
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            _ = bytearray(self.alloc_size)
            count += 1
        gc.collect()
        elapsed = time.perf_counter() - start
        if elapsed <= 1e-6:
            return 0.0
        return (count * self._alloc_factor) / elapsed

    def run_all(self, verbose=False):
        results = {}
        if verbose:
            print("  Running Sequential Bandwidth test...")
        results["seq_bw"] = self.seq_bandwidth()
        if verbose:
            print("  Running Random Access Speed test...")
        results["rand_lat"] = self.random_latency()
        if verbose:
            print("  Running Memory Copy test...")
        results["copy"] = self.copy_speed()
        if verbose:
            print("  Running Allocation Stress test...")
        results["alloc"] = self.alloc_stress()
        if verbose:
            print("  " + "="*50)
        return results

    @staticmethod
    def score(results):
        bw = results.get("seq_bw",   0) or 0
        copy = results.get("copy",     0) or 0
        lat = results.get("rand_lat", 0) or 0
        return int(bw * 0.4 + copy * 500 + lat / 5_000)
