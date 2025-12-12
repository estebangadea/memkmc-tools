# src/memkmc/voxel/grid.py

from __future__ import annotations
from typing import Dict, Tuple
import numpy as np


def load_type_classes(path: str) -> Dict[int, str]:
    """Load a mapping from LAMMPS atom type IDs to abstract classes.

    File format:
        # type  class  [name...]
        1       water
        2       polymer
        3       tma
    """
    mapping: Dict[int, str] = {}
    with open(path, "r") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            t = int(parts[0])
            cls = parts[1]
            mapping[t] = cls
    if not mapping:
        raise ValueError(f"No type-class entries found in {path!r}.")
    return mapping


def build_label_grid(
    box: Dict[str, float],
    types: np.ndarray,
    positions: np.ndarray,
    spacing: float,
    type_to_class: Dict[int, str],
) -> Tuple[np.ndarray, Dict[str, int]]:
    """Build a 3D integer label grid from atom positions and type mapping.

    This reproduces the original `make_grid_data.py` behavior when the
    classes include ``water``, ``polymer`` and ``tma``:

    * Choose the number of bins by ``n = int(L // spacing)`` and then define
      the actual bin size as ``L / n`` (if n==0, fall back to 1 bin).
    * Use indices ``int((x - origin) // bin_size)`` for each coordinate.
    * Voxels containing any ``tma`` are labelled as ``tma``.
    * Otherwise, voxels are labelled as ``water`` if
      ``n_water >= n_polymer`` (ties and empty voxels → water),
      and ``polymer`` otherwise.
    """
    lx, ly, lz = box["lx"], box["ly"], box["lz"]
    xlo, ylo, zlo = box["xlo"], box["ylo"], box["zlo"]

    # Choose number of bins as in the original script (using spacing as a target)
    nx = int(lx // spacing)
    ny = int(ly // spacing)
    nz = int(lz // spacing)
    if nx < 1:
        nx = 1
    if ny < 1:
        ny = 1
    if nz < 1:
        nz = 1

    binsizex = lx / nx
    binsizey = ly / ny
    binsizez = lz / nz

    # Determine available classes
    classes = sorted(set(type_to_class.values()))
    class_to_int: Dict[str, int] = {"void": 0}
    for i, cls in enumerate(classes, start=1):
        class_to_int[cls] = i

    # Per-class count grids
    counts = {cls: np.zeros((nx, ny, nz), dtype=int) for cls in classes}

    # Accumulate counts
    for t, (x, y, z) in zip(types, positions):
        cls = type_to_class.get(int(t))
        if cls is None:
            # Unknown types: ignore
            continue

        ix = int((x - xlo) // binsizex)
        iy = int((y - ylo) // binsizey)
        iz = int((z - zlo) // binsizez)

        if 0 <= ix < nx and 0 <= iy < ny and 0 <= iz < nz:
            counts[cls][ix, iy, iz] += 1
        # else: ignore atoms outside, like the original script

    labels = np.zeros((nx, ny, nz), dtype=int)

    has_tma = "tma" in classes
    has_water = "water" in classes
    has_polymer = "polymer" in classes

    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                if has_tma and counts["tma"][ix, iy, iz] > 0:
                    cls = "tma"
                elif has_water and has_polymer:
                    n_w = counts["water"][ix, iy, iz]
                    n_p = counts["polymer"][ix, iy, iz]
                    # Note: this includes empty voxels (0 >= 0) → water,
                    # matching the original M1 >= M2 logic
                    if n_w >= n_p:
                        cls = "water"
                    else:
                        cls = "polymer"
                else:
                    # Generic majority rule for other class sets
                    best_cls = None
                    best_count = 0
                    for c in classes:
                        c_count = counts[c][ix, iy, iz]
                        if c_count > best_count or (
                            c_count == best_count
                            and c_count > 0
                            and (best_cls is None or c < best_cls)
                        ):
                            best_cls = c
                            best_count = c_count
                    cls = best_cls if best_cls is not None else "void"

                labels[ix, iy, iz] = class_to_int.get(cls, 0)

    return labels, class_to_int


def write_grid_xyz(labels: np.ndarray, path: str) -> None:
    """Write grid to an XYZ-style file:

        N
        <blank>
        label ix iy iz
    """
    nx, ny, nz = labels.shape
    n_vox = nx * ny * nz

    with open(path, "w") as f:
        f.write(f"{n_vox}\n\n")
        for iz in range(nz):
            for iy in range(ny):
                for ix in range(nx):
                    lab = int(labels[ix, iy, iz])
                    f.write(f"{lab} {ix} {iy} {iz}\n")