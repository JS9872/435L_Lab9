"""Build the Lab 9 Word report from measured outputs and real screenshots.

Report dependencies: python-docx and Pillow. Run after all experiments and capture_terminal.py.
Design: standard_business_brief; compact memo masthead without a decorative rule.
"""

import json
from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Twips
from PIL import Image, ImageDraw, ImageFont

from capture_terminal import read_log


ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def line_times(phase):
    text = read_log(ROOT / f"results/{phase}/line_profiler.txt")
    return {name: float(duration) for duration, name in re.findall(
        r"Total time: ([\d.e+-]+) s\s+File: [^\n]+\s+Function: (\w+)", text)}


def cprofile_times(phase):
    text = read_log(ROOT / f"results/{phase}/cprofile.txt")
    result = {}
    for line in text.splitlines():
        match = re.match(r"\s*\d+\s+([\d.]+)\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s+(.+)", line)
        if match:
            result[match[3]] = {"self": float(match[1]), "cumulative": float(match[2])}
    return result


def memory_summary(phase):
    text = read_log(ROOT / f"results/{phase}/memory_profiler.txt")
    samples = [float(x) for x in re.findall(r"^\s*\d+\s+([\d.]+) MiB", text, re.MULTILINE)]
    if not samples:
        raise ValueError("Missing memory output for " + phase)
    return min(samples), max(samples)


def create_chart(benchmark):
    image = Image.new("RGB", (1500, 720), "white")
    draw = ImageDraw.Draw(image)
    fonts = Path("C:/Windows/Fonts")
    title = ImageFont.truetype(str(fonts / "calibrib.ttf"), 34)
    body = ImageFont.truetype(str(fonts / "calibri.ttf"), 27)
    small = ImageFont.truetype(str(fonts / "calibri.ttf"), 23)
    draw.text((35, 20), "Repeated unprofiled timings (median)", font=title, fill="#16334f")
    panels = [
        (100, "Fast function — microseconds per call", [
            ("Original loop", benchmark["original_fast"]["median_seconds"] * 1e6),
            ("Generator example", benchmark["generator_candidate"]["median_seconds"] * 1e6),
            ("Exact formula", benchmark["optimized_fast"]["median_seconds"] * 1e6)]),
        (430, "Whole program — seconds per call", [
            ("Original main", benchmark["original_main"]["median_seconds"]),
            ("Optimized main", benchmark["optimized_main"]["median_seconds"])])]
    colors = ("#607d96", "#92a8b8", "#2e74b5")
    for top, heading, values in panels:
        draw.text((35, top), heading, font=body, fill="#222222")
        max_value = max(value for _, value in values) * 1.15
        for i in range(5):
            x = 340 + 900 * i / 4
            draw.line((x, top + 48, x, top + 48 + 65 * len(values)), fill="#e1e5e9", width=2)
            draw.text((x - 15, top + 53 + 65 * len(values)), f"{max_value*i/4:.2f}",
                      font=small, fill="#555555")
        for i, (label, value) in enumerate(values):
            y = top + 58 + 65 * i
            draw.text((35, y), label, font=body, fill="#222222")
            width = 900 * value / max_value
            draw.rectangle((340, y, 340 + max(width, 2), y + 34), fill=colors[i])
            draw.text((355 + width, y), f"{value:.4f}", font=small, fill="#222222")
    output = ROOT / "results/timing_comparison.png"
    image.save(output)
    return output


def set_style(doc, name, size, color="202020", before=0, after=6, line=1.1, bold=False):
    style = doc.styles[name]
    style.font.name = "Calibri"
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor.from_string(color)
    style.font.bold = bold
    fmt = style.paragraph_format
    fmt.space_before, fmt.space_after = Pt(before), Pt(after)
    fmt.line_spacing = line
    return style


def table(doc, rows):
    widths = [4320, 2520, 2520]
    tbl = doc.add_table(rows=0, cols=3)
    tbl.autofit = False
    for values in rows:
        cells = tbl.add_row().cells
        for cell, value in zip(cells, values):
            cell.text = str(value)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.space_before = Pt(4)
                for run in p.runs:
                    run.font.size = Pt(10)
    pr = tbl._tbl.tblPr
    width = pr.find(qn("w:tblW"))
    width.set(qn("w:w"), "9360")
    width.set(qn("w:type"), "dxa")
    indent = OxmlElement("w:tblInd")
    indent.set(qn("w:w"), "120")
    indent.set(qn("w:type"), "dxa")
    pr.append(indent)
    margins = OxmlElement("w:tblCellMar")
    for edge, value in (("top", 80), ("bottom", 80), ("start", 120), ("end", 120)):
        node = OxmlElement("w:" + edge)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        margins.append(node)
    pr.append(margins)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement("w:" + edge)
        for key, value in (("val", "single"), ("sz", "4"), ("color", "D5DAE0")):
            node.set(qn("w:" + key), value)
        borders.append(node)
    pr.append(borders)
    grid = tbl._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for w in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(w))
        grid.append(col)
    for row in tbl.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = Twips(w)
    for cell in tbl.rows[0].cells:
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), "F2F4F7")
        cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    repeat = OxmlElement("w:tblHeader")
    tbl.rows[0]._tr.get_or_add_trPr().append(repeat)
    return tbl


def para(doc, text, style=None):
    return doc.add_paragraph(text, style=style)


def new_page(doc, heading):
    doc.add_page_break()
    doc.add_heading(heading, 1)


def main():
    benchmark = load("results/benchmark.json")
    before = load("results/before/coverage.json")
    after = load("results/after/coverage.json")
    final = load("results/final/coverage.json")
    lines = {phase: line_times(phase) for phase in ("before", "after")}
    memory = {phase: memory_summary(phase) for phase in ("before", "after")}
    chart = create_chart(benchmark)
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(1)
    section.left_margin = section.right_margin = Inches(1)
    section.header_distance = section.footer_distance = Inches(0.492)
    set_style(doc, "Normal", 11)
    set_style(doc, "Title", 28, "16334F", after=8, bold=True)
    set_style(doc, "Subtitle", 12, "555555", after=10)
    for name, size, color, before_space, after_space in (
        ("Heading 1", 16, "2E74B5", 16, 8),
        ("Heading 2", 13, "2E74B5", 12, 6),
        ("Heading 3", 12, "1F4D78", 8, 4)):
        set_style(doc, name, size, color, before_space, after_space, bold=True)
    set_style(doc, "Caption", 9, "555555", before=4, after=6)
    header = section.header.paragraphs[0]
    header.text = "EECE 435L  |  Lab 9: Profiling in Python"
    for run in header.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string("666666")
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Joey Saade  |  ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    doc.core_properties.author = "Joey Saade"
    doc.core_properties.title = "Lab 9 - Profiling in Python"
    doc.core_properties.subject = "Original and optimized profiling evidence"
    para(doc, "Lab 9\nProfiling in Python", "Title")
    para(doc, "Joey Saade | Software Tools Lab | Fall 2026–2027", "Subtitle")
    para(doc, "Repository: https://github.com/JS9872/435L_Lab9")
    doc.add_heading("Objective and implementation", 1)
    para(doc, "Identify execution-time bottlenecks, observe process memory, assess coverage, and measure an optimization using cProfile, line_profiler, memory_profiler, and coverage.py. Both versions use the complete workloads from the handout.")
    para(doc, "The original slow_function sleeps for two seconds and sums 10,000 squares; fast_function sums 100 squares; memory_intensive_function sums 10,000,000 squares. The expected results are 333283335000, 328350, and 333333283333335000000 respectively. Broken formatting, repeated excerpts, and malformed entry-point guards in the handout were repaired.")
    doc.add_heading("Optimization and controlled comparison", 2)
    para(doc, "All optimized entry points call optimized_fast_function instead of fast_function. For n=100, the exact identity n(n−1)(2n−1)/6 computes the same integer sum for range(n), using integer division and a fixed number of operations. The original and optimized files are both retained. The slow and large-loop functions are shared unchanged so their workloads remain identical.")
    para(doc, "The optional generator-expression example was benchmarked separately. It avoids a list allocation, but the original loop does not allocate a list either. The selected formula removes all 100 iterations, which is a stronger optimization for this fixed problem.")
    doc.add_heading("Environment and method", 2)
    para(doc, benchmark["python"].split("\n")[0] + "\n" + benchmark["platform"])
    para(doc, "; ".join(f"{key} {value}" for key, value in benchmark["packages"].items()))
    para(doc, "Raw outputs are saved under results/before and results/after. Terminal screenshots display these exact saved outputs and their commands, labelled as saved-output views. Long reports are split into successive panels; cProfile screenshots show the top of the time-sorted report and a separately labelled optimized-function row when needed. Full logs remain available in the repository.")

    new_page(doc, "Measured timing results")
    table(doc, [
        ("Metric", "Original", "Optimized"),
        ("Fast function, median μs/call", f"{benchmark['original_fast']['median_seconds']*1e6:.4f}", f"{benchmark['optimized_fast']['median_seconds']*1e6:.4f}"),
        ("Whole program, median seconds", f"{benchmark['original_main']['median_seconds']:.6f}", f"{benchmark['optimized_main']['median_seconds']:.6f}"),
        ("Line profiler: fast function (s)", f"{lines['before']['fast_function']:.9f}", f"{lines['after']['optimized_fast_function']:.9f}"),
        ("Line profiler: large loop (s)", f"{lines['before']['memory_intensive_function']:.6f}", f"{lines['after']['memory_intensive_function']:.6f}"),
    ])
    para(doc, "Repeated timing: seven batches of 100,000 fast-function calls; three complete-program calls per version. The chart uses separate scales because the units and magnitudes differ.", "Caption")
    doc.add_picture(str(chart), width=Inches(6.5))
    doc.add_heading("Interpretation", 2)
    para(doc, f"The exact formula is {benchmark['fast_speedup']:.2f}× faster than the original fast loop in the repeated unprofiled benchmark. The generator candidate took {benchmark['generator_candidate']['median_seconds']*1e6:.4f} μs per call. These measurements characterize this Python version and machine, rather than a universal speed guarantee.")
    para(doc, f"The whole-program median ratio was {benchmark['main_speedup']:.4f}× (original / optimized). Changing a function that runs for microseconds cannot materially improve a program dominated by a two-second sleep and ten million loop iterations. Differences in total time largely reflect measurement noise and system scheduling; no meaningful end-to-end improvement is claimed.")
    para(doc, "cProfile identifies time.sleep and memory_intensive_function as the principal contributors. line_profiler attributes the slow function mainly to the sleep, and the large function to its loop and square/accumulate line. The optimized fast function has only an assignment and an arithmetic return. Profiler overhead is substantial, so instrumented timings are not used as ordinary application-speed benchmarks.")

    new_page(doc, "Memory, tests, and coverage")
    doc.add_heading("Memory analysis", 2)
    para(doc, f"Observed call-boundary RSS ranged from {memory['before'][0]:.1f} to {memory['before'][1]:.1f} MiB before optimization and {memory['after'][0]:.1f} to {memory['after'][1]:.1f} MiB afterward. These are separate Python processes: their absolute footprints should not be subtracted to infer savings. The within-run increments and sampled peak give the relevant evidence.")
    para(doc, "Despite its name, memory_intensive_function retains only an accumulator and current loop index over a lazy range. It is CPU intensive, with approximately constant auxiliary storage at these input sizes; integer size grows with the numerical result rather than the number of retained elements. Neither version builds a ten-million-element list. No material reduction in memory use is claimed for the fast-function change.")
    para(doc, "memory_profiler reports the pre-existing process RSS as the first line's increment. That value is not newly allocated function memory. Small RSS movements also reflect interpreter allocation and process noise. Decorated thin wrappers measure RSS around each full-size function call; memory_usage additionally samples the complete workload at a requested 10 ms interval. This avoids millions of expensive Windows RSS queries and does not claim per-iteration memory attribution. Brief peaks shorter than the effective sampling interval may be missed.")
    for phase in ("before", "after"):
        text = read_log(ROOT / f"results/{phase}/memory_profiler.txt")
        sample_line = next(line for line in text.splitlines() if line.startswith("Sampled RSS:"))
        para(doc, phase.title() + " optimization — " + sample_line)
    doc.add_heading("Test design and handout corrections", 2)
    para(doc, "Both suites verify exact sums, the two-second sleep, fast-function timing, and that main calls every required function once. The optimized suite also checks equivalence to the original fast function. Four tests run per version; the combined suite runs eight tests. Actual timings and RSS readings are printed.")
    para(doc, "The handout's positive retained-memory assertion is not valid for a scalar accumulation, so tests check valid memory readings and numerical correctness instead. Its five-second large-loop budget is checked only in unprofiled runs: coverage tracing inflated an early run to roughly 19 seconds, and simultaneous full memory profiling also affected ordinary timing. Instrumented correctness tests do not apply that unprofiled timing budget. Final raw test logs document the completed runs.")
    doc.add_heading("Coverage gaps and follow-up", 2)
    for label, data in (("Original", before), ("Optimized", after)):
        for filename, info in data["files"].items():
            summary = info["summary"]
            para(doc, f"{label} initial report ({filename}): {summary['covered_lines']}/{summary['num_statements']} executable statements; {summary['percent_covered']:.2f}% combined statement/branch coverage. Missing source lines: {info['missing_lines']}. The uncovered line is main() inside the __main__ guard; its true branch is not reached by importing the module.")
    para(doc, "The optimized initial report targets profiler_optimized.py; its unchanged imported functions are measured in the original and final combined reports. The smaller optimized module gives a different coverage denominator, so a lower initial percentage does not imply weaker function testing.")
    para(doc, f"Follow-up: run_final_coverage.py runs unittest discovery and then both real script entry points under appended branch coverage. The final combined report covers {final['totals']['covered_lines']}/{final['totals']['num_statements']} statements with {final['totals']['percent_covered']:.2f}% combined coverage. Initial gap reports are preserved separately. Open htmlcov/index.html for the complete report.")

    manifest = load("screenshots/manifest.json")
    figure = 0
    evidence_groups = [
        ("cProfile — before and after", "cprofile", ("before", "after")),
        ("Line profiling — original", "line_profiler", ("before",)),
        ("Line profiling — optimized", "line_profiler", ("after",)),
        ("Memory profiling — original", "memory_profiler", ("before",)),
        ("Memory profiling — optimized", "memory_profiler", ("after",)),
        ("Test execution — before and after", "tests", ("before", "after")),
        ("Coverage — initial gaps", "coverage", ("before", "after")),
    ]
    for heading, kind, phases in evidence_groups:
        new_page(doc, heading)
        for phase in phases:
            for entry in manifest:
                if entry["phase"] != phase or entry["kind"] != kind:
                    continue
                figure += 1
                p = para(doc, f"Figure {figure}. {phase.title()} optimization, panel {entry['page']}. "
                         + entry["command"], "Caption")
                p.paragraph_format.keep_with_next = True
                doc.add_picture(str(ROOT / entry["path"]), width=Inches(6.5))
    new_page(doc, "Final verification and reproduction")
    para(doc, "Final combined statement and branch coverage after exercising both entry points:")
    for entry in manifest:
        if entry["phase"] == "final":
            doc.add_picture(str(ROOT / entry["path"]), width=Inches(6.5))
    for line in read_log(ROOT / "results/final/coverage.txt").splitlines():
        p = para(doc, line)
        for run in p.runs:
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        p.paragraph_format.space_after = Pt(0)
    doc.add_heading("Reproduction commands", 2)
    for command in (
        "python -m venv .venv",
        "./.venv/Scripts/python.exe -m pip install -r requirements.txt",
        "./.venv/Scripts/python.exe run_experiments.py",
        "./.venv/Scripts/python.exe run_final_coverage.py",
    ):
        p = para(doc, command)
        for run in p.runs:
            run.font.name = "Consolas"
            run.font.size = Pt(9)
    para(doc, "Memory drivers combine decorated call-boundary measurements and periodic RSS sampling. Run experiments sequentially and avoid other CPU-intensive tasks when comparing ordinary timings. All input sizes remain the handout's original values. requirements.txt pins the profiling packages; the report-only scripts additionally require python-docx and Pillow.")
    doc.add_heading("Submitted materials", 2)
    para(doc, "Original and optimized workload scripts, profiler drivers, and tests; run_experiments.py and benchmark.py; raw before/after outputs and benchmark JSON; HTML coverage folders with their assets; console screenshot PNGs; and this Word report. README.md explains the commands, test corrections, and directory contents. The source handout and local environment credentials are excluded from the public repository.")
    para(doc, "Reference: supplied handout, lab9 -Profiling in python.docx, EECE 435L Software Tools Lab, Fall 2026–2027.")
    output = ROOT / "lab9_Joey_Saade.docx"
    doc.save(output)
    print("Built", output)


if __name__ == "__main__":
    main()
