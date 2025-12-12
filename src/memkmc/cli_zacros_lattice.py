from __future__ import annotations
import argparse
from pathlib import Path

from memkmc.zacrosio.lattice import write_cubic_pbc_lattice


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Zacros explicit cubic lattice with 3D PBC."
    )
    parser.add_argument("nx", type=int, help="Number of sites along x.")
    parser.add_argument("ny", type=int, help="Number of sites along y.")
    parser.add_argument("nz", type=int, help="Number of sites along z.")
    parser.add_argument(
        "-o",
        "--output",
        default="lattice_input.dat",
        help="Output file name (default: lattice_input.dat).",
    )
    parser.add_argument(
        "--site-type-name",
        default="G",
        help="Name of the single site type (default: 'G').",
    )

    args = parser.parse_args()
    outpath = Path(args.output)

    write_cubic_pbc_lattice(
        nx=args.nx,
        ny=args.ny,
        nz=args.nz,
        outfile=outpath,
        site_type_name=args.site_type_name,
    )

    print(
        f"[memkmc-zacros-lattice] Wrote 3D PBC lattice "
        f"{args.nx} x {args.ny} x {args.nz} to {outpath}"
    )