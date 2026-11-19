"""Close entry-point gaps and generate combined source coverage."""

from pathlib import Path
import os

from run_experiments import run


def main():
    target = Path("results/final")
    target.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, COVERAGE_FILE=".coverage.final")
    source = "--source=profiler,profiler_optimized"
    run(["-m", "coverage", "run", "--branch", source, "-m", "unittest", "discover", "-v"],
        target / "tests.txt", env)
    for module in ("profiler", "profiler_optimized"):
        run(["-m", "coverage", "run", "--append", "--branch", source, module + ".py"],
            target / (module + "_entrypoint.txt"), env)
    run(["-m", "coverage", "report", "-m"], target / "coverage.txt", env)
    run(["-m", "coverage", "html", "-d", "htmlcov"], target / "coverage_html.txt", env)
    run(["-m", "coverage", "json", "-o", str(target / "coverage.json")],
        target / "coverage_json.txt", env)


if __name__ == "__main__":
    main()
