# src/memkmc/cli_voxelize.py

from __future__ import annotations
import argparse
from pathlib import Path

from memkmc.voxel.lammps import read_lammps_data, read_lammpstrj
from memkmc.voxel.grid import load_type_classes, build_label_grid, write_grid_xyz


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voxelize a membrane structure from LAMMPS data or trajectory."
    )
    parser.add_argument("input", help="LAMMPS .data or .lammpstrj file")
    parser.add_argument(
        "--format",
        choices=["data", "lammpstrj"],
        default="data",
        help="Input format (default: data).",
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=0.4,
        help="Target voxel spacing (same units as input coordinates).",
    )
    parser.add_argument(
        "--types",
        required=True,
        help="Type→class mapping file (e.g. type_classes.txt).",
    )
    parser.add_argument(
        "--frame",
        default="last",
        help="For lammpstrj: which frame to use ('last' or integer index).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="grid.xyz",
        help="Output grid file (XYZ-like format).",
    )

    args = parser.parse_args()
    inp = Path(args.input)

    if args.format == "data":
        box, types, pos = read_lammps_data(str(inp))
    else:
        frame = args.frame
        if isinstance(frame, str) and frame != "last":
            try:
                frame = int(frame)
            except ValueError:
                raise SystemExit("Frame must be 'last' or an integer index.")
        box, types, pos = read_lammpstrj(str(inp), frame=frame)

    type_to_class = load_type_classes(args.types)
    labels, class_to_int = build_label_grid(
        box=box,
        types=types,
        positions=pos,
        spacing=args.spacing,
        type_to_class=type_to_class,
    )

    write_grid_xyz(labels, args.output)

    print(
        f"[memkmc-voxelize] Wrote grid {labels.shape} to {args.output!r} "
        f"with classes: {class_to_int}"
    )