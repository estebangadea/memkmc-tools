import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a Zacros simulation (stub CLI)."
    )
    parser.add_argument(
        "run_dir",
        help="Path to a Zacros run directory containing output files."
    )
    parser.add_argument(
        "--summary", "-s", action="store_true",
        help="Print a brief textual summary."
    )
    args = parser.parse_args()

    if args.summary:
        print(
            f"[memkmc-analyze] Stub: would analyze run in '{args.run_dir}' "
            "and print a summary."
        )
    else:
        print(
            f"[memkmc-analyze] Stub: would analyze run in '{args.run_dir}'."
        )