from __future__ import annotations
import argparse
from pathlib import Path
from typing import List

import numpy as np
import matplotlib.pyplot as plt


def _read_iec_wu(path: Path):
    """Read IEC_WU_*.dat file and return IEC, WU arrays.

    Expects header, then columns: time, IEC, WU, VH.
    """
    iec: list[float] = []
    wu: list[float] = []

    with path.open("r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        iec.append(float(parts[1]))
        wu.append(float(parts[2]))

    if not iec:
        raise ValueError(f"No IEC/WU data in {path}")

    return np.array(iec, dtype=float), np.array(wu, dtype=float)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Plot WU vs IEC curves from IEC_WU_*.dat files, including "
            "individual trajectories and their average."
        )
    )
    parser.add_argument(
        "iec_wu_files",
        nargs="+",
        help="IEC_WU_*.dat files produced by memkmc-analyze.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="WUvsIEC.png",
        help="Output figure filename (default: WUvsIEC.png).",
    )
    parser.add_argument(
        "--x-min",
        type=float,
        default=1.4,
        help="Minimum IEC value for interpolation/plot (default: 1.4).",
    )
    parser.add_argument(
        "--x-max",
        type=float,
        default=2.3,
        help="Maximum IEC value for interpolation/plot (default: 2.3).",
    )
    parser.add_argument(
        "--npts",
        type=int,
        default=200,
        help="Number of interpolation points (default: 200).",
    )

    args = parser.parse_args()

    files = [Path(f) for f in args.iec_wu_files]

    fig, ax = plt.subplots(figsize=(4.0, 3.5), dpi=180)

    curves_x: List[np.ndarray] = []
    curves_y: List[np.ndarray] = []

    # Plot individual curves
    for path in files:
        if not path.exists():
            print(f"[memkmc-plot-iec-wu] Skipping non-existent file: {path}")
            continue

        iec, wu = _read_iec_wu(path)
        if len(iec) < 2:
            continue

        # plot raw curve
        ax.plot(
            iec,
            wu,
            color="lightsteelblue",
            alpha=0.7,
            linewidth=0.75,
        )

        curves_x.append(iec)
        curves_y.append(wu)

    if not curves_x:
        print("[memkmc-plot-iec-wu] No valid curves found; nothing to plot.")
        return

    # Interpolate all curves onto a common IEC grid and average
    x_common = np.linspace(args.x_min, args.x_max, args.npts)
    y_interp = []

    for x, y in zip(curves_x, curves_y):
        if len(x) <= 10:
            continue
        # Ensure monotonic x for interpolation
        order = np.argsort(x)
        x_sorted = x[order]
        y_sorted = y[order]
        # Linear interpolation within [min(x), max(x)]
        y_common = np.interp(x_common, x_sorted, y_sorted)
        y_interp.append(y_common)

    if y_interp:
        y_interp = np.array(y_interp)
        y_avg = np.mean(y_interp, axis=0)
        ax.plot(x_common, y_avg, color="tab:red", linewidth=2, label="Average curve")

    # Axes styling (following your original script)
    ax.set_ylabel("WU")
    ax.set_xlabel("IEC")
    ax.set_xlim([1.34, 2.4])
    ax.set_ylim([0.1, 0.9])
    ax.tick_params(axis="both", direction="in")

    plt.tight_layout()
    plt.savefig(args.output)
    print(f"[memkmc-plot-iec-wu] Saved figure to {args.output}")