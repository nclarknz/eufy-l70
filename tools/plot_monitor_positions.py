#!/usr/bin/env python3
"""Parse a monitor JSONL log and plot DPS 108 X,Y coordinates.

Each line is expected to be a JSON object with a "dps" dict. DPS 108 is
stored as a string like "[2936,-791,-38]" and is interpreted as a list.

Usage:
    python tools/plot_monitor_positions.py tools/monitor.log
    python tools/plot_monitor_positions.py tools/monitor.log --save positions.png
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def parse_dps_108(value):
    if isinstance(value, list):
        return [int(v) for v in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [int(v) for v in parsed]
        except json.JSONDecodeError:
            pass
        cleaned = value.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            try:
                parts = [p.strip() for p in cleaned[1:-1].split(",")]
                return [int(p) for p in parts if p != ""]
            except ValueError:
                pass
    raise ValueError(f"Unable to parse DPS 108 value: {value!r}")


def load_positions(path):
    positions = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

            dps = item.get("dps")
            if not isinstance(dps, dict):
                continue

            if "108" not in dps:
                continue

            try:
                pos = parse_dps_108(dps["108"])
            except ValueError as exc:
                raise ValueError(f"Line {line_number}: {exc}") from exc

            if len(pos) < 2:
                raise ValueError(f"Line {line_number}: DPS 108 has fewer than 2 values: {pos}")
            positions.append(pos)
    return positions


def main():
    parser = argparse.ArgumentParser(description="Extract DPS 108 positions from a monitor log.")
    parser.add_argument("log_file", help="Path to the monitor JSONL log file")
    parser.add_argument("--save", help="Optional path to save the XY plot image")
    parser.add_argument("--no-show", action="store_true",
                        help="Do not display the plot window after generating it")
    args = parser.parse_args()

    if not os.path.isfile(args.log_file):
        print(f"Log file not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    positions = load_positions(args.log_file)
    if not positions:
        print("No DPS 108 positions found in the log.")
        sys.exit(0)

    print("DPS 108 values:")
    print(positions)
    print()
    print("X,Y coordinate pairs:")
    xy_pairs = [[pos[0], pos[1]] for pos in positions]
    print(xy_pairs)
    print()
    print(f"Parsed {len(positions)} DPS 108 entries.")

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is required to plot the coordinates. Install it with: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    xs = [pos[0] for pos in positions]
    ys = [pos[1] for pos in positions]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(xs, ys, marker="o", linestyle="-", color="tab:blue", label="trajectory")
    ax.scatter(xs, ys, color="tab:red", zorder=3)
    for index, (x, y) in enumerate(zip(xs, ys)):
        ax.annotate(str(index), (x, y), textcoords="offset points", xytext=(4, 4), fontsize=8)

    ax.set_title("DPS 108 X,Y Trace")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.axis("equal")

    if args.save:
        fig.savefig(args.save, dpi=150, bbox_inches="tight")
        print(f"Plot saved to: {args.save}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
