"""Central configuration for PyBench.

Holds the shared paths and tunable defaults imported across the codebase
(benchmark duration, monitor sampling rate, thread count, scoring weights).
Importing this module also guarantees the results output directory exists.
"""
import os

# Base Directories
# BASE_DIR is the project root (the folder containing this file); all other
# paths are derived from it so the tool works regardless of the CWD.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Default settings
DEFAULT_DURATION = 10            # How long each individual sub-test runs, in seconds.
DEFAULT_RUNS = 1                 # Number of full benchmark passes (reserved for future use).
DEFAULT_MONITOR_INTERVAL = 0.5   # System-monitor sampling period, in seconds.
THREAD_COUNT = os.cpu_count() or 1  # Worker count for parallel CPU/disk tests.

# Relative weights for combining sub-scores into a composite figure.
# NOTE: the active scorer (scoring/scorer.py) currently averages module
# scores rather than using these weights; kept here for reference/future use.
SCORING_WEIGHTS = {
    "cpu": 0.35,
    "memory": 0.25,
    "disk": 0.20,
    "gpu": 0.20
}

# Ensure results directory exists so exporters can write without extra checks.
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
