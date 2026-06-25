"""Background system telemetry sampler.

``SystemMonitor`` is a daemon thread that polls hardware metrics (CPU, RAM,
GPU, disk, network) at a fixed interval while benchmarks run, storing a
timestamped snapshot per sample. Disk and network figures are computed as
deltas between samples to yield per-second rates. CPU temperature and GPU
stats are gathered via several platform-specific fallbacks and degrade
gracefully to 0/None when no sensor is available.
"""
import time
import threading
import psutil
import platform
import subprocess
import re


class SystemMonitor(threading.Thread):
    """Daemon thread that samples system metrics into ``self.metrics``.

    Args:
        interval: Seconds between samples.
    """

    def __init__(self, interval=1.0):
        super().__init__()
        self.interval = interval
        self._stop_event = threading.Event()
        self.metrics = []
        self.daemon = True

    @staticmethod
    def _get_cpu_temp():
        """Return CPU temperature in °C, or 0 if unavailable.

        Tries, in order: psutil sensors, Linux thermal-zone sysfs files, the
        ``sensors`` CLI, then Windows WMI (OpenHardwareMonitor, then the
        generic thermal-zone counter). Each source is best-effort.
        """
        try:
            temps = psutil.sensors_temperatures()
            for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz", "zenpower"):
                if key in temps and temps[key]:
                    return temps[key][0].current
        except Exception:
            pass

        if platform.system() == "Linux":
            try:
                import glob
                zones = glob.glob("/sys/class/thermal/thermal_zone*/temp")
                readings = []
                for z in zones:
                    with open(z) as f:
                        t = int(f.read().strip()) / 1000.0
                    if 10.0 < t < 110.0:
                        readings.append(t)
                if readings:
                    return max(readings)
            except Exception:
                pass

            try:
                out = subprocess.check_output(["sensors"], text=True, timeout=3,
                                              stderr=subprocess.DEVNULL)
                m = re.search(r"(?:Core 0|Tdie|Tctl).*?\+(\d+\.\d+)\s*°C", out)
                if m:
                    return float(m.group(1))
            except Exception:
                pass

        if platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                for sensor in w.Sensor():
                    if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                        return float(sensor.Value)
            except Exception:
                pass

            try:
                import wmi
                w = wmi.WMI(namespace="root\\cimv2")
                for item in w.Win32_PerfFormattedData_Counters_ThermalZoneInformation():
                    t = (float(item.Temperature) - 2732) / 10.0
                    if 10.0 < t < 110.0:
                        return t
            except Exception:
                pass

        return 0

    @staticmethod
    def _get_gpu_stats():
        """Return (usage%, temp°C, vram_mb), or (None, None, None) if no GPU.

        Prefers ``nvidia-smi``; on Windows falls back to OpenHardwareMonitor
        via WMI. Non-NVIDIA GPUs without those sensors return all-None.
        """
        try:
            out = subprocess.check_output(
                ["nvidia-smi",
                 "--query-gpu=utilization.gpu,temperature.gpu,memory.used",
                 "--format=csv,noheader,nounits"],
                text=True, timeout=3, stderr=subprocess.DEVNULL)
            parts = out.strip().split(",")
            if len(parts) >= 3:
                return float(parts[0]), float(parts[1]), float(parts[2])
        except Exception:
            pass

        if platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                usage = temp = vram = None
                for s in w.Sensor():
                    n = s.Name.lower()
                    if s.SensorType == "Load" and "gpu" in n:
                        usage = float(s.Value)
                    elif s.SensorType == "Temperature" and "gpu" in n:
                        temp = float(s.Value)
                    elif s.SensorType == "SmallData" and "gpu memory used" in n:
                        vram = float(s.Value)
                if any(v is not None for v in (usage, temp, vram)):
                    return usage, temp, vram
            except Exception:
                pass

        return None, None, None

    def stop(self):
        """Signal the sampling loop to exit after its current iteration."""
        self._stop_event.set()

    def run(self):
        """Sampling loop: snapshot metrics every ``interval`` until stopped.

        Disk and network throughput are derived from the byte-counter delta
        since the previous sample divided by the elapsed time.
        """
        last_net = psutil.net_io_counters()
        last_disk = psutil.disk_io_counters()
        last_time = time.time()

        while not self._stop_event.is_set():
            current_time = time.time()
            dt = current_time - last_time
            if dt <= 0:
                dt = 0.1

            # CPU
            cpu_usage = psutil.cpu_percent(interval=None)
            cpu_freq_obj = psutil.cpu_freq()
            cpu_freq = cpu_freq_obj.current if cpu_freq_obj else 0
            cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
            cpu_temp = self._get_cpu_temp()

            # RAM
            mem = psutil.virtual_memory()

            # GPU
            gpu_u, gpu_t, gpu_v = self._get_gpu_stats()
            gpu_data = []
            if gpu_u is not None:
                gpu_data.append({
                    "usage": gpu_u,
                    "vram_used": gpu_v if gpu_v is not None else 0,
                    "vram_total": 0,
                    "temp": gpu_t if gpu_t is not None else 0,
                    "power": 0,
                    "name": "GPU"
                })

            # Disk
            curr_disk = psutil.disk_io_counters()
            disk_read_speed = (curr_disk.read_bytes -
                               last_disk.read_bytes) / dt
            disk_write_speed = (curr_disk.write_bytes -
                                last_disk.write_bytes) / dt

            # Network
            curr_net = psutil.net_io_counters()
            net_download = (curr_net.bytes_recv - last_net.bytes_recv) / dt
            net_upload = (curr_net.bytes_sent - last_net.bytes_sent) / dt

            snapshot = {
                "timestamp": current_time,
                "cpu": {
                    "usage": cpu_usage,
                    "frequency": cpu_freq,
                    "cores": cpu_cores,
                    "temp": cpu_temp
                },
                "memory": {
                    "used": mem.used / (1024**2),
                    "available": mem.available / (1024**2),
                    "usage": mem.percent
                },
                "gpu": gpu_data,
                "disk": {
                    "read_speed": disk_read_speed,
                    "write_speed": disk_write_speed
                },
                "network": {
                    "download": net_download,
                    "upload": net_upload
                }
            }

            self.metrics.append(snapshot)

            last_net = curr_net
            last_disk = curr_disk
            last_time = current_time

            time.sleep(self.interval)

    def get_latest_snapshot(self):
        """Return the most recent sample dict, or None if none collected yet."""
        return self.metrics[-1] if self.metrics else None

    def get_metrics(self):
        """Return the full list of collected per-sample snapshots."""
        return self.metrics
