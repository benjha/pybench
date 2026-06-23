import os
import argparse
from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live

# Import our modules
from config import DEFAULT_DURATION, THREAD_COUNT, RESULTS_DIR, DEFAULT_MONITOR_INTERVAL
from monitor.system_monitor import SystemMonitor
from monitor.aggregator import aggregate_metrics
from modules.cpu_benchmark import CPUBenchmark
from modules.memory_benchmark import MemoryBenchmark
from modules.disk_benchmark import DiskBenchmark
from modules.gpu_benchmark import GPUBenchmark
from scoring.scorer import Scorer
from reporter.exporter import Exporter

# Import UI components
from ui.formatter import show_welcome
from ui.dashboard import StatsDisplay
from ui.results_view import display_results

console = Console()
VERBOSE = False


def run_benchmark_cycle():
    monitor = SystemMonitor(interval=DEFAULT_MONITOR_INTERVAL)
    monitor.start()

    results = {}
    stats_display = StatsDisplay(monitor)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )

    # Sync UI refresh rate with monitor interval (at least 4 times per second for smoothness)
    ui_refresh_rate = max(4, int(1 / DEFAULT_MONITOR_INTERVAL))

    with Live(Group(progress, stats_display), refresh_per_second=ui_refresh_rate):
        stats_display.active_component = "CPU"
        task = progress.add_task(
            "[cyan]Running CPU Benchmark...", total=100)
        cpu_bench = CPUBenchmark(
            duration=DEFAULT_DURATION, threads=THREAD_COUNT)
        results['cpu'] = cpu_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

        stats_display.active_component = "MEMORY"
        task = progress.add_task(
            "[magenta]Running Memory Benchmark...", total=100)
        mem_bench = MemoryBenchmark(duration=DEFAULT_DURATION)
        results['memory'] = mem_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

        stats_display.active_component = "DISK"
        task = progress.add_task(
            "[yellow]Running Disk Benchmark...", total=100)
        disk_bench = DiskBenchmark(
            target_dir=RESULTS_DIR, duration=DEFAULT_DURATION)
        results['disk'] = disk_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

        stats_display.active_component = "GPU"
        task = progress.add_task(
            "[green]Running GPU Benchmark...", total=100)
        gpu_bench = GPUBenchmark(duration=DEFAULT_DURATION)
        results['gpu'] = gpu_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

    monitor.stop()
    monitor.join()

    # Process results
    metrics = monitor.get_metrics()
    summary_metrics = aggregate_metrics(metrics)
    scorer = Scorer()
    scores = scorer.get_full_breakdown(results)
    exporter = Exporter(output_dir=RESULTS_DIR)
    report_path = exporter.export(results, summary_metrics, scores)

    display_results(results, scores, summary_metrics, report_path)


def main():
    global VERBOSE
    parser = argparse.ArgumentParser(
        description="PyBench - Python Benchmark Tool")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display detailed logs")
    args = parser.parse_args()
    VERBOSE = args.verbose

    os.system('cls' if os.name == 'nt' else 'clear')
    show_welcome()
    run_benchmark_cycle()


if __name__ == "__main__":
    main()
