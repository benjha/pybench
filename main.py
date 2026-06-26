"""PyBench entry point.

Wires together the four benchmark modules, the scorer, and the JSON exporter,
then renders progress and final results in the terminal with Rich. Run with
``python main.py`` (add ``--verbose`` for per-test logging).
"""
import os
import argparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live

# Import our modules
from config import DEFAULT_DURATION, THREAD_COUNT, RESULTS_DIR
from modules.cpu_benchmark import CPUBenchmark
from modules.memory_benchmark import MemoryBenchmark
from modules.disk_benchmark import DiskBenchmark
from modules.gpu_benchmark import GPUBenchmark
from scoring.scorer import Scorer
from reporter.exporter import Exporter

# Import UI components
from ui.formatter import show_welcome
from ui.results_view import display_results

console = Console()
VERBOSE = False


def run_benchmark_cycle():
    """Run all four benchmarks once, then score, export, and display results.

    Each module is executed in sequence inside a Rich ``Live`` view that shows
    a progress bar. Afterwards the results are scored, written to a timestamped
    JSON report, and printed as summary tables.
    """
    results = {}

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )

    with Live(progress, refresh_per_second=10):
        task = progress.add_task(
            "[cyan]Running CPU Benchmark...", total=100)
        cpu_bench = CPUBenchmark(
            duration=DEFAULT_DURATION, threads=THREAD_COUNT)
        results['cpu'] = cpu_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

        task = progress.add_task(
            "[magenta]Running Memory Benchmark...", total=100)
        mem_bench = MemoryBenchmark(duration=DEFAULT_DURATION)
        results['memory'] = mem_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

        task = progress.add_task(
            "[yellow]Running Disk Benchmark...", total=100)
        disk_bench = DiskBenchmark(
            target_dir=RESULTS_DIR, duration=DEFAULT_DURATION)
        results['disk'] = disk_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

        task = progress.add_task(
            "[green]Running GPU Benchmark...", total=100)
        gpu_bench = GPUBenchmark(duration=DEFAULT_DURATION)
        results['gpu'] = gpu_bench.run_all(verbose=VERBOSE)
        progress.update(task, completed=100)

    # Process results
    scorer = Scorer()
    scores = scorer.get_full_breakdown(results)
    exporter = Exporter(output_dir=RESULTS_DIR)
    report_path = exporter.export(results, scores)

    display_results(results, scores, report_path)


def main():
    """Parse CLI arguments, clear the screen, and start a benchmark cycle."""
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
