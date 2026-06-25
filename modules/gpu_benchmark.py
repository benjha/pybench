"""GPU benchmark suite (CUDA via CuPy).

Runs two tests on the first available CUDA device: a compute kernel applying
sqrt/log/sin per element, and a host<->device VRAM bandwidth transfer. If no
CUDA device is available, the compute test transparently falls back to a CPU
scalar loop and the VRAM test reports ``None``.

CuPy is imported lazily/guarded so the module still loads (and the rest of
PyBench runs) on machines without a CUDA runtime. CuPy ships prebuilt wheels
with the CUDA runtime bundled and JIT-compiles kernels via NVRTC, so no CUDA
Toolkit / ``nvcc`` install is required — only an NVIDIA driver at runtime.
"""
import time
import math

try:
    import cupy as cp
    HAS_CUPY = True
except Exception:
    HAS_CUPY = False

# Compute-intensity knob: math iterations per element in the compute kernel.
# The reported throughput is normalized by this value so the score stays
# comparable regardless of how high it is set.
COMPUTE_INNER_ITERS = 256


class GPUBenchmark:
    """Runs the GPU test battery, with automatic CPU fallback.

    Args:
        duration: Seconds to run each sub-test.

    Attributes:
        cuda_ok: True once a CUDA device was found and selected via CuPy.
    """

    def __init__(self, duration=5):
        self.duration = duration
        self.cuda_ok = False
        self.device = None
        self._init_cuda()

    def _init_cuda(self):
        """Select the first CUDA device via CuPy; stay silent on failure.

        Leaves ``cuda_ok`` False if no device is found or setup raises, which
        triggers the CPU fallback path in the tests.
        """
        if not HAS_CUPY:
            return
        try:
            if cp.cuda.runtime.getDeviceCount() < 1:
                return
            self.device = cp.cuda.Device(0)
            self.device.use()
            self.cuda_ok = True
        except Exception:
            pass

    # ── GPU compute (CUDA) ────────────────────────────────────────────────────

    def compute(self):
        """GPU compute throughput in MOps/s (falls back to CPU if no CUDA).

        Builds and dispatches the compute kernel over a large float32 array,
        synchronizing each launch. The result is normalized by the kernel's
        inner-loop count so the figure is independent of the intensity knob.
        """
        if not self.cuda_ok:
            return self._cpu_fallback_compute()
        try:
            import numpy as np
            SIZE = 16 * 1024 * 1024
            src = cp.random.rand(SIZE, dtype=cp.float32)
            dst = cp.empty_like(src)
            kernel = cp.RawKernel(r"""
                extern "C" __global__
                void compute(const float* src, float* dst, int n) {
                    int i = blockIdx.x * blockDim.x + threadIdx.x;
                    if (i >= n) return;
                    float x = src[i];
                    float acc = 0.0f;
                    for (int k = 0; k < %d; k++) {
                        acc += sqrtf(x) * logf(x + 1.0f) * sinf(x + k);
                    }
                    dst[i] = acc;
                }
            """ % COMPUTE_INNER_ITERS, "compute")
            block = 256
            grid = (SIZE + block - 1) // block
            count = 0
            start = time.perf_counter()
            while time.perf_counter() - start < self.duration:
                kernel((grid,), (block,), (src, dst, np.int32(SIZE)))
                cp.cuda.runtime.deviceSynchronize()
                count += 1
            elapsed = time.perf_counter() - start
            # Normalize by the inner-loop count so the reported throughput is
            # invariant to the compute-intensity knob (matches the original
            # single-op-per-element scale when COMPUTE_INNER_ITERS == 1).
            return (count * SIZE * COMPUTE_INNER_ITERS) / elapsed / 1e6
        except Exception:
            return self._cpu_fallback_compute()

    def _cpu_fallback_compute(self):
        """Scalar math fallback when no GPU is available."""
        SIZE = 10_000
        count = 0
        start = time.perf_counter()
        while time.perf_counter() - start < self.duration:
            for i in range(1, SIZE):
                _ = math.sqrt(i) * math.log(i + 1) * math.sin(i)
            count += 1
        elapsed = time.perf_counter() - start
        return (count * SIZE) / elapsed / 1e6

    # ── VRAM bandwidth ────────────────────────────────────────────────────────

    def vram_bandwidth(self):
        """Host->device->host transfer bandwidth in MB/s, or None without CUDA.

        Repeatedly uploads a NumPy array to a device buffer and copies it back,
        measuring effective PCIe/VRAM throughput.
        """
        if not self.cuda_ok:
            return None          # ← None, not 0
        try:
            import numpy as np
            SIZE = 256 * 1024 * 1024  # 256 MB
            data = np.random.rand(SIZE // 4).astype(np.float32)
            out = np.empty_like(data)
            d_buf = cp.empty(data.shape, dtype=cp.float32)
            total = 0
            start = time.perf_counter()
            while time.perf_counter() - start < self.duration:
                d_buf.set(data)        # host -> device
                d_buf.get(out=out)     # device -> host
                cp.cuda.runtime.deviceSynchronize()
                total += SIZE
            elapsed = time.perf_counter() - start
            return (total / elapsed) / (1024 ** 2) if elapsed > 1e-6 else None
        except Exception:
            return None

    def run_all(self, verbose=False):
        """Run the GPU sub-tests and return results, including the CUDA status."""
        results = {}
        if not self.cuda_ok:
            if verbose:
                print(
                    "  [WARNING] CUDA not found or initialization failed. Using CPU fallback for GPU tests.")
        if verbose:
            print("  Running GPU Compute test...")
        results["compute"] = self.compute()
        if verbose:
            print("  Running VRAM Bandwidth test...")
        results["vram_bw"] = self.vram_bandwidth()   # may be None
        results["cuda_ok"] = self.cuda_ok
        if verbose:
            print("  " + "="*50)
        return results

    @staticmethod
    def score(results):
        """Weighted GPU score from compute MOps/s and VRAM bandwidth.

        (Mirrors the active scorer in scoring/scorer.py for standalone use.)
        """
        compute = results.get("compute", 0) or 0
        vram = results.get("vram_bw", 0) or 0
        return int(compute * 5 + vram * 0.1)
