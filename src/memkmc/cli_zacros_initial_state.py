from __future__ import annotations
import argparse
from pathlib import Path

from memkmc.zacrosio.initial_state import write_initial_state_from_grid


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Zacros initial_state file from a membrane grid XYZ file."
        )
    )
    parser.add_argument(
        "grid",
        help="Grid XYZ file (label ix iy iz format, as produced by memkmc).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="state_input.dat",
        help="Output initial_state file (default: state_input.dat).",
    )
    parser.add_argument(
        "--mapping",
        required=True,
        help="Label→species mapping file (text: 'label species').",
    )

    args = parser.parse_args()

    grid_path = Path(args.grid)
    outpath = Path(args.output)
    mapping_path = Path(args.mapping)

    write_initial_state_from_grid(
        grid_xyz=grid_path,
        outfile=outpath,
        mapping_file=mapping_path,
    )

    print(
        f"[memkmc-zacros-initial-state] Wrote initial state for grid {grid_path} "
        f"to {outpath}"
    )