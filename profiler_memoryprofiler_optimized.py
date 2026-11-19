"""Memory profile the optimized call path, with unchanged input sizes."""

from memory_profiler import profile
import profiler_optimized

slow_function = profile(profiler_optimized.slow_function)
optimized_fast_function = profile(profiler_optimized.optimized_fast_function)
memory_intensive_function = profile(profiler_optimized.memory_intensive_function)


def main():
    slow_function()
    optimized_fast_function()
    memory_intensive_function()


if __name__ == "__main__":
    main()
