# Result JSON Schema

Dokumen ini menjelaskan seluruh field dalam file `results/run_<timestamp>.json` yang dihasilkan oleh PyBench.

---

## Top-Level Structure

```json
{
  "run_id": "20250611_143022",
  "timestamp": "Wed Jun 11 14:30:22 2026",
  "hardware": { },
  "system_monitor": { },
  "benchmark_results": { },
  "scores": { }
}
```

| Field               | Type     | Deskripsi                                            | Source                        |
| ------------------- | -------- | ---------------------------------------------------- | ----------------------------- |
| `run_id`            | `string` | ID unik berbasis timestamp (`%Y%m%d_%H%M%S`)         | `reporter/exporter.py:115`    |
| `timestamp`         | `string` | Waktu eksekusi dalam format `time.ctime()`           | `reporter/exporter.py:121`    |
| `hardware`          | `object` | Informasi spesifikasi hardware sistem                | `reporter/exporter.py:24-112` |
| `system_monitor`    | `object` | Statistik penggunaan sumber daya selama benchmark    | `monitor/aggregator.py:4-51`  |
| `benchmark_results` | `object` | Hasil numerik mentah dari benchmark yang dipilih     | `main.py`                     |
| `scores`            | `object` | Skor yang sudah dinormalisasi per komponen + overall | `scoring/scorer.py:32-53`     |

---

## 1. `hardware`

Disusun oleh method `get_hardware_info()` di `reporter/exporter.py`.

```json
{
  "cpu": "AMD Ryzen 7 5800X 8-Core Processor",
  "cpu_cores": 8,
  "cpu_threads": 16,
  "cpu_base_clock": "3800.00 MHz",
  "ram": "32.00 GB",
  "os": "Windows 10",
  "python_version": "3.11.4",
  "disk_total": "512.00 GB",
  "gpu": "NVIDIA GeForce RTX 3070",
  "gpu_vram": "8192.00 MB"
}
```

| Field            | Type      | Required | Contoh                                 | Deskripsi                                                                            |
| ---------------- | --------- | -------- | -------------------------------------- | ------------------------------------------------------------------------------------ |
| `cpu`            | `string`  | selalu   | `"AMD Ryzen 7 5800X 8-Core Processor"` | Nama/model CPU dari `cpuinfo.get_cpu_info()`, fallback `platform.processor()`        |
| `cpu_cores`      | `integer` | selalu   | `8`                                    | Jumlah core fisik via `psutil.cpu_count(logical=False)`                              |
| `cpu_threads`    | `integer` | selalu   | `16`                                   | Jumlah thread logis via `psutil.cpu_count(logical=True)`                             |
| `cpu_base_clock` | `string`  | selalu   | `"3800.00 MHz"`                        | Frekuensi CPU max (atau current) via `psutil.cpu_freq()`. Format `"{value:.2f} MHz"` |
| `ram`            | `string`  | selalu   | `"32.00 GB"`                           | Total RAM fisik. Format `"{round(GB,2)} GB"`                                         |
| `os`             | `string`  | selalu   | `"Windows 10"`                         | Nama OS + release via `platform.system()` + `platform.release()`                     |
| `python_version` | `string`  | selalu   | `"3.11.4"`                             | Versi Python via `platform.python_version()`                                         |
| `disk_total`     | `string`  | kadang   | `"512.00 GB"`                          | Total kapasitas disk partisi root. Tidak ada jika `psutil.disk_usage()` gagal        |
| `gpu`            | `string`  | selalu   | `"NVIDIA GeForce RTX 3070"`            | Nama GPU. Urutan deteksi: NVML → CUDA → WMI → lspci → `"No GPU found"`               |
| `gpu_vram`       | `string`  | kadang   | `"8192.00 MB"`                         | VRAM GPU (hanya ada saat NVML berhasil). Format `"{round(MB,2)} MB"`                 |

---

## 2. `system_monitor`

Dihasilkan oleh fungsi `aggregate_metrics()` di `monitor/aggregator.py` dari snapshot `SystemMonitor`.

Setiap sub-field mengikuti pola **statistics envelope**:

```json
{
  "avg": 45.23,
  "min": 10.0,
  "max": 95.5,
  "std_dev": 12.34
}
```

| Sub-field | Type     | Deskripsi                               |
| --------- | -------- | --------------------------------------- |
| `avg`     | `number` | Rata-rata aritmetik                     |
| `min`     | `number` | Nilai minimum teramati                  |
| `max`     | `number` | Nilai maksimum teramati                 |
| `std_dev` | `number` | Standar deviasi (0 jika data < 2 titik) |

### Semua Key `system_monitor`

| Key                | Kondisi               | Contoh                                                     | Sumber dari Snapshot                        |
| ------------------ | --------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| `cpu`              | selalu                | `{"avg":45.23,"min":10.0,"max":95.5,"std_dev":12.34}`      | `cpu.usage` — penggunaan CPU %              |
| `cpu_freq`         | selalu                | `{"avg":3600.5,"min":2200.0,"max":4700.0,"std_dev":350.1}` | `cpu.frequency` — frekuensi CPU MHz         |
| `cpu_temp`         | selalu                | `{"avg":72.5,"min":45.0,"max":90.0,"std_dev":8.5}`         | `cpu.temp` — suhu CPU °C (hanya nilai > 0)  |
| `ram`              | selalu                | `{"avg":65.3,"min":55.0,"max":80.0,"std_dev":5.2}`         | `memory.usage` — penggunaan RAM %           |
| `gpu`              | `null` jika tanpa GPU | `{"avg":60.0,"min":0.0,"max":100.0,"std_dev":30.0}`        | `gpu[0].usage` — penggunaan GPU %           |
| `gpu_temp`         | `null` jika tanpa GPU | `{"avg":68.5,"min":40.0,"max":85.0,"std_dev":10.2}`        | `gpu[0].temp` — suhu GPU °C                 |
| `gpu_vram`         | `null` jika tanpa GPU | `{"avg":2048.0,"min":512.0,"max":4096.0,"std_dev":800.0}`  | `gpu[0].vram_used` — VRAM terpakai MB       |
| `disk_read`        | selalu                | `{"avg":1.5e8,"min":0.0,"max":5.0e8,"std_dev":1.0e8}`      | `disk.read_speed` — baca disk bytes/detik   |
| `disk_write`       | selalu                | `{"avg":8.0e7,"min":0.0,"max":3.0e8,"std_dev":5.0e7}`      | `disk.write_speed` — tulis disk bytes/detik |
| `network_download` | selalu                | `{"avg":5.0e6,"min":0.0,"max":1.5e7,"std_dev":3.0e6}`      | `network.download` — download bytes/detik   |
| `network_upload`   | selalu                | `{"avg":1.0e6,"min":0.0,"max":5.0e6,"std_dev":8.0e5}`      | `network.upload` — upload bytes/detik       |

> **Catatan:** Key `gpu`, `gpu_temp`, `gpu_vram` tetap ada tetapi bernilai `null` jika tidak ada sensor GPU. Key lainnya selalu ada (tapi isinya bisa `null` jika tidak ada data).

### Struktur Raw Snapshot (sebelum agregasi)

Setiap snapshot dalam list `Monitor.metrics`:

```json
{
  "timestamp": 1749631822.5,
  "cpu": {
    "usage": 45.2,
    "frequency": 3600.0,
    "cores": [40.0, 35.0, 60.0],
    "temp": 72.3
  },
  "memory": {
    "used": 8192.0,
    "available": 24576.0,
    "usage": 65.3
  },
  "gpu": [
    {
      "usage": 60.0,
      "vram_used": 2048.0,
      "vram_total": 0,
      "temp": 68.5,
      "power": 0,
      "name": "GPU"
    }
  ],
  "disk": {
    "read_speed": 150000000.0,
    "write_speed": 80000000.0
  },
  "network": {
    "download": 5000000.0,
    "upload": 1000000.0
  }
}
```

---

## 3. `benchmark_results`

Key dalam objek ini **hanya ada** jika benchmark yang bersangkutan dijalankan (dipilih user).

### 3a. CPU (`"cpu"`)

**Source:** `modules/cpu_benchmark.py`, method `run_all()`

```json
{
  "single": 15420,
  "multi": 89750,
  "compress": 480,
  "encrypt": 120,
  "prime": 250
}
```

| Field      | Type      | Contoh  | Deskripsi                                                          |
| ---------- | --------- | ------- | ------------------------------------------------------------------ |
| `single`   | `integer` | `15420` | Operasi matematika single-thread (sqrt+log+sin) dalam durasi tetap |
| `multi`    | `integer` | `89750` | Operasi matematika multi-thread (semua CPU threads)                |
| `compress` | `integer` | `480`   | Operasi `zlib.compress()` pada data acak 64KB                      |
| `encrypt`  | `integer` | `120`   | Iterasi `hashlib.pbkdf2_hmac("sha256")` pada data 64KB             |
| `prime`    | `integer` | `250`   | Pass lengkap Sieve of Eratosthenes (n=100000)                      |

### 3b. Memory (`"memory"`)

**Source:** `modules/memory_benchmark.py`, method `run_all()`

```json
{
  "seq_bw": 8500.42,
  "rand_lat": 3200000.0,
  "copy": 45.23,
  "alloc": 3500.0
}
```

| Field      | Type    | Contoh      | Deskripsi                                                       |
| ---------- | ------- | ----------- | --------------------------------------------------------------- |
| `seq_bw`   | `float` | `8500.42`   | Bandwidth sequential read+write (MB/s) — copy `bytearray` 128MB |
| `rand_lat` | `float` | `3200000.0` | Random 8-byte access IOPS dari buffer float 64MB                |
| `copy`     | `float` | `45.23`     | Kecepatan copy memory (GB/s) via `memoryview` buffer 256MB      |
| `alloc`    | `float` | `3500.0`    | Siklus alokasi+dealokasi per detik `bytearray` 1MB              |

### 3c. Disk (`"disk"`)

**Source:** `modules/disk_benchmark.py`, method `run_all()`

```json
{
  "seq_write": 3200.5,
  "seq_read": 5500.2,
  "rand_write": 45000.0,
  "rand_read": 72000.0,
  "iops": 117000.0
}
```

| Field        | Type    | Contoh     | Deskripsi                                 |
| ------------ | ------- | ---------- | ----------------------------------------- |
| `seq_write`  | `float` | `3200.5`   | Sequential write (MB/s), 1MB blocks, Q8T1 |
| `seq_read`   | `float` | `5500.2`   | Sequential read (MB/s), 1MB blocks, Q8T1  |
| `rand_write` | `float` | `45000.0`  | Random write IOPS, 4KB blocks, Q32T1      |
| `rand_read`  | `float` | `72000.0`  | Random read IOPS, 4KB blocks, Q32T1       |
| `iops`       | `float` | `117000.0` | Dihitung sebagai `rand_read + rand_write` |

### 3d. GPU (`"gpu"`)

**Source:** `modules/gpu_benchmark.py`, method `run_all()`

```json
{
  "compute": 850.75,
  "vram_bw": 12000.0,
  "cuda_ok": true
}
```

| Field       | Type                | Contoh    | Deskripsi                                                                             |
| ----------- | ------------------- | --------- | ------------------------------------------------------------------------------------- |
| `compute`   | `float`             | `850.75`  | Throughput komputasi (MOps/s) — kernel CUDA sqrt+log+sin 1M floats, atau fallback CPU |
| `vram_bw`   | `float` atau `null` | `12000.0` | Bandwidth VRAM (MB/s). `null` jika CUDA tidak tersedia/gagal                          |
| `cuda_ok`   | `boolean`           | `true`    | Apakah CUDA berhasil diinisialisasi                                                    |

---

## 4. `scores`

Dihitung oleh `Scorer.get_full_breakdown()` di `scoring/scorer.py`.

```json
{
  "cpu": 60305,
  "memory": 4100,
  "disk": 490,
  "gpu": 5454,
  "overall": 17587
}
```

| Field     | Type      | Contoh  | Formula                                                                     | Deskripsi            |
| --------- | --------- | ------- | --------------------------------------------------------------------------- | -------------------- |
| `cpu`     | `integer` | `60305` | `single + multi * 0.5` (0 jika tidak di-benchmark)                          | Skor performa CPU    |
| `memory`  | `integer` | `4100`  | `seq_bw * 0.4 + copy * 500 + rand_lat / 5000` (0 jika tidak)                | Skor performa memori |
| `disk`    | `integer` | `490`   | `(seq_read+seq_write) * 0.05 + (rand_read+rand_write) * 1.2` (0 jika tidak) | Skor performa disk   |
| `gpu`     | `integer` | `5454`  | `compute * 5 + vram_bw * 0.1` (0 jika tidak)                                | Skor performa GPU    |
| `overall` | `integer` | `17587` | `rata-rata(sub_scores)` hanya dari komponen dengan skor > 0                 | Skor overall         |

> **Catatan:** Komponen yang tidak di-benchmark mendapat skor `0`. `overall` hanya merata-rata komponen dengan skor > 0.

---

## Ringkasan Field Opsional / Kondisional

| Top-level Key           | Sub-field                     | Kondisi Tidak Ada                                                    |
| ----------------------- | ----------------------------- | -------------------------------------------------------------------- |
| `benchmark_results`     | `cpu`                         | Hanya ada jika user memilih benchmark `1`                            |
| `benchmark_results`     | `memory`                      | Hanya ada jika user memilih benchmark `2`                            |
| `benchmark_results`     | `disk`                        | Hanya ada jika user memilih benchmark `3`                            |
| `benchmark_results`     | `gpu`                         | Hanya ada jika user memilih benchmark `4`                            |
| `hardware`              | `disk_total`                  | Tidak ada jika `psutil.disk_usage()` gagal                           |
| `hardware`              | `gpu_vram`                    | Tidak ada jika NVML gagal (tanpa GPU NVIDIA / tanpa `pynvml`)        |
| `system_monitor`        | `gpu`, `gpu_temp`, `gpu_vram` | Bernilai `null` (bukan tidak ada) saat tanpa sensor GPU              |
| `benchmark_results.gpu` | `vram_bw`                     | Bernilai `null` saat CUDA tidak tersedia atau test bandwidth gagal   |

---

## Data Flow

```
run_benchmark_cycle(selections)
  │
  ├─ monitor = SystemMonitor(interval=0.5)
  │     .start()                          → mengumpulkan snapshot tiap 0.5 detik
  │     .get_metrics()                    → list[snapshot]
  │
  ├─ results = {}
  │     results['cpu']    = CPUBenchmark.run_all()
  │     results['memory'] = MemoryBenchmark.run_all()
  │     results['disk']   = DiskBenchmark.run_all()
  │     results['gpu']    = GPUBenchmark.run_all()
  │
  ├─ metrics = monitor.get_metrics()
  ├─ summary_metrics = aggregate_metrics(metrics)    → system_monitor
  │
  ├─ scorer = Scorer()
  ├─ scores = scorer.get_full_breakdown(results)     → scores
  │
  ├─ exporter = Exporter(output_dir="results")
  └─ exporter.export(results, summary_metrics, scores)
       → menghasilkan results/run_{run_id}.json
```

---

## Contoh JSON Lengkap

```json
{
  "run_id": "20250611_143022",
  "timestamp": "Wed Jun 11 14:30:22 2026",
  "hardware": {
    "cpu": "AMD Ryzen 7 5800X 8-Core Processor",
    "cpu_cores": 8,
    "cpu_threads": 16,
    "cpu_base_clock": "3800.00 MHz",
    "ram": "32.00 GB",
    "os": "Windows 10",
    "python_version": "3.11.4",
    "disk_total": "512.00 GB",
    "gpu": "NVIDIA GeForce RTX 3070",
    "gpu_vram": "8192.00 MB"
  },
  "system_monitor": {
    "cpu": { "avg": 45.23, "min": 10.0, "max": 95.5, "std_dev": 12.34 },
    "cpu_freq": { "avg": 3600.5, "min": 2200.0, "max": 4700.0, "std_dev": 350.1 },
    "cpu_temp": { "avg": 72.5, "min": 45.0, "max": 90.0, "std_dev": 8.5 },
    "ram": { "avg": 65.3, "min": 55.0, "max": 80.0, "std_dev": 5.2 },
    "gpu": { "avg": 60.0, "min": 0.0, "max": 100.0, "std_dev": 30.0 },
    "gpu_temp": { "avg": 68.5, "min": 40.0, "max": 85.0, "std_dev": 10.2 },
    "gpu_vram": { "avg": 2048.0, "min": 512.0, "max": 4096.0, "std_dev": 800.0 },
    "disk_read": { "avg": 150000000.0, "min": 0.0, "max": 500000000.0, "std_dev": 100000000.0 },
    "disk_write": { "avg": 80000000.0, "min": 0.0, "max": 300000000.0, "std_dev": 50000000.0 },
    "network_download": { "avg": 5000000.0, "min": 0.0, "max": 15000000.0, "std_dev": 3000000.0 },
    "network_upload": { "avg": 1000000.0, "min": 0.0, "max": 5000000.0, "std_dev": 800000.0 }
  },
  "benchmark_results": {
    "cpu": {
      "single": 15420,
      "multi": 89750,
      "compress": 480,
      "encrypt": 120,
      "prime": 250
    },
    "memory": {
      "seq_bw": 8500.42,
      "rand_lat": 3200000.0,
      "copy": 45.23,
      "alloc": 3500.0
    },
    "disk": {
      "seq_write": 3200.5,
      "seq_read": 5500.2,
      "rand_write": 45000.0,
      "rand_read": 72000.0,
      "iops": 117000.0
    },
    "gpu": {
      "compute": 850.75,
      "vram_bw": 12000.0,
      "cuda_ok": true
    }
  },
  "scores": {
    "cpu": 60305,
    "memory": 4100,
    "disk": 490,
    "gpu": 5454,
    "overall": 17587
  }
}
```
