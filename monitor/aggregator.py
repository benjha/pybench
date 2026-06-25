"""Aggregation of raw monitor samples into summary statistics."""
import statistics


def aggregate_metrics(metrics_list):
    """Reduce a list of monitor snapshots to per-metric summary stats.

    Extracts each metric's time series from the snapshots produced by
    ``SystemMonitor`` and computes avg/min/max/std-dev for each. CPU
    temperature samples of 0 (sensor unavailable) are dropped before
    aggregation. Returns ``{}`` for empty input.
    """
    if not metrics_list:
        return {}

    def get_stats(data):
        """Return avg/min/max/std-dev for a numeric series, or None if empty."""
        if not data:
            return None
        return {
            "avg": round(statistics.mean(data), 2),
            "min": round(min(data), 2),
            "max": round(max(data), 2),
            "std_dev": round(statistics.stdev(data), 2) if len(data) > 1 else 0
        }
    # Extract time series
    cpu_usage = [m['cpu']['usage'] for m in metrics_list]
    cpu_freq = [m['cpu']['frequency'] for m in metrics_list]
    cpu_temp = [m['cpu']['temp'] for m in metrics_list if m['cpu']['temp'] > 0]

    mem_usage = [m['memory']['usage'] for m in metrics_list]

    # GPU Aggregation
    gpu_usage = []
    gpu_temp = []
    gpu_vram = []
    if metrics_list[0]['gpu']:
        num_gpus = len(metrics_list[0]['gpu'])
        for i in range(num_gpus):
            # GPU samples come from per-snapshot nvidia-smi calls that can
            # intermittently fail/time out, leaving some snapshots with fewer
            # (or zero) GPU entries. Only read snapshots that have this index.
            gpu_usage.extend([m['gpu'][i]['usage'] for m in metrics_list if len(m['gpu']) > i])
            gpu_temp.extend([m['gpu'][i]['temp'] for m in metrics_list if len(m['gpu']) > i])
            gpu_vram.extend([m['gpu'][i]['vram_used'] for m in metrics_list if len(m['gpu']) > i])
    disk_read = [m['disk']['read_speed'] for m in metrics_list]
    disk_write = [m['disk']['write_speed'] for m in metrics_list]

    net_down = [m['network']['download'] for m in metrics_list]
    net_up = [m['network']['upload'] for m in metrics_list]
    return {
        "cpu": get_stats(cpu_usage),
        "cpu_freq": get_stats(cpu_freq),
        "cpu_temp": get_stats(cpu_temp),
        "ram": get_stats(mem_usage),
        "gpu": get_stats(gpu_usage),
        "gpu_temp": get_stats(gpu_temp),
        "gpu_vram": get_stats(gpu_vram),
        "disk_read": get_stats(disk_read),
        "disk_write": get_stats(disk_write),
        "network_download": get_stats(net_down),
        "network_upload": get_stats(net_up)
    }
