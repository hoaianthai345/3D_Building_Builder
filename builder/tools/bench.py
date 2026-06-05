"""Measure real hardware cost of the procedural builder across complexity levels.

Records build time, peak RAM, GLB size and triangle count for a grid of
(floors x rooms_per_floor), writes a CSV, and prints a Markdown table to paste
into REPORT.md (the <<HARDWARE METRICS>> slot).

    python -m builder.tools.bench            # default grid
    python -m builder.tools.bench --csv bench/results.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import tempfile
import tracemalloc

from ..procedural import build_glb
from ..schemas import BuildingSpec, SpaceType

GRID = [(3, 4), (5, 6), (8, 6), (12, 4), (20, 8), (40, 10)]


def _measure(floors: int, rooms: int) -> dict:
    spec = BuildingSpec(
        space_type=SpaceType.office,
        floors=floors,
        rooms_per_floor=rooms,
        occupancy=floors * rooms * 4,
        footprint_w=24.0,
        footprint_d=16.0,
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "b.glb")
        tracemalloc.start()
        info = build_glb(spec, out)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return {
        "floors": floors,
        "rooms_per_floor": rooms,
        "complexity": floors * rooms,
        "build_ms": round(getattr(info, "_build_ms", 0.0), 1),
        "peak_ram_mb": round(peak / 1024 / 1024, 2),
        "tri_count": info.tri_count,
        "glb_kb": info.size_kb,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark procedural builder")
    p.add_argument("--csv", default="bench/results.csv")
    args = p.parse_args()

    rows = [_measure(f, r) for f, r in GRID]

    os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
    with open(args.csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"# Procedural builder benchmark ({platform.python_version()} on {platform.machine()})\n")
    print("| Floors | Rooms/floor | Complexity | Build (ms) | Peak RAM (MB) | Triangles | GLB (KB) |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['floors']} | {r['rooms_per_floor']} | {r['complexity']} | "
              f"{r['build_ms']} | {r['peak_ram_mb']} | {r['tri_count']} | {r['glb_kb']} |")
    print(f"\nCSV: {args.csv}")


if __name__ == "__main__":
    main()
