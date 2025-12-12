from __future__ import annotations
from pathlib import Path
from typing import List

from memkmc.zacrosio.lattice import write_cubic_pbc_lattice
from memkmc.zacrosio.initial_state import write_initial_state_from_grid
from memkmc.zacrosio.simulation import write_simulation_input
from memkmc.zacrosio.mechanism import write_degradation_mechanism
from memkmc.zacrosio.energetics import write_uniform_energetics


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # repo root if you keep tests/data under it

# Example inputs – adjust as needed
GRID_XYZ = ROOT / "tests" / "data" / "membrane_example_grid.xyz"
LABEL_TO_SPECIES = HERE / "label_to_species.txt"  # we define this below
SEEDS: List[int] = [101, 102, 103]
SPACING = 4.0  # not used here; grid already exists


def infer_grid_shape(grid_xyz: Path):
    """Infer (nx, ny, nz) from a grid XYZ file."""
    with grid_xyz.open("r") as f:
        # Skip the first two lines
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
    print(f"Using grid file: {GRID_XYZ}")
    nx, ny, nz = infer_grid_shape(GRID_XYZ)
    print(f"Inferred lattice size: nx={nx}, ny={ny}, nz={nz}")

    base = HERE / "runs_example"
    base.mkdir(parents=True, exist_ok=True)

    for seed in SEEDS:
        seed_dir = base / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== Preparing inputs in {seed_dir} for seed {seed} ===")

        # 1) Lattice (3D PBC)
        lattice_path = seed_dir / "lattice_input.dat"
        write_cubic_pbc_lattice(nx, ny, nz, outfile=lattice_path)
        print(f"  - lattice_input.dat written")

        # 2) Initial state from the shared grid
        #    We assume the lattice ordering matches the grid ordering, which it does:
        #    iz, iy, ix loops with site IDs starting at 1.
        state_path = seed_dir / "state_input.dat"
        write_initial_state_from_grid(
            grid_xyz=GRID_XYZ,
            outfile=state_path,
            mapping_file=LABEL_TO_SPECIES,
        )
        print(f"  - state_input.dat written")

        # 3) Simulation input (per-seed random seed)
        sim_path = seed_dir / "simulation_input.dat"
        write_simulation_input(
            outfile=sim_path,
            random_seed=seed,
        )
        print(f"  - simulation_input.dat written")

        # 4) Mechanism input
        mech_path = seed_dir / "mechanism_input.dat"
        write_degradation_mechanism(
            outfile=mech_path,
            ke=0.5,
            kwe=2.5e12,
            km=1.0e11,
            kd=1.0e8,
        )
        print(f"  - mechanism_input.dat written")

        # 5) Energetics input
        ener_path = seed_dir / "energetics_input.dat"
        write_uniform_energetics(
            outfile=ener_path,
            site_energy_mem=-1.0,
            site_energy_mw=-1.0,
            site_energy_tma=-1.0,
            site_energy_hew=-1.0,
            tma_mw_interaction=-0.18,
            tma_hew_interaction=-0.18,
        )
        print(f"  - energetics_input.dat written")

    print("\nAll example seed directories prepared. You can now copy your Zacros "
          "executable/template files into each seed_* directory and run.")


if __name__ == "__main__":
    main()