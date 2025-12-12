import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voxelize a membrane structure (stub CLI)."
    )
    parser.add_argument("input", help="Input structure file (e.g. XYZ)")
    parser.add_argument(
        "--spacing", type=float, default=0.4,
        help="Target voxel spacing (in simulation length units)."
    )
    parser.add_argument(
        "--output", "-o", default="grid.npz",
        help="Output voxel grid file."
    )
    args = parser.parse_args()

    # Placeholder behavior for now:
    print(
        f"[memkmc-voxelize] Stub: would voxelize '{args.input}' "
        f"with spacing={args.spacing} and write '{args.output}'."
    )