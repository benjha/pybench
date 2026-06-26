"""Final results rendering: detail, score, and monitoring summary tables."""
from rich.table import Table
from rich.console import Console
from ui.formatter import mb_format

console = Console()


def display_results(results, scores, report_path):
    """Print the results and score summary tables plus the saved report path.

    Renders raw per-test results and the score summary. Only sections present
    in ``results`` are shown, so partial runs display cleanly.

    Args:
        results: Raw per-module benchmark results.
        scores: Per-module and overall scores.
        report_path: Path to the exported JSON report.
    """
    console.print(
        "\n[bold green]Benchmark Completed Successfully![/bold green]")

    # 1. DETAILED RESULTS TABLE
    detail_table = Table(title="🔍 RAW BENCHMARK DETAILS",
                         header_style="bold yellow", border_style="bright_blue")
    detail_table.add_column("Component", style="cyan")
    detail_table.add_column("Test Case", style="white")
    detail_table.add_column("Result", justify="right", style="bold green")

    if 'disk' in results:
        d = results['disk']
        detail_table.add_row("DISK", "Sequential Read (Q8T1)",
                             mb_format(d.get('seq_read', 0)))
        detail_table.add_row("DISK", "Sequential Write (Q8T1)",
                             mb_format(d.get('seq_write', 0)))
        detail_table.add_row("DISK", "Random Read (Q32T1)",
                             f"{d.get('rand_read', 0):.2f} IOPS")
        detail_table.add_row("DISK", "Random Write (Q32T1)",
                             f"{d.get('rand_write', 0):.2f} IOPS")
        detail_table.add_section()

    if 'memory' in results:
        m = results['memory']
        detail_table.add_row("MEMORY", "Sequential Bandwidth",
                             mb_format(m.get('seq_bw', 0)))
        detail_table.add_row("MEMORY", "Random Access Speed",
                             f"{m.get('rand_lat', 0):,.0f} IOPS")
        detail_table.add_row("MEMORY", "Memory Copy Speed",
                             f"{m.get('copy', 0):.2f} GB/s")
        detail_table.add_section()

    if 'cpu' in results:
        c = results['cpu']
        detail_table.add_row("CPU", "Multi-thread (Math)",
                             f"{c.get('multi', 0):,} Ops")
        detail_table.add_row("CPU", "Single-thread (Math)",
                             f"{c.get('single', 0):,} Ops")
        detail_table.add_section()

    if 'gpu' in results:
        g = results['gpu']
        comp = g.get('compute')
        vram = g.get('vram_bw')
        detail_table.add_row("GPU", "Compute Performance",
                             f"{comp:.2f} MOps/s" if comp is not None else "N/A")
        detail_table.add_row("GPU", "VRAM Bandwidth", mb_format(
            vram) if vram is not None else "N/A")
        detail_table.add_section()

    console.print(detail_table)

    # 2. SCORES TABLE
    score_table = Table(title="🏆 SCORE SUMMARY",
                        header_style="bold magenta", border_style="bright_blue")
    score_table.add_column("Category", style="cyan")
    score_table.add_column("Score", justify="right", style="bold yellow")

    for cat in ['cpu', 'memory', 'disk', 'gpu']:
        if cat in scores:
            score_table.add_row(cat.upper(), f"{scores[cat]:,}")
    score_table.add_section()
    score_table.add_row("[bold green]OVERALL SCORE[/]",
                        f"[bold green]{scores.get('overall', 0):,}[/]")
    console.print(score_table)

    console.print(f"\n[bold white]📂 Report:[/] [dim]{report_path}[/dim]")
