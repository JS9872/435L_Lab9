"""Profile full workloads at call boundaries and sample RSS every 10 ms.

Thin decorated wrappers avoid millions of slow Windows RSS queries inside loops.
The sampled peak also detects transient changes that before/after readings miss.
"""

from memory_profiler import memory_usage, profile
import profiler

@profile
def slow_function():
    return profiler.slow_function()


@profile
def fast_function():
    return profiler.fast_function()


@profile
def memory_intensive_function():
    return profiler.memory_intensive_function()


def main():
    slow_function()
    fast_function()
    memory_intensive_function()


if __name__ == "__main__":
    samples = memory_usage((main, (), {}), interval=0.01)
    print(f"Sampled RSS: start={samples[0]:.3f} MiB, "
          f"peak={max(samples):.3f} MiB, end={samples[-1]:.3f} MiB, "
          f"peak-start={max(samples)-samples[0]:.3f} MiB; "
          f"samples={len(samples)}, interval=0.01 s")
