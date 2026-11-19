"""Validate optimized results and ensure main uses the replacement function."""

import time
import unittest
from unittest.mock import patch

import memory_profiler
import profiler
import profiler_optimized as optimized


class TestProfilerOptimized(unittest.TestCase):
    def time_function(self, func):
        start = time.perf_counter()
        result = func()
        return result, time.perf_counter() - start

    def test_slow_function(self):
        result, duration = self.time_function(optimized.slow_function)
        print(f"slow_function: result={result}, duration={duration:.6f} s")
        self.assertEqual(result, 333283335000)
        self.assertGreaterEqual(duration, 2)

    def test_optimized_fast_function(self):
        result, duration = self.time_function(optimized.optimized_fast_function)
        print(f"optimized_fast_function: result={result}, duration={duration:.9f} s")
        self.assertEqual(result, profiler.fast_function())
        self.assertEqual(result, 328350)
        self.assertLess(duration, 1)

    def test_memory_intensive_function(self):
        before = memory_profiler.memory_usage(-1, interval=0.1, timeout=0.1)[0]
        result, duration = self.time_function(optimized.memory_intensive_function)
        after = memory_profiler.memory_usage(-1, interval=0.1, timeout=0.1)[0]
        print(f"memory_intensive_function: result={result}, duration={duration:.6f} s")
        print(f"RSS before={before:.3f} MiB, after={after:.3f} MiB, delta={after-before:.3f} MiB")
        self.assertEqual(result, 333333283333335000000)
        self.assertLess(duration, 5)
        self.assertGreater(before, 0)
        self.assertGreater(after, 0)

    def test_main_calls_optimized_function(self):
        with patch.multiple(optimized, slow_function=unittest.mock.DEFAULT,
                            optimized_fast_function=unittest.mock.DEFAULT,
                            memory_intensive_function=unittest.mock.DEFAULT) as mocks:
            optimized.main()
        for function in mocks.values():
            function.assert_called_once_with()


if __name__ == "__main__":
    unittest.main(verbosity=2)
