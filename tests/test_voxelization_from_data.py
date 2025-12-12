from __future__ import annotations
from pathlib import Path
import numpy as np

from memkmc.voxel.lammps import read_lammps_data
from memkmc.voxel.grid import build_label_grid

DATA_DIR = Path(__file__).parent / "data"

DATA_FILE = DATA_DIR / "membrane_example.data"
XYZ_REF = DATA_DIR / "membrane_example.xyz"
GRID_REF = DATA_DIR / "membrane_example_grid.xyz"

# This must match the bin size you used earlier (app_binsize = 4 Å)
SPACING = 4.0

# Mapping from LAMMPS atom types -> abstract classes
# This is inferred from your original script:
#   5,6 -> water; 1,2,4,7,8,9 -> polymer; 3 -> TMA
TYPE_TO_CLASS = {
    1: "polymer",
    2: "polymer",
    3: "tma",
    4: "polymer",
    5: "water",
    6: "water",
    7: "polymer",
    8: "polymer",
    9: "polymer",
}

# Mapping from *old grid labels* (M4) to classes:
#   0 → void, 1 → water, 3 → polymer, 4 → tma
LABEL_TO_CLASS_REF = {
    0: "void",
    1: "water",
    3: "polymer",
    4: "tma",
}


def read_reference_xyz(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Read the old outxyz file:

        N
        <blank>
        type x y z

    Returns types, positions (N,3).
    """
    types = []
    pos = []
    with path.open("r") as f:
        for i, line in enumerate(f):
            if i < 2:
                continue
            parts = line.split()
            if not parts:
                continue
            t = int(parts[0])
            x, y, z = map(float, parts[1:4])
            types.append(t)
            pos.append((x, y, z))
    return np.array(types, dtype=int), np.array(pos, dtype=float)


def read_grid_xyz(path: Path) -> np.ndarray:
    """
    Read grid in the format:

        N
        <blank>
        label ix iy iz
    """
    labels = []
    ix_list, iy_list, iz_list = [], [], []

    with path.open("r") as f:
        for i, line in enumerate(f):
            if i < 2:
                continue
            parts = line.split()
            if not parts:
                continue
            lab = int(parts[0])
            ix = int(parts[1])
            iy = int(parts[2])
            iz = int(parts[3])
            labels.append(lab)
            ix_list.append(ix)
            iy_list.append(iy)
            iz_list.append(iz)

    nx = max(ix_list) + 1
    ny = max(iy_list) + 1
    nz = max(iz_list) + 1

    arr = np.zeros((nx, ny, nz), dtype=int)
    for lab, ix, iy, iz in zip(labels, ix_list, iy_list, iz_list):
        arr[ix, iy, iz] = lab
    return arr


def test_read_lammps_data_matches_reference_xyz():
    """Our LAMMPS data reader should give the same positions/types as the old xyz."""
    box, types, pos = read_lammps_data(str(DATA_FILE))
    types_ref, pos_ref = read_reference_xyz(XYZ_REF)

    assert types.shape == types_ref.shape
    assert pos.shape == pos_ref.shape

    # Exact equality should hold if we parsed the same columns
    assert np.array_equal(types, types_ref)
    assert np.allclose(pos, pos_ref)


def test_build_label_grid_matches_reference_grid_by_class():
    """
    Build a label grid with the new code and compare to the old grid,
    but in terms of *phase classes* (void/water/polymer/tma), not raw ints.

    This avoids depending on the exact numeric codes as long as the
    classification is identical.
    """
    box, types, pos = read_lammps_data(str(DATA_FILE))
    labels_new, class_to_int = build_label_grid(
        box=box,
        types=types,
        positions=pos,
        spacing=SPACING,
        type_to_class=TYPE_TO_CLASS,
    )

    labels_ref = read_grid_xyz(GRID_REF)

    assert labels_new.shape == labels_ref.shape

    # Build int->class mapping for new labels
    int_to_class_new = {v: k for k, v in class_to_int.items()}

    # Vectorized comparison in class space
    vec_new = np.vectorize(lambda i: int_to_class_new.get(int(i), "void"))
    vec_ref = np.vectorize(lambda i: LABEL_TO_CLASS_REF.get(int(i), "void"))

    classes_new = vec_new(labels_new)
    classes_ref = vec_ref(labels_ref)

    assert np.array_equal(classes_new, classes_ref)