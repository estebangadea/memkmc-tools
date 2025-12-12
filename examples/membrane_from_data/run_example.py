from __future__ import annotations
from pathlib import Path

from memkmc.voxel.lammps import read_lammps_data
from memkmc.voxel.grid import (
    load_type_classes,
    build_label_grid,
    write_grid_xyz,
)
from memkmc.voxel.properties import (
    count_particles,
    count_grid_voxels,
    compute_lambda,
    compute_grid_fractions,
    compute_water_uptake,
    build_properties,
)


# Paths (adjust if you move the data elsewhere)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # repo root if you keep tests/data there

DATA_FILE = ROOT / "tests" / "data" / "membrane_example.data"
PHASE_MAPPING_FILE = HERE / "type_classes_phase.txt"
OUT_GRID = HERE / "membrane_example_grid_from_example.xyz"

SPACING = 4.0  # target bin size, as in the original script


def main() -> None:
    print(f"Reading LAMMPS data: {DATA_FILE}")
    box, types, pos = read_lammps_data(str(DATA_FILE))

    # 1) Phase mapping for voxelization (matches M1/M4 logic)
    phase_mapping = load_type_classes(str(PHASE_MAPPING_FILE))

    print("Building voxel grid...")
    labels, class_to_int = build_label_grid(
        box=box,
        types=types,
        positions=pos,
        spacing=SPACING,
        type_to_class=phase_mapping,
    )

    print(f"Grid shape: {labels.shape}")
    write_grid_xyz(labels, str(OUT_GRID))
    print(f"Wrote grid to {OUT_GRID}")

    # 2) Lambda mapping for particle counts (matches make_grid_data.py):
    #    - type 6 -> water (counts for lambda and water mass)
    #    - type 3 -> tma
    #    - type 5 -> cl (separate, NOT water)
    #    - others -> polymer
    lambda_mapping = {
        1: "polymer",
        2: "polymer",
        3: "tma",
        4: "polymer",
        5: "cl",
        6: "water",
        7: "polymer",
        8: "polymer",
        9: "polymer",
    }

    # 3) Count particles and voxels
    p_counts = count_particles(types, lambda_mapping)
    g_counts = count_grid_voxels(labels, class_to_int)

    # 4) Compute lambda and grid-based fractions (FV, VWU)
    lam = compute_lambda(p_counts)
    fv, vwu = compute_grid_fractions(g_counts)

    # 5) Optional: WU using a simple mass model.
    # You can update these masses to exactly match your force field / script.
    # These are consistent with the original `masses` array in make_grid_data.py:
    # [-1, 12.0107, 15.0345, 74.1451, 15.9994, 35.4527, 18.0153, 12.0107, 17, 14]
    mass_by_class = {
        "water": 18.0153,  # type 6
        # For the example we lump all non-water into "dry" mass using a rough guess.
        # For production use, build this from the actual composition of your membrane.
        "polymer": 50.0,
        "tma": 74.1451,
        "cl": 35.4527,
    }
    wu = compute_water_uptake(p_counts, mass_by_class)

    # 6) Assemble properties object (IEC left as None for now)
    props = build_properties(
        particle_counts=p_counts,
        grid_counts=g_counts,
        iec=None,
        wu=wu,
    )

    # 7) Print a mini report (similar to report.dat)
    print("\n=== Membrane properties (example) ===")
    print(f"Total particles                 : {props.n_part}")
    print(f"N_water (type 6)                : {props.n_water}")
    print(f"N_TMA                           : {props.n_tma}")
    print(f"lambda (N_water / N_TMA)        : {props.lam:.2f}")
    print()
    print(f"Grid voxels (total)             : {g_counts.total}")
    print(f"Grid water-like voxels          : {props.n_water_grid}")
    print(f"Grid TMA voxels                 : {props.n_tma_grid}")
    print(f"Grid non-TMA voxels (\"polymer\") : {props.n_pol_grid}")
    print(f"FV  (water voxels / non-TMA)    : {props.fv:.4f}")
    print(f"VWU (water voxels / non-water)  : {props.vwu:.4f}")
    print()
    if props.wu is not None:
        print(f"Water uptake (example WU)       : {props.wu:.4f}")
    if props.iec is not None:
        print(f"IEC                             : {props.iec:.4e}")
    else:
        print("IEC                             : (not computed; fill in mass_dry and use compute_iec)")


if __name__ == "__main__":
    main()