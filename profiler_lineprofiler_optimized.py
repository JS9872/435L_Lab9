"""Line-by-line profiling after replacing fast_function in the call path."""

from line_profiler import LineProfiler
from profiler_optimized import (
    main, memory_intensive_function, optimized_fast_function, slow_function,
)


def profile_main():
    profiler = LineProfiler(
        slow_function, optimized_fast_function, memory_intensive_function,
    )
    profiler.runcall(main)
    profiler.print_stats()


if __name__ == "__main__":
    profile_main()
