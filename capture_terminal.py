"""Capture real Windows console windows displaying the preserved experiment logs.

Screenshots are explicitly labelled as saved-output views, never as live runs.
Requires Pillow for capture; it is a report-building utility, not a workload dependency.
"""

import argparse
import ctypes
from ctypes import wintypes
import json
import math
from pathlib import Path
import subprocess
import sys
import time


def read_log(path):
    data = Path(path).read_bytes()
    return data.decode("utf-16" if data.startswith(b"\xff\xfe") else "utf-8-sig")


def child(spec_path):
    from PIL import ImageGrab

    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    kernel = ctypes.windll.kernel32
    user = ctypes.windll.user32
    user.SetProcessDPIAware()
    kernel.GetConsoleWindow.restype = wintypes.HWND
    hwnd = kernel.GetConsoleWindow()
    kernel.SetConsoleTitleW("lab9_Joey_Saade | " + spec["name"])
    user.ShowWindow(hwnd, 9)
    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
    class FONT(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.ULONG), ("nFont", wintypes.DWORD),
                    ("dwFontSize", COORD), ("FontFamily", wintypes.UINT),
                    ("FontWeight", wintypes.UINT), ("FaceName", wintypes.WCHAR * 32)]
    font = FONT()
    font.cbSize = ctypes.sizeof(FONT)
    font.dwFontSize = COORD(0, 16)
    font.FontFamily = 54
    font.FontWeight = 400
    font.FaceName = "Consolas"
    kernel.SetCurrentConsoleFontEx(kernel.GetStdHandle(-11), False, ctypes.byref(font))
    rows = 8 + sum(max(1, math.ceil(len(line) / 103)) for line in spec["text"].splitlines())
    user.MoveWindow(hwnd, 30, 30, 1560, min(1550, rows * 34 + 90), True)
    user.SetForegroundWindow(hwnd)
    # Use a real console, clear it, and show exact saved output without image synthesis.
    subprocess.run(["cmd", "/c", "cls"])
    print("Project: lab9_Joey_Saade | EECE 435L | " + spec["name"])
    print("Saved output from completed run (see results/ for full raw logs)")
    print("Command: python " + spec["command"])
    print("=" * 90)
    print(spec["text"])
    sys.stdout.flush()
    time.sleep(1.0)
    rect = wintypes.RECT()
    user.GetClientRect(hwnd, ctypes.byref(rect))
    origin = wintypes.POINT(0, 0)
    user.ClientToScreen(hwnd, ctypes.byref(origin))
    if rect.right - rect.left < 200:
        raise RuntimeError("A visible native console is required for authentic capture")
    ImageGrab.grab(bbox=(origin.x, origin.y,
                        origin.x + rect.right, origin.y + rect.bottom)).save(spec["output"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--child")
    args = parser.parse_args()
    if args.child:
        child(args.child)
        return
    target = Path("screenshots")
    target.mkdir(exist_ok=True)
    commands = {
        "cprofile": ("-m cProfile -s time {module}.py", "cprofile.txt"),
        "line_profiler": ("profiler_lineprofiler{suffix}.py", "line_profiler.txt"),
        "memory_profiler": ("-m memory_profiler profiler_memoryprofiler{suffix}.py", "memory_profiler.txt"),
        "tests": ("-m unittest -v {tests}", "tests_unprofiled.txt"),
        "coverage": ("-m coverage report -m", "coverage.txt"),
    }
    manifest = []
    for phase, suffix, module, tests in (
        ("before", "", "profiler", "test_profiler"),
        ("after", "_optimized", "profiler_optimized", "test_profiler_optimized"),
        ("final", "", "", ""),
    ):
        for kind, (command, filename) in commands.items():
            if phase == "final" and kind != "coverage":
                continue
            lines = read_log(Path("results") / phase / filename).splitlines()
            if kind == "cprofile":
                relevant = [line for line in lines[18:] if "(optimized_fast_function)" in line]
                lines = lines[:18]
                if relevant:
                    lines += ["Additional function row from the same report:", *relevant]
            # Long path lines otherwise wrap awkwardly. Preserve output, use separate panels.
            chunks = [lines[i:i+29] for i in range(0, len(lines), 29)]
            for page, chunk in enumerate(chunks, 1):
                name = f"{phase}_{kind}_{page}"
                output = target / (name + ".png")
                spec = {"name": name, "command": command.format(
                    module=module, suffix=suffix, tests=tests),
                    "text": "\n".join(chunk), "output": str(output.resolve())}
                spec_path = target / (name + ".tmp")
                spec_path.write_text(json.dumps(spec), encoding="utf-8")
                process = subprocess.run(["conhost.exe", sys.executable,
                                          str(Path(__file__).resolve()), "--child",
                                          str(spec_path.resolve())])
                if process.returncode or not output.exists():
                    raise RuntimeError("Console screenshot failed: " + name)
                manifest.append({"phase": phase, "kind": kind, "page": page,
                                 "path": str(output), "command": spec["command"]})
                spec_path.unlink()
                print("Captured", output, flush=True)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
