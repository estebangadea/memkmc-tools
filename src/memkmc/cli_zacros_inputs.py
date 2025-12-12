import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Zacros input files from a voxelized membrane (stub CLI)."
    )
    parser.add_argument("grid", help="Voxel grid file (e.g. grid.npz)")
    parser.add_argument(
        "--outdir", "-o", default="zacros_inputs",
        help="Directory where Zacros input files will be written."
    )
    args = parser.parse_args()

    print(
        f"[memkmc-zacros-inputs] Stub: would read grid '{args.grid}' "
        f"and write Zacros inputs to '{args.outdir}'."
    )