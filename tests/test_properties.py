from pathlib import Path
import numpy as np

from memkmc.voxel.lammps import read_lammps_data
from memkmc.voxel.grid import load_type_classes, build_label_grid
from memkmc.voxel.properties import (
    count_particles, count_grid_voxels,
    compute_lambda, compute_grid_fractions,
)

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "membrane_example.data"
TYPE_CLASSES = DATA_DIR / "type_classes_example.txt"

SPACING = 4.0


def read_grid_xyz(path: Path) -> np.ndarray:
    with path.open("r") as f:
        n = int(f.readline().strip())
        _ = f.readline()
        labels = []
        ix, iy, iz = [], [], []
        for line in f:
            parts = line.split()
            if not parts:
                continue
            labels.append(int(parts[0]))
            ix.append(int(parts[1]))
            iy.append(int(parts[2]))
            iz.append(int(parts[3]))
    nx = max(ix) + 1
    ny = max(iy) + 1
    nz = max(iz) + 1
    arr = np.zeros((nx, ny, nz), dtype=int)
    for lab, i, j, k in zip(labels, ix, iy, iz):
        arr[i, j, k] = lab
    return arr


def test_lambda_and_grid_fractions_match_reference():
    box, types, pos = read_lammps_data(str(DATA_FILE))

    # 1) Phase mapping for the grid (matches M1/M4):
    #    5 and 6 → water-like; 1,2,4,7,8,9 → polymer; 3 → tma.
    phase_mapping = load_type_classes(str(TYPE_CLASSES))

    labels_new, class_to_int = build_label_grid(
        box=box,
        types=types,
        positions=pos,
        spacing=SPACING,
        type_to_class=phase_mapping,
    )

    # 2) λ mapping for particle counts (matches water_N, tma_N logic in make_grid_data.py):
    #    - type 6 → water
    #    - type 3 → tma
    #    - type 5 → cl (separate, not water)
    #    - others → polymer
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

    # Particle-based lambda
    p_counts = count_particles(types, lambda_mapping)
    lam = compute_lambda(p_counts)
    assert abs(lam - 20.71) < 1e-2   # matches report.dat

    # Grid-based FV and VWU from our code
    g_counts = count_grid_voxels(labels_new, class_to_int)
    fv, vwu = compute_grid_fractions(g_counts)
    assert abs(fv - 0.5903) < 1e-4
    assert abs(vwu - 1.2586) < 1e-4