# 🧪 PyBench

[![GitHub](https://img.shields.io/badge/GitHub-dxnz--id-181717?style=flat-square&logo=github)](https://github.com/dxnz-id)
[![Repo](https://img.shields.io/badge/Repo-PyBench-181717?style=flat-square&logo=github)](https://github.com/dxnz-id/pybench)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

> A cross-platform, terminal-based hardware benchmark tool written in Python.  
> Measures CPU, Memory, Disk, and GPU performance — with real-time system monitoring and structured JSON export.

---

## Overview

PyBench is a lightweight benchmark suite designed to stress-test and profile hardware components using pure Python and OpenCL. It provides reproducible, comparable results across machines with a clean terminal UI powered by [Rich](https://github.com/Textualize/rich).

---

## Features

| Module      | Tests                                                                                                               |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| **CPU**     | Single-thread math, multi-thread parallel, zlib compression, PBKDF2 encryption, prime sieve                         |
| **Memory**  | Sequential bandwidth, random access speed, memoryview copy speed, allocation stress                                 |
| **Disk**    | SEQ1M Q8T1 read/write, RND4K Q32T1 read/write, total IOPS                                                           |
| **GPU**     | OpenCL compute kernel (sqrt · log · sin), host↔device memory bandwidth                                              |
| **Monitor** | Real-time CPU %, frequency, RAM usage, GPU %, temperature, VRAM, disk I/O, network — with Avg / Min / Max / Std Dev |
| **Scoring** | Weighted score per module + overall composite score                                                                 |
| **Export**  | Full results saved as structured JSON with timestamp-based run ID                                                   |

---

## Demo

```text
╭──────────────────────────────────────────────────────────────╮
│                                                              │
│ PyBench                                                      │
│ --------------------------------------------                 │
│ Available Benchmarks:                                        │
│ 1. CPU Benchmark                                             │
│ 2. Memory Benchmark                                          │
│ 3. Disk Benchmark                                            │
│ 4. GPU Benchmark                                             │
│ --------------------------------------------                 │
│ Enter numbers separated by comma (e.g. 1,3) or 'all' to run. │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
Select benchmarks (e.g. 1,2,3) or 'all' (all): all

⠋ Running CPU Benchmark...      ████████████████████ 100%
⠋ Running Memory Benchmark...   ████████████████████ 100%
⠋ Running Disk Benchmark...     ████████████████████ 100%
⠋ Running GPU Benchmark...      ████████████████████ 100%

Benchmark Completed Successfully!

🔍 RAW BENCHMARK DETAILS
┌───────────┬─────────────────────────┬──────────────────┐
│ Component │ Test Case               │           Result │
├───────────┼─────────────────────────┼──────────────────┤
│ DISK      │ Sequential Read (Q8T1)  │        8.20 GB/s │
│ DISK      │ Sequential Write (Q8T1) │      626.00 MB/s │
│ DISK      │ Random Read (Q32T1)     │    40787.11 IOPS │
│ DISK      │ Random Write (Q32T1)    │    17604.28 IOPS │
│ MEMORY    │ Sequential Bandwidth    │        4.09 GB/s │
│ MEMORY    │ Random Access Speed     │     529,456 IOPS │
│ MEMORY    │ Memory Copy Speed       │        5.63 MB/s │
│ CPU       │ Multi-thread (Math)     │        9,882 Ops │
│ CPU       │ Single-thread (Math)    │        4,319 Ops │
│ GPU       │ Compute Performance     │      2.02 MOps/s │
│ GPU       │ VRAM Bandwidth          │              N/A │
└───────────┴─────────────────────────┴──────────────────┘

🏆 SCORE SUMMARY
┌───────────────┬───────────┐
│ Category      │     Score │
├───────────────┼───────────┤
│ CPU           │     9,260 │
│ MEMORY        │     4,594 │
│ DISK          │    70,520 │
│ GPU           │        10 │
│ OVERALL SCORE │    21,096 │
└───────────────┴───────────┘

📊 HARDWARE MONITORING SUMMARY
┌───────┬──────────────────────────────────────────────────┐
│ Group │ Metric Details (AVG / MIN-MAX)                   │
├───────┼──────────────────────────────────────────────────┤
│ CPU   │ Usage: 36.17% | Clock: 763MHz | Temp: 64.6°      │
│ RAM   │ Usage: 61.27% (61.1% - 61.9%)                    │
│ GPU   │ N/A (No GPU Sensor detected)                     │
└───────┴──────────────────────────────────────────────────┘

📂 Report: results/run_20260501_175030.json
```

---

## Project Structure

```text
pybench/
│
├── main.py                  # Entry point — CLI selector & benchmark runner
├── config.py                # Duration, thread count, result path settings
├── requirements.txt         # Standard pip dependencies
├── pyproject.toml           # Modern Python packaging (uv/build)
├── uv.lock                  # Lockfile for reproducible environments
├── CONTRIBUTING.md          # Guidelines for contributing to PyBench
├── CODE_OF_CONDUCT.md       # Rules for community behavior
│
├── modules/
│   ├── cpu_benchmark.py     # Single/multi-thread, compression, encryption, prime sieve
│   ├── memory_benchmark.py  # Bandwidth, latency, copy speed, allocation
│   ├── disk_benchmark.py    # Sequential & random I/O, IOPS
│   └── gpu_benchmark.py     # OpenCL compute kernel + VRAM bandwidth
│
├── monitor/
│   ├── system_monitor.py    # Background thread — polls psutil & nvidia-smi every 0.5s
│   └── aggregator.py        # Computes Avg / Min / Max / Std Dev from raw samples
│
├── scoring/
│   └── scorer.py            # Score formulas per module + overall composite
│
├── reporter/
│   └── exporter.py          # Serializes results to timestamped JSON
│
├── ui/
│   ├── dashboard.py         # Live stats panel (Rich Live)
│   ├── formatter.py         # Welcome screen & log helpers
│   └── results_view.py      # Final results table renderer
│
└── results/                 # Auto-created — stores run_YYYYMMDD_HHMMSS.json
```

---

## Installation

PyBench uses `uv` for lightning-fast and reproducible environment management.

**Requirements:** Python 3.12+, `uv` (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/dxnz-id/pybench.git
cd pybench

# 2. Setup environment and install dependencies
uv venv
uv sync

# 3. Run the application
uv run python main.py
```

*(Alternatively, you can use standard Python: `python -m venv .venv` and `pip install -r requirements.txt`)*

> **Note — OpenCL:** GPU benchmarking requires OpenCL drivers.
>
> - NVIDIA: install CUDA Toolkit
> - Intel / AMD integrated: install the vendor's OpenCL runtime
> - If OpenCL is unavailable, the GPU compute test falls back to a CPU scalar implementation automatically.

---

## Usage

```bash
# Run interactively (recommended)
python main.py

# Run with verbose logging
python main.py --verbose
```

At the prompt, enter the benchmarks you want to run:

```text
Select benchmarks (e.g. 1,2,3) or 'all' (all): all

1 → CPU Benchmark
2 → Memory Benchmark
3 → Disk Benchmark
4 → GPU Benchmark
all → Run everything
```

Results are automatically saved to `results/run_<timestamp>.json`.

---

## Benchmark Methodology

All tests use a **time-bounded loop** pattern: each sub-test runs for a fixed duration (`DEFAULT_DURATION`, default **10 seconds**) and scores by counting how many operations were completed — not by measuring how long a fixed task takes.

> **Intensity knobs & normalization.** Most benchmark classes expose constructor parameters that control how much work each unit does (e.g. `math_iters`, `compress_size`, `pbkdf2_iters`, `sieve_n` for CPU; buffer sizes for memory; `file_size`/thread counts for disk; the GPU kernel's inner-loop count). Raising a knob makes each iteration heavier, which lowers the raw completion count. To keep results comparable, count-based metrics are **normalized back to a fixed baseline of work-per-iteration**, so changing an intensity knob does not change the reported score on the same hardware. Metrics that are already rates (MB/s, GB/s, IOPS) are inherently intensity-invariant.

---



### CPU

Focuses on raw processor throughput across floating-point math, cryptography, compression, and parallel workloads. Each metric is normalized to a baseline work unit (see note above) so intensity settings don't skew scores.

**Single-thread** — Measures pure single-core performance by repeatedly executing an FPU-heavy loop (`sqrt · log · sin`) of length `math_iters` (default **5,000**). Stresses the Floating Point Unit (FPU) without any parallelism.

```python
def _math_workload(iterations):
    x = 0.0
    for i in range(1, iterations):
        x += math.sqrt(i) * math.log(i + 1) * math.sin(i)
    return x
```

**Multi-thread** — Dispatches the same workload across all logical cores via **`ProcessPoolExecutor`**. Using separate processes (not threads) sidesteps the GIL, so the work runs truly in parallel. The score is the sum of all worker completions, reflecting total multi-core throughput.

```python
with ProcessPoolExecutor(max_workers=cores) as ex:
    futures = [ex.submit(_math_worker, self.duration, self.math_iters)
               for _ in range(cores)]
    total = sum(f.result() for f in futures)
```

**Compression** — Repeatedly compresses a random buffer (`compress_size`, default **256 KB**) with `zlib` at level 6. Random data is near-incompressible, so this stresses the integer pipeline and memory manipulation.

**Encryption** — Runs `hashlib.pbkdf2_hmac(sha256)` with a configurable round count (`pbkdf2_iters`, default **1,000**) over a small fixed-size input. PBKDF2 pre-hashes its input once and then cost scales linearly with the iteration count, so iterations are used as the single intensity knob — making the metric cleanly normalizable.

**Prime Sieve** — Implements the Sieve of Eratosthenes up to `sieve_n` (default **1,000,000**) using a `bytearray`. Tests CPU branching logic and array traversal patterns.

```python
def sieve(n):
    s = bytearray([1]) * (n + 1)
    s[0] = s[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i*i::i] = bytearray(len(s[i*i::i]))
```

---

### Memory

Focuses on RAM throughput and latency — how fast the system can move large blocks of data and how quickly it responds to non-sequential access patterns.

**Sequential Bandwidth** — Allocates a large `bytearray` (`seq_buf_size`, default **512 MB**), copies it into a new buffer (write pass), then performs a read. Measures raw bulk transfer speed in MB/s.

```python
BUF_SIZE = self.seq_buf_size
buf2 = bytearray(BUF_SIZE)
buf2[:] = buf        # write pass
_ = buf2[0]          # read pass
total_bytes += BUF_SIZE * 2
```

**Random Access Speed** — Builds an index table sized to exceed the CPU cache (`rand_buf_size`, default **256 MB**) and performs **pointer chasing** — each read's value selects the next index — so the CPU cannot trivially prefetch and the loads actually reach main memory. The table is filled with a large prime stride (cheap O(n) build) to scatter accesses across pages. Result reported as dependent reads/s (IOPS).

```python
# next index = current slot's value → defeats prefetching
idx = buf[idx]
```

**Copy Speed** — Uses Python's `memoryview` to copy a large buffer (`copy_chunk`, default **256 MB**) directly at the memory level, minimizing Python object overhead. Reported in GB/s.

```python
mv_dst[:] = mv_src   # low-level bulk copy via memoryview
```

**Allocation Stress** — Continuously allocates and discards `bytearray` objects (`alloc_size`, default **1 MB**), then forces a `gc.collect()`. Tests OS memory management and the Python garbage collector under sustained pressure. Normalized to the baseline block size.

---

### Disk

Modeled after the **CrystalDiskMark** methodology. A temporary file (`CDM_test.tmp`, `file_size` default **1 GB**) is created before testing and deleted automatically on completion. Block sizes, queue depth (thread count), and file size are all configurable via the constructor.

| Sub-test        | Block Size       | Threads          | Use case simulated                               |
| --------------- | ---------------- | ---------------- | ------------------------------------------------ |
| **SEQ1M Q8T1**  | `seq_block` (1 MB) | `seq_threads` (8)  | Large file transfers (video, ISO, game installs) |
| **RND4K Q32T1** | `rnd_block` (4 KB) | `rnd_threads` (32) | OS boot, app launch, small file I/O (IOPS-bound) |

Sequential tests move through the file in ordered offsets. Random tests use `random.randint` to seek to arbitrary block-aligned positions, stressing the drive's IOPS capability. Queue depth is emulated with a thread pool (file I/O releases the GIL). All writes call `os.fsync()` to ensure data is committed to hardware rather than OS cache.

> **Defeating the page cache.** Because I/O is buffered, reads may be served from the OS page cache rather than the drive. Pass `exceed_ram=True` to grow the test file beyond physical RAM (≈1.5× RAM, detected via `psutil`) so the working set cannot be fully cached and reads measure the real device. Ensure the target directory has enough free space.

```python
# RND4K — random sector seek before every operation
pos = random.randint(0, self.file_size // block_size - 1) * block_size
f.seek(pos)
f.write(data)   # or f.read(block_size)
```

---

### GPU

Uses **PyOpenCL** to execute compute workloads on the GPU. If no OpenCL platform is detected, the compute test falls back to a CPU scalar loop automatically — `vram_bw` returns `null` in that case.

**GPU Compute** — Compiles and dispatches an OpenCL C kernel on-the-fly over a **16M-element** `float32` array in parallel across all GPU compute units. Each work-item runs an inner loop (`COMPUTE_INNER_ITERS`, default **256**) of `sqrt · log · sin` to raise arithmetic intensity and saturate the cores rather than being purely memory-bound. The kernel is retrieved once (via `cl.Kernel`) and reused across launches to avoid per-iteration overhead. Result is reported in **MOps/s**, normalized by the inner-loop count so the figure is invariant to the intensity setting.

```c
__kernel void compute(__global float* src, __global float* dst) {
    int i = get_global_id(0);
    float x = src[i];
    float acc = 0.0f;
    for (int k = 0; k < COMPUTE_INNER_ITERS; k++) {
        acc += sqrt(x) * log(x + 1.0f) * sin(x + k);
    }
    dst[i] = acc;
}
```

**VRAM Bandwidth** — Repeatedly transfers a 256 MB `float32` NumPy array from host RAM to device VRAM (`cl.Buffer` with `COPY_HOST_PTR`) and back (`cl.enqueue_copy`). Measures PCIe bus throughput and VRAM read/write speed in MB/s.

---

### System Monitor

A background daemon thread polls system state every `0.5s` for the entire duration of the benchmark run using `psutil`, `nvidia-smi` (via subprocess), and WMI fallbacks. Raw samples are collected into lists and aggregated into **Avg / Min / Max / Std Dev** by `monitor/aggregator.py` after the run completes. Monitored metrics include: CPU usage %, CPU frequency, RAM usage, GPU usage %, GPU temperature, VRAM used, disk I/O speed, and network throughput.

---

## Scoring System

Higher score = better performance. Scores are unitless integers calibrated so mid-range hardware scores roughly in the same order of magnitude across modules. The formulas are implemented in `scoring/scorer.py` (the active path used by `main.py`); each benchmark class also carries a matching `score()` static method for standalone use.

```
CPU Score    = single_ops + (multi_ops × 0.5)

Memory Score = (seq_bw × 0.4) + (copy_gb × 500) + (rand_lat / 5,000)

Disk Score   = (seq_total_MB × 0.05) + (rnd_total_IOPS × 1.2)

GPU Score    = (compute_MOps × 5) + (vram_bw_MB × 0.1)

Overall      = average of all modules with score > 0
```

Because every count-based metric is normalized to a fixed baseline of work-per-iteration, these scores remain comparable across runs **regardless of the intensity-knob settings** used, as long as `DEFAULT_DURATION` is the same.

> **Note:** `config.py` also defines `SCORING_WEIGHTS`, but the active scorer averages the module scores rather than applying those weights — the constant is retained for reference/future use.

---

## Output Format

Each run produces a JSON file in `results/` with the following structure:

```json
{
  "run_id": "20260428_122852",
  "timestamp": "Tue Apr 28 12:28:52 2026",
  "hardware": {
    "cpu": "13th Gen Intel(R) Core(TM) i5-13450HX",
    "cpu_cores": 10,
    "cpu_threads": 16,
    "cpu_base_clock": "2400.00 MHz",
    "ram": "11.71 GB",
    "gpu": "NVIDIA GeForce RTX 3050 6GB Laptop GPU",
    "gpu_vram": "6144.0 MB",
    "disk_total": "237.41 GB",
    "os": "Windows 11"
  },
  "system_monitor": {
    "cpu": { "avg": 20.32, "min": 0.0, "max": 73.7, "std_dev": 15.02 },
    "cpu_freq": {
      "avg": 2171.2,
      "min": 1520.0,
      "max": 2400.0,
      "std_dev": 386.97
    },
    "ram": { "avg": 59.56, "min": 57.0, "max": 63.6, "std_dev": 2.05 },
    "gpu": { "avg": 4.11, "min": 0.0, "max": 48.0, "std_dev": 9.59 },
    "gpu_temp": { "avg": 44.21, "min": 43.0, "max": 49.0, "std_dev": 1.77 }
  },
  "benchmark_results": {
    "cpu": {
      "single": 126391,
      "multi": 184701,
      "compress": 5843,
      "encrypt": 2506329,
      "prime": 45899
    },
    "memory": {
      "seq_bw": 4634.33,
      "rand_lat": 1430777.29,
      "copy": 8.23,
      "alloc": 3077.19
    },
    "disk": {
      "seq_write": 3566.22,
      "seq_read": 5960.72,
      "rand_write": 70188.45,
      "rand_read": 75401.3,
      "iops": 145589.76
    },
    "gpu": { "compute": 3545.31, "vram_bw": 1216.46, "opencl_ok": true }
  },
  "scores": {
    "cpu": 218741,
    "memory": 6254,
    "disk": 175184,
    "gpu": 17848,
    "overall": 104506
  }
}
```

---

## Dependencies

| Package        | Purpose                                          |
| -------------- | ------------------------------------------------ |
| `rich`         | Terminal UI — progress bars, live panels, tables |
| `psutil`       | CPU, RAM, and disk metrics                       |
| `nvidia-ml-py` | Hardware identification (NVML) in exporter.py    |
| `py-cpuinfo`   | Detailed CPU model information                   |
| `pyopencl`     | GPU compute kernel execution                     |
| `numpy`        | Array operations for GPU benchmark               |

---

## Limitations

- **CPU temperature** requires platform-specific drivers (e.g., OpenHardwareMonitor on Windows, `lm-sensors` on Linux). PyBench reports `null` if unavailable.
- **GPU monitoring** via `nvidia-smi` only supports NVIDIA GPUs. Intel/AMD integrated graphics are not monitored via this method (though hardware info might still be detected via OpenCL), and temperature/usage stats may fall back to WMI on Windows if `nvidia-smi` is unavailable.
- **Disk benchmark** creates a temporary file (1 GB by default, or ≈1.5× RAM with `exceed_ram=True`). Ensure the target directory has sufficient free space.
- **Multi-core CPU test** uses `ProcessPoolExecutor` to escape the GIL, so it reflects genuine parallel throughput across cores. The single-thread, compression, encryption, and prime tests still run pure-Python workloads, so absolute numbers reflect interpreter-level performance — consistent and comparable across machines on the same Python version, but not directly comparable to native-compiled tools.
- **Multiprocessing** requires the program to be launched via `python main.py` (the entry point is guarded by `if __name__ == "__main__"`), which is necessary for the "spawn" start method on Windows/macOS.
- **Score comparability** is valid between runs using the same `DEFAULT_DURATION`. Intensity-knob changes do **not** affect scores, since count-based metrics are normalized to a fixed baseline.

---

## Support the Developer

If you find PyBench useful and would like to support its development, you can buy me a coffee:

<a href="https://www.ko-fi.com/dxnzid">
  <img src="https://cdn.ko-fi.com/cdn/kofi3.png?v=3" width="160" alt="Support on Ko-fi" />
</a>

---

## Future Roadmap

1. **Detailed Reporting**: HTML / PDF export for benchmark results.
2. **Network Benchmark**: Latency and bandwidth tests for internet/LAN.
3. **Hardware Database**: Online leaderboard to compare your scores.
4. **macOS Support**: Adding Apple Silicon (M1/M2/M3) specific fallback sensors.

---

## Contributing

We welcome contributions from the community! Whether it's adding a new benchmark module, optimizing existing code, or fixing bugs, please read our [Contributing Guidelines](CONTRIBUTING.md) before opening a Pull Request to ensure your changes align with PyBench's architecture.

---

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

---

_PyBench is a hardware benchmarking utility built to explore and demonstrate systems-level programming performance in Python._  
_Results are relative benchmarks and should not be compared to native-compiled tools such as CrystalDiskMark, Cinebench, or 3DMark._  
_Disclaimer: This program was primarily written with the assistance of AI._
