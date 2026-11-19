"""Optimize fast_function only; preserve the other workloads for comparison."""

from profiler import memory_intensive_function, slow_function


def optimized_fast_function():
    """Sum squares for range(100) in constant time using the exact identity."""
    n = 100
    return n * (n - 1) * (2 * n - 1) // 6


def main():
    slow_function()
    optimized_fast_function()
    memory_intensive_function()


if __name__ == "__main__":
    main()
