from __future__ import annotations
import argparse
from pathlib import Path
from typing import List

from memkmc.zacrosio.lattice import write_cubic_pbc_lattice
from memkmc.zacrosio.initial_state import write_initial_state_from_grid
from memkmc.zacrosio.simulation import write_simulation_input
from memkmc.zacrosio.mechanism import write_degradation_mechanism
from memkmc.zacrosio.energetics import write_uniform_energetics


def _infer_grid_shape(grid_xyz: Path):
    """Infer (nx, ny, nz) from a grid XYZ file."""
    with grid_xyz.open("r") as f:
        # Skip first two lines (N, header/comment)
        next(f)
        next(f)
        ix_list, iy_list, iz_list = [], [], []
        for line in f:
            parts = line.split()
            if not parts:
                continue
            ix_list.append(int(parts[1]))
            iy_list.append(int(parts[2]))
            iz_list.append(int(parts[3]))
    nx = max(ix_list) + 1
    ny = max(iy_list) + 1
    nz = max(iz_list) + 1
    return nx, ny, nz


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare full Zacros input sets (lattice, state, simulation, "
            "mechanism, energetics) for a set of seeds using a membrane grid."
        )
    )
    parser.add_argument(
        "grid",
        help="Grid XYZ file (label ix iy iz format, as produced by memkmc-voxelize).",
    )
    parser.add_argument(
        "--mapping",
        required=True,
        help="Label→species mapping file (text: 'label species', used for initial_state).",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        required=True,
        help="Random seeds (e.g. --seeds 101 102 103).",
    )
    parser.add_argument(
        "--outdir",
        default="runs",
        help="Base output directory for seed_* folders (default: 'runs').",
    )
    # Mechanism parameters
    parser.add_argument("--ke", type=float, default=0.5,
                        help="Pre-exponential for sn2_degradation (default: 0.5).")
    parser.add_argument("--kwe", type=float, default=2.5e12,
                        help="Pre-exponential for wat_removal1 (default: 2.5e12).")
    parser.add_argument("--km", type=float, default=1.0e11,
                        help="Pre-exponential for wat_removal2 (default: 1.0e11).")
    parser.add_argument("--kd", type=float, default=1.0e8,
                        help="Pre-exponential for hew_elimination (default: 1.0e8).")

    # Energetics parameters (default = your current values)
    parser.add_argument("--e_mem", type=float, default=-1.0,
                        help="mem* single-site energy (eV, default: -1.0).")
    parser.add_argument("--e_mw", type=float, default=-1.0,
                        help="mw* single-site energy (eV, default: -1.0).")
    parser.add_argument("--e_tma", type=float, default=-1.0,
                        help="tma* single-site energy (eV, default: -1.0).")
    parser.add_argument("--e_hew", type=float, default=-1.0,
                        help="hew* single-site energy (eV, default: -1.0).")
    parser.add_argument("--e_tma_mw", type=float, default=-0.18,
                        help="tma*-mw* interaction energy (eV, default: -0.18).")
    parser.add_argument("--e_tma_hew", type=float, default=-0.18,
                        help="tma*-hew* interaction energy (eV, default: -0.18).")

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing input files in seed_* dirs.",
    )

    args = parser.parse_args()

    grid_path = Path(args.grid)
    mapping_path = Path(args.mapping)
    base_out = Path(args.outdir)

    if not grid_path.exists():
        raise SystemExit(f"Grid file {grid_path} does not exist.")

    base_out.mkdir(parents=True, exist_ok=True)

    # Infer lattice dimensions from the grid
    nx, ny, nz = _infer_grid_shape(grid_path)
    print(f"[memkmc-zacros-prepare-run] Using grid: {grid_path}")
    print(f"[memkmc-zacros-prepare-run] Inferred lattice: nx={nx}, ny={ny}, nz={nz}")

    for seed in args.seeds:
        seed_dir = base_out / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nPreparing inputs in {seed_dir} (seed={seed})")

        lattice_path = seed_dir / "lattice_input.dat"
        state_path = seed_dir / "state_input.dat"
        sim_path = seed_dir / "simulation_input.dat"
        mech_path = seed_dir / "mechanism_input.dat"
        ener_path = seed_dir / "energetics_input.dat"

        # Handle overwrite logic
        if not args.overwrite:
            existing = [
                p for p in [lattice_path, state_path, sim_path, mech_path, ener_path]
                if p.exists()
            ]
            if existing:
                print(
                    f"  - Skipping seed {seed}: some input files already exist "
                    f"(use --overwrite to regenerate)."
                )
                continue

        # 1) Lattice
        write_cubic_pbc_lattice(nx, ny, nz, outfile=lattice_path)
        print("  - lattice_input.dat written")

        # 2) Initial state from shared grid + mapping
        write_initial_state_from_grid(
            grid_xyz=grid_path,
            outfile=state_path,
            mapping_file=mapping_path,
        )
        print("  - state_input.dat written")

        # 3) Simulation input (per-seed random seed)
        write_simulation_input(
            outfile=sim_path,
            random_seed=seed,
        )
        print("  - simulation_input.dat written")

        # 4) Mechanism input
        write_degradation_mechanism(
            outfile=mech_path,
            ke=args.ke,
            kwe=args.kwe,
            km=args.km,
            kd=args.kd,
        )
        print("  - mechanism_input.dat written")

        # 5) Energetics input
        write_uniform_energetics(
            outfile=ener_path,
            site_energy_mem=args.e_mem,
            site_energy_mw=args.e_mw,
            site_energy_tma=args.e_tma,
            site_energy_hew=args.e_hew,
            tma_mw_interaction=args.e_tma_mw,
            tma_hew_interaction=args.e_tma_hew,
        )
        print("  - energetics_input.dat written")

    print("\n[memkmc-zacros-prepare-run] Done. Seed directories are ready for Zacros runs.")