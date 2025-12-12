from __future__ import annotations
import argparse
from pathlib import Path

from memkmc.zacrosio.simulation import write_simulation_input
from memkmc.zacrosio.mechanism import write_degradation_mechanism


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Zacros simulation_input.dat and mechanism_input.dat "
            "for a set of random seeds."
        )
    )
    parser.add_argument(
        "seeds",
        nargs="+",
        type=int,
        help="Random seeds (e.g. 101 102 103).",
    )
    parser.add_argument(
        "--outdir",
        default=".",
        help="Base output directory (default: current directory).",
    )
    parser.add_argument(
        "--ke",
        type=float,
        default=0.5,
        help="Pre-exponential factor for sn2_degradation (default: 0.5).",
    )
    parser.add_argument(
        "--kwe",
        type=float,
        default=2.5e12,
        help="Pre-exponential factor for wat_removal1 (default: 2.5e12).",
    )
    parser.add_argument(
        "--km",
        type=float,
        default=1.0e11,
        help="Pre-exponential factor for wat_removal2 (default: 1.0e11).",
    )
    parser.add_argument(
        "--kd",
        type=float,
        default=1.0e8,
        help="Pre-exponential factor for hew_elimination (default: 1.0e8).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing simulation_input.dat / mechanism_input.dat if present.",
    )

    args = parser.parse_args()
    base = Path(args.outdir)

    base.mkdir(parents=True, exist_ok=True)

    for seed in args.seeds:
        seed_dir = base / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)

        sim_path = seed_dir / "simulation_input.dat"
        mech_path = seed_dir / "mechanism_input.dat"

        if not args.overwrite:
            if sim_path.exists() or mech_path.exists():
                print(f"[memkmc-zacros-inputs] Skipping seed {seed}: files already exist.")
                continue

        write_simulation_input(
            outfile=sim_path,
            random_seed=seed,
        )
        write_degradation_mechanism(
            outfile=mech_path,
            ke=args.ke,
            kwe=args.kwe,
            km=args.km,
            kd=args.kd,
        )

        print(
            f"[memkmc-zacros-inputs] Wrote inputs for seed {seed} in {seed_dir}"
        )