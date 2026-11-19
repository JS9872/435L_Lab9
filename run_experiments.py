"""Run reproducible before/after experiments, preserving UTF-8 raw output.

Usage: python run_experiments.py [--skip-memory] [--coverage-only]
Memory profiling uses decorated call boundaries and periodic full-workload RSS sampling.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def run(arguments, output, env=None):
    print("Running:", sys.executable, *arguments, flush=True)
    process = subprocess.run([sys.executable, *arguments], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             env=env, encoding="utf-8", errors="replace")
    Path(output).write_text(process.stdout, encoding="utf-8")
    if process.returncode:
        print(process.stdout)
        raise SystemExit(process.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-memory", action="store_true")
    parser.add_argument("--coverage-only", action="store_true")
    args = parser.parse_args()
    for phase, suffix, module, tests in (
        ("before", "", "profiler", "test_profiler"),
        ("after", "_optimized", "profiler_optimized", "test_profiler_optimized"),
    ):
        directory = Path("results") / phase
        directory.mkdir(parents=True, exist_ok=True)
        if not args.coverage_only:
            run(["-m", "cProfile", "-s", "time", module + ".py"],
                directory / "cprofile.txt")
            run([f"profiler_lineprofiler{suffix}.py"], directory / "line_profiler.txt")
            if not args.skip_memory:
                run(["-m", "memory_profiler", f"profiler_memoryprofiler{suffix}.py"],
                    directory / "memory_profiler.txt")
            run(["-m", "unittest", "-v", tests], directory / "tests_unprofiled.txt")
        env = dict(os.environ, COVERAGE_FILE=f".coverage.{phase}")
        run(["-m", "coverage", "run", "--branch", "--source=" + module,
             "-m", "unittest", "-v", tests], directory / "tests.txt", env)
        run(["-m", "coverage", "report", "-m"], directory / "coverage.txt", env)
        run(["-m", "coverage", "html", "-d", f"htmlcov/{phase}"],
            directory / "coverage_html.txt", env)
        run(["-m", "coverage", "json", "-o", str(directory / "coverage.json")],
            directory / "coverage_json.txt", env)
    if not args.coverage_only:
        run(["benchmark.py"], "results/benchmark.txt")
    print("All requested experiments completed successfully.")


if __name__ == "__main__":
    main()
