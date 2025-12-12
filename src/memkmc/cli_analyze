from __future__ import annotations
import argparse
from pathlib import Path

from memkmc.analysis.specnum import analyze_specnum_file, write_iec_wu_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze Zacros species_numbers files (specnum_*.txt) and "
            "write IEC/WU/VH time series."
        )
    )
    parser.add_argument(
        "specnum_files",
        nargs="+",
        help="Input specnum_*.txt files.",
    )
    parser.add_argument(
        "--prefix",
        default="IEC_WU_",
        help="Prefix for output files (default: 'IEC_WU_').",
    )
    parser.add_argument(
        "--suffix",
        default=".dat",
        help="Suffix for output files (default: '.dat').",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing IEC_WU files.",
    )

    args = parser.parse_args()

    for spec_path in args.specnum_files:
        spec_path = Path(spec_path)
        if not spec_path.exists():
            print(f"[memkmc-analyze] Skipping non-existent file: {spec_path}")
            continue

        stem = spec_path.stem  # e.g. 'specnum_101'
        outname = Path(f"{args.prefix}{stem}{args.suffix}")

        if outname.exists() and not args.overwrite:
            print(f"[memkmc-analyze] {outname} exists, use --overwrite to replace.")
            continue

        print(f"[memkmc-analyze] Analyzing {spec_path} -> {outname}")
        result = analyze_specnum_file(spec_path)
        write_iec_wu_file(result, outname)