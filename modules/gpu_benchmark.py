import time
import math

try:
    import pyopencl as cl
    HAS_OPENCL = True
except Exception:
    HAS_OPENCL = False

# Compute-intensity knob: math iterations per element in the compute kernel.
# The reported throughput is normalized by this value so the score stays
# comparable regardless of how high it is set.
COMPUTE_INNER_ITERS = 256


class GPUBenchmark:
    def __init__(self, duration=5):
        self.duration = duration
        self.opencl_ok = False
        self.ctx = None
        self.queue = None
        self._init_opencl()

    def _init_opencl(self):
        if not HAS_OPENCL:
            return
        try:
            platforms = cl.get_platforms()
            if not platforms:
                return
            devices = platforms[0].get_devices()
            if not devices:
                return
            self.ctx = cl.Context(devices=[devices[0]])
            self.queue = cl.CommandQueue(self.ctx)
            self.opencl_ok = True
        except Exception:
            pass

    # ── GPU compute (OpenCL) ──────────────────────────────────────────────────

    def compute(self):
        if not self.opencl_ok:
            return self._cpu_fallback_compute()
        try:
            import numpy as np
            import pyopencl.array as cla
            SIZE = 16 * 1024 * 1024
            src = cla.to_device(
                self.queue, np.random.rand(SIZE).astype(np.float32))
            dst = cla.empty_like(src)
            prog = cl.Program(self.ctx, """
                __kernel void compute(__global float* src, __global float* dst) {
                    int i = get_global_id(0);
                    float x = src[i];
                    float acc = 0.0f;
                    for (int k = 0; k < %d; k++) {
                        acc += sqrt(x) * log(x + 1.0f) * sin(x + k);
                    }
                    dst[i] = acc;
                }
            """ % COMPUTE_INNER_ITERS).build()
            kernel = cl.Kernel(prog, "compute")
            count = 0
            start = time.perf_counter()
            while time.perf_counter() - start < self.duration:
                kernel(self.queue, (SIZE,), None, src.data, dst.data)
                self.queue.finish()
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
        """Returns MB/s or None when OpenCL is unavailable."""
        if not self.opencl_ok:
            return None          # ← None, not 0
        try:
            import numpy as np
            SIZE = 256 * 1024 * 1024  # 256 MB
            data = np.random.rand(SIZE // 4).astype(np.float32)
            total = 0
            start = time.perf_counter()
            while time.perf_counter() - start < self.duration:
                buf = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                hostbuf=data)
                out = np.empty_like(data)
                cl.enqueue_copy(self.queue, out, buf)
                self.queue.finish()
                total += SIZE
                del buf
            elapsed = time.perf_counter() - start
            return (total / elapsed) / (1024 ** 2) if elapsed > 1e-6 else None
        except Exception:
            return None

    def run_all(self, verbose=False):
        results = {}
        if not self.opencl_ok:
            if verbose:
                print(
                    "  [WARNING] OpenCL not found or initialization failed. Using CPU fallback for GPU tests.")
            pass
        if verbose:
            print("  Running GPU Compute test...")
        results["compute"] = self.compute()
        if verbose:
            print("  Running VRAM Bandwidth test...")
        results["vram_bw"] = self.vram_bandwidth()   # may be None
        results["opencl_ok"] = self.opencl_ok
        if verbose:
            print("  " + "="*50)
        return results

    @staticmethod
    def score(results):
        compute = results.get("compute", 0) or 0
        vram = results.get("vram_bw", 0) or 0
        return int(compute * 5 + vram * 0.1)
