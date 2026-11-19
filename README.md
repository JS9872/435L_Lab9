# EECE 435L — Lab 9: Profiling in Python

Joey Saade · Fall 2026–2027 · [435L_Lab9](https://github.com/JS9872/435L_Lab9)

## Submission

- `lab9_Joey_Saade.docx`: analysis and authentic terminal screenshots before/after optimization.
- Original code: `profiler.py`, `profiler_lineprofiler.py`, `profiler_memoryprofiler.py`, `test_profiler.py`.
- Optimized code: the corresponding `*_optimized.py` files.
- `htmlcov/before/index.html` and `htmlcov/after/index.html`: initial function-suite coverage, showing gaps.
- `htmlcov/index.html`: comprehensive final coverage after testing script entry points too.
- `results/`: full profiler outputs, test output, coverage JSON, and repeated benchmark measurements.
- `screenshots/`: actual Windows terminal captures displaying the preserved raw outputs, clearly labelled as saved-output views.

Keep each HTML coverage directory intact: `index.html` needs its accompanying assets and source pages.

## Reproduce

Python 3.12 was used. From this directory in PowerShell:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe run_experiments.py
```

The memory drivers use decorated call boundaries plus 10 ms RSS sampling over the complete workload. This avoids querying Windows RSS for more than 20 million individual loop-line events. Input sizes are **not reduced**. The line profiler still traces the original loops in full. For a run that omits memory profiling:

```powershell
./.venv/Scripts/python.exe run_experiments.py --skip-memory
```

Individual handout commands:

```powershell
./.venv/Scripts/python.exe -m cProfile -s time profiler.py
./.venv/Scripts/python.exe profiler_lineprofiler.py
./.venv/Scripts/python.exe -m memory_profiler profiler_memoryprofiler.py
./.venv/Scripts/python.exe -m unittest -v test_profiler
./.venv/Scripts/python.exe -m cProfile -s time profiler_optimized.py
./.venv/Scripts/python.exe profiler_lineprofiler_optimized.py
./.venv/Scripts/python.exe -m memory_profiler profiler_memoryprofiler_optimized.py
./.venv/Scripts/python.exe -m unittest -v test_profiler_optimized
./.venv/Scripts/python.exe benchmark.py
```

`python run_final_coverage.py` produces the final combined HTML report, including direct script execution. Use the virtual environment's Python for these commands.

## Design and interpretation

The original handout's broken indentation, duplicated excerpts, and `__name__` guards are repaired. The original functions still use 10,000, 100, and 10,000,000 iterations and a two-second sleep.

`optimized_fast_function()` uses the exact identity `n*(n-1)*(2*n-1)//6` for `n=100`. It produces `328350` without iteration or a collection. Every optimized entry point calls this replacement. The other two functions are shared with the original module to keep their workloads identical. The handout's optional generator expression is measured separately in `benchmark.py`.

The so-called memory-intensive function accumulates a scalar over a lazy `range`; it does not retain ten million objects. A positive before/after RSS delta is therefore not a valid correctness assertion. The tests report both readings and verify the exact numerical result instead. Memory-profiler function-entry “Increment” includes the existing process footprint; it is not memory newly allocated by the function. Its decorated thin wrappers measure call-boundary RSS; periodic sampling estimates peak RSS and may miss events shorter than the sampling interval. It does not claim per-iteration memory attribution.

The handout's five-second large-loop timing limit is reported as an observational target rather than a correctness assertion. The unchanged loop took 3.48 s in one ordinary run and 9.48 s in another; the literal failed assertion is preserved in `results/observations/handout_timing_failure.txt`. Coverage and line profiling add still more overhead. All exact-result assertions remain enforced. Repeated benchmark output retains every sample rather than claiming a speedup from one call. Optimizing this tiny function is not expected to materially change total runtime dominated by the sleep and large loop.

Initial coverage deliberately exposes script-entry gaps: imported unit tests call functions and mocked `main()` paths without executing the `__main__` call. The final coverage runner executes both real scripts and closes those gaps. Initial per-version reports target their respective modules; the final combined report includes both modules and their shared functions.

## Report utilities

`capture_terminal.py` uses Pillow and a native Windows console. `build_report.py` uses python-docx and Pillow; these report-only tools are separate from the profiling requirements. The report was rendered through installed Microsoft Word and checked as page images. No source handout or environment credentials are published.
