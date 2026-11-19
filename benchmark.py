"""Repeated unprofiled timings; profiler overhead is not an application speedup."""

import json
import platform
import statistics
import sys
import timeit
from importlib.metadata import version
from pathlib import Path

import profiler
import profiler_optimized


def generator_candidate():
    return sum(i ** 2 for i in range(100))


def main():
    results = {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {name: version(name) for name in
                     ("line_profiler", "memory_profiler", "coverage", "psutil")},
        "method": "7 repeats x 100000 calls for fast functions; 3 x 1 for main; median",
    }
    for label, func in (("original_fast", profiler.fast_function),
                        ("generator_candidate", generator_candidate),
                        ("optimized_fast", profiler_optimized.optimized_fast_function)):
        assert func() == 328350
        samples = timeit.repeat(func, number=100000, repeat=7)
        results[label] = {"seconds_per_call": [x / 100000 for x in samples],
                          "median_seconds": statistics.median(samples) / 100000}
    for label, func in (("original_main", profiler.main),
                        ("optimized_main", profiler_optimized.main)):
        samples = timeit.repeat(func, number=1, repeat=3)
        results[label] = {"seconds_per_call": samples,
                          "median_seconds": statistics.median(samples)}
    results["fast_speedup"] = (results["original_fast"]["median_seconds"] /
                               results["optimized_fast"]["median_seconds"])
    results["main_speedup"] = (results["original_main"]["median_seconds"] /
                               results["optimized_main"]["median_seconds"])
    Path("results").mkdir(exist_ok=True)
    Path("results/benchmark.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
