# src/memkmc/voxel/grid.py

from __future__ import annotations
from typing import Dict, Tuple
import numpy as np


def load_type_classes(path: str) -> Dict[int, str]:
    """
    Load a mapping from LAMMPS atom type IDs to abstract classes.

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
    """
    Build a 3D integer label grid from atom positions and type mapping.

    Returns
    -------
    labels : (nx, ny, nz) int ndarray
        Label for each voxel. 0 = void, >0 = class labels.
    class_to_int : dict
        Mapping from class name to integer label.
    """
    lx, ly, lz = box["lx"], box["ly"], box["lz"]
    xlo, ylo, zlo = box["xlo"], box["ylo"], box["zlo"]

    nx = int(np.floor(lx / spacing))
    ny = int(np.floor(ly / spacing))
    nz = int(np.floor(lz / spacing))

    if nx <= 0 or ny <= 0 or nz <= 0:
        raise ValueError("Grid sizes must be positive; check spacing and box size.")

    labels = np.zeros((nx, ny, nz), dtype=int)

    # Determine available classes and assign integer IDs
    classes = sorted(set(type_to_class.values()))
    class_to_int: Dict[str, int] = {"void": 0}
    for i, cls in enumerate(classes, start=1):
        class_to_int[cls] = i

    # Fill grid
    rel = positions - np.array([[xlo, ylo, zlo]])
    idx = np.floor(rel / spacing).astype(int)

    # clamp indices to [0, n-1] to avoid boundary issues
    idx[:, 0] = np.clip(idx[:, 0], 0, nx - 1)
    idx[:, 1] = np.clip(idx[:, 1], 0, ny - 1)
    idx[:, 2] = np.clip(idx[:, 2], 0, nz - 1)

    for t, (ix, iy, iz) in zip(types, idx):
        cls = type_to_class.get(int(t), "void")
        label = class_to_int.get(cls, 0)
        # we just overwrite; you could also store counts separately
        labels[ix, iy, iz] = label

    return labels, class_to_int


def write_grid_xyz(labels: np.ndarray, path: str) -> None:
    """
    Write grid to an XYZ-style file:
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