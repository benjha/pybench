"""CPU benchmark suite.

Measures processor throughput across five workloads — single-thread math,
multi-process math, zlib compression, PBKDF2 hashing, and a prime sieve.

Every test is a time-bounded loop: it repeats a fixed unit of work for
``duration`` seconds and counts completions. Because raising an intensity knob
makes each unit of work larger (and therefore lowers the raw count), each
metric is multiplied by a normalization factor so the reported numbers stay
comparable to a fixed baseline regardless of the knob settings.
"""
import time
import math
import hashlib
import os
from concurrent.futures import ProcessPoolExecutor


def _math_workload(iterations):
    """Run one FPU-heavy unit of work (``iterations`` of sqrt/log/sin).

    Returns the accumulated value purely so the loop cannot be optimized away.
    """
    x = 0.0
    for i in range(1, iterations):
        x += math.sqrt(i) * math.log(i + 1) * math.sin(i)
    return x


def _math_worker(duration, iterations):
    """Module-level worker so it can be pickled for ProcessPoolExecutor.

    Runs the math workload in a loop for ``duration`` seconds and returns
    the number of completed iterations.
    """
    count = 0
    start = time.perf_counter()
    while time.perf_counter() - start < duration:
        _math_workload(iterations)
        count += 1
    return count


# Baseline work-per-iteration. Reported metrics are normalized to these so
# that scores stay comparable no matter how the intensity knobs are set.
BASE_MATH_ITERS = 500
BASE_COMPRESS_SIZE = 64 * 1024
BASE_PBKDF2_ITERS = 1000
BASE_SIEVE_N = 100_000

# Fixed input size for the encryption test. PBKDF2 pre-hashes its input once
# and then the cost scales linearly with the iteration count, so we keep the
# input small/constant and use the iteration count as the single intensity
# knob — that makes the metric cleanly normalizable.
ENCRYPT_INPUT_SIZE = 1024


class CPUBenchmark:
    """Runs the CPU test battery and normalizes results to fixed baselines.

    Args:
        duration: Seconds to run each individual sub-test.
        threads: Worker process count for the multi-core test (defaults to
            the logical CPU count).
        math_iters: Inner-loop length for the math tests (intensity knob).
        compress_size: Bytes compressed per zlib call (intensity knob).
        pbkdf2_iters: PBKDF2 rounds per call, i.e. KDF hardness (intensity knob).
        sieve_n: Upper bound for the prime sieve (intensity knob).
    """

    def __init__(self, duration=5, threads=None,
                 math_iters=5000, compress_size=256 * 1024,
                 pbkdf2_iters=1000, sieve_n=1_000_000):
        self.duration = duration
        self.threads = threads or (os.cpu_count() or 4)
        # Intensity knobs (raise to make each test work harder):
        self.math_iters = math_iters        # inner loop length for math tests
        self.compress_size = compress_size  # bytes compressed per call
        self.pbkdf2_iters = pbkdf2_iters    # PBKDF2 rounds per call (hardness)
        self.sieve_n = sieve_n              # upper bound for prime sieve
        # Normalization factors: each completed iteration does this much more
        # work than the baseline, so we scale the raw counts up accordingly.
        self._math_factor = self.math_iters / BASE_MATH_ITERS
        self._compress_factor = self.compress_size / BASE_COMPRESS_SIZE
        self._encrypt_factor = self.pbkdf2_iters / BASE_PBKDF2_ITERS
        self._sieve_factor = self.sieve_n / BASE_SIEVE_N

    def _run_timed(self, func):
        """Call ``func`` repeatedly for ``duration`` seconds; return the count."""
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            func()
            count += 1
        return count

    # ── Tests ─────────────────────────────────────────────────────────────────

    def single_thread(self):
        """Single-core FPU throughput, normalized to the baseline math unit."""
        count = self._run_timed(lambda: _math_workload(self.math_iters))
        return count * self._math_factor

    def multi_thread(self):
        """Total multi-core FPU throughput via separate processes.

        Uses processes rather than threads so the work runs truly in parallel
        instead of being serialized by the GIL. The result is the summed
        completion count across all workers, normalized to the baseline unit.
        """
        cores = self.threads
        with ProcessPoolExecutor(max_workers=cores) as ex:
            futures = [ex.submit(_math_worker, self.duration, self.math_iters)
                       for _ in range(cores)]
            total = sum(f.result() for f in futures)
        return total * self._math_factor

    def compression(self):
        """zlib (level 6) throughput on a random buffer, baseline-normalized.

        Random data is near-incompressible, so this stresses the integer
        pipeline and memory rather than producing small output.
        """
        import zlib
        data = os.urandom(self.compress_size)
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            zlib.compress(data, level=6)
            count += 1
        return count * self._compress_factor

    def encryption(self):
        """PBKDF2-HMAC-SHA256 throughput, normalized by the iteration count.

        The input is a small fixed size so cost scales linearly with
        ``pbkdf2_iters``, which makes the metric cleanly normalizable.
        """
        data = os.urandom(ENCRYPT_INPUT_SIZE)
        key = os.urandom(32)
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            hashlib.pbkdf2_hmac("sha256", data, key, self.pbkdf2_iters)
            count += 1
        return count * self._encrypt_factor

    def prime_sieve(self):
        """Sieve-of-Eratosthenes throughput up to ``sieve_n``, baseline-normalized.

        Exercises branchy control flow and large ``bytearray`` slice
        traversal. Normalization is approximate since sieve cost is slightly
        super-linear in ``n``.
        """
        def sieve(n):
            s = bytearray([1]) * (n + 1)
            s[0] = s[1] = 0
            for i in range(2, int(n ** 0.5) + 1):
                if s[i]:
                    # Mark every multiple of i as composite in one slice write.
                    s[i*i::i] = bytearray(len(s[i*i::i]))
        count = self._run_timed(lambda: sieve(self.sieve_n))
        return count * self._sieve_factor

    def run_all(self, verbose=False):
        """Run every CPU sub-test and return a dict of normalized results."""
        results = {}
        if verbose:
            print("  Running Single-thread test...")
        results["single"] = self.single_thread()
        if verbose:
            print("  Running Multi-thread test (Stress Test)...")
        results["multi"] = self.multi_thread()
        if verbose:
            print("  Running Compression test...")
        results["compress"] = self.compression()
        if verbose:
            print("  Running Encryption simulation...")
        results["encrypt"] = self.encryption()
        if verbose:
            print("  Running Prime Sieve test...")
        results["prime"] = self.prime_sieve()
        if verbose:
            print("  " + "="*50)
        return results

    @staticmethod
    def score(results):
        """Weighted CPU score: single-thread plus half the multi-thread total.

        (The active scorer lives in scoring/scorer.py; this mirrors it for
        standalone use of the module.)
        """
        return int(results.get("single", 0) + results.get("multi", 0) * 0.5)
