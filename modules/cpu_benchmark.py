import time
import math
import hashlib
import os
from concurrent.futures import ProcessPoolExecutor


def _math_workload(iterations):
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
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            func()
            count += 1
        return count

    # ── Tests ─────────────────────────────────────────────────────────────────

    def single_thread(self):
        count = self._run_timed(lambda: _math_workload(self.math_iters))
        return count * self._math_factor

    def multi_thread(self):
        """True multi-core stress via separate processes (escapes the GIL)."""
        cores = self.threads
        with ProcessPoolExecutor(max_workers=cores) as ex:
            futures = [ex.submit(_math_worker, self.duration, self.math_iters)
                       for _ in range(cores)]
            total = sum(f.result() for f in futures)
        return total * self._math_factor

    def compression(self):
        import zlib
        data = os.urandom(self.compress_size)
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            zlib.compress(data, level=6)
            count += 1
        return count * self._compress_factor

    def encryption(self):
        data = os.urandom(ENCRYPT_INPUT_SIZE)
        key = os.urandom(32)
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            hashlib.pbkdf2_hmac("sha256", data, key, self.pbkdf2_iters)
            count += 1
        return count * self._encrypt_factor

    def prime_sieve(self):
        def sieve(n):
            s = bytearray([1]) * (n + 1)
            s[0] = s[1] = 0
            for i in range(2, int(n ** 0.5) + 1):
                if s[i]:
                    s[i*i::i] = bytearray(len(s[i*i::i]))
        count = self._run_timed(lambda: sieve(self.sieve_n))
        return count * self._sieve_factor

    def run_all(self, verbose=False):
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
        return int(results.get("single", 0) + results.get("multi", 0) * 0.5)
