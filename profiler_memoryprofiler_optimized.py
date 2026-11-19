"""Boundary and sampled peak RSS for the optimized full-size call path."""

from memory_profiler import memory_usage, profile
import profiler_optimized

@profile
def slow_function():
    return profiler_optimized.slow_function()


@profile
def optimized_fast_function():
    return profiler_optimized.optimized_fast_function()


@profile
def memory_intensive_function():
    return profiler_optimized.memory_intensive_function()


def main():
    slow_function()
    optimized_fast_function()
    memory_intensive_function()


if __name__ == "__main__":
    samples = memory_usage((main, (), {}), interval=0.01)
    print(f"Sampled RSS: start={samples[0]:.3f} MiB, "
          f"peak={max(samples):.3f} MiB, end={samples[-1]:.3f} MiB, "
          f"peak-start={max(samples)-samples[0]:.3f} MiB; "
          f"samples={len(samples)}, interval=0.01 s")
