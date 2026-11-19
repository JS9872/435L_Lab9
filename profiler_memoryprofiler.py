"""Memory profile the original functions at their actual source lines."""

from memory_profiler import profile
import profiler

slow_function = profile(profiler.slow_function)
fast_function = profile(profiler.fast_function)
memory_intensive_function = profile(profiler.memory_intensive_function)


def main():
    slow_function()
    fast_function()
    memory_intensive_function()


if __name__ == "__main__":
    main()
