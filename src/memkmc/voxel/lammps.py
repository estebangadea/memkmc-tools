# src/memkmc/voxel/lammps.py

from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np

Box = Dict[str, float]


def _parse_header_counts(lines: List[str]) -> Tuple[int, int, Box]:
    n_atoms = None
    n_types = None
    xlo = xhi = ylo = yhi = zlo = zhi = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.endswith("atoms"):
            n_atoms = int(line.split()[0])
        elif line.endswith("atom types"):
            n_types = int(line.split()[0])
        elif "xlo xhi" in line:
            parts = line.split()
            xlo, xhi = float(parts[0]), float(parts[1])
        elif "ylo yhi" in line:
            parts = line.split()
            ylo, yhi = float(parts[0]), float(parts[1])
        elif "zlo zhi" in line:
            parts = line.split()
            zlo, zhi = float(parts[0]), float(parts[1])

    if None in (n_atoms, n_types, xlo, xhi, ylo, yhi, zlo, zhi):
        raise ValueError("Could not parse header in LAMMPS data file.")

    box = {
        "xlo": xlo,
        "xhi": xhi,
        "ylo": ylo,
        "yhi": yhi,
        "zlo": zlo,
        "zhi": zhi,
        "lx": xhi - xlo,
        "ly": yhi - ylo,
        "lz": zhi - zlo,
    }
    return n_atoms, n_types, box


def read_lammps_data(path: str) -> Tuple[Box, np.ndarray, np.ndarray]:
    """
    Read a LAMMPS data file and return box info, types and positions.

    Returns
    -------
    box : dict
        {xlo, xhi, ylo, yhi, zlo, zhi, lx, ly, lz}
    types : (N,) int ndarray
        Atom types.
    positions : (N, 3) float ndarray
        Atom positions (x, y, z).
    """
    with open(path, "r") as f:
        lines = f.readlines()

    # 1) header
    n_atoms, n_types, box = _parse_header_counts(lines)

    # 2) find sections
    masses_start = atoms_start = None
    atoms_style = "atomic"
    for i, line in enumerate(lines):
        if line.strip().startswith("Masses"):
            masses_start = i
        if line.strip().startswith("Atoms"):
            atoms_start = i
            # 'Atoms # full', 'Atoms # atomic', ...
            if "#" in line:
                atoms_style = line.split("#", 1)[1].strip()
            break

    if atoms_start is None:
        raise ValueError("No 'Atoms' section found in LAMMPS data file.")

    # 3) parse masses (we just keep a dict, might be useful later)
    masses: Dict[int, float] = {}
    if masses_start is not None:
        i = masses_start + 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                break
            if line.startswith("#"):
                i += 1
                continue
            parts = line.split()
            if len(parts) >= 2:
                t = int(parts[0])
                m = float(parts[1])
                masses[t] = m
            i += 1

    # 4) parse Atoms section
    # Find first non-empty after 'Atoms' line
    i = atoms_start + 1
    while i < len(lines) and not lines[i].strip():
        i += 1

    atom_lines: List[str] = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            break
        if line.startswith("#"):
            i += 1
            continue
        atom_lines.append(line)
        i += 1

    if len(atom_lines) != n_atoms:
        # Not fatal, but warn via ValueError for now
        raise ValueError(
            f"Expected {n_atoms} atom lines, found {len(atom_lines)} in Atoms section."
        )

    types = np.empty(n_atoms, dtype=int)
    pos = np.empty((n_atoms, 3), dtype=float)

    for idx, line in enumerate(atom_lines):
        parts = line.split()
        # Basic styles
        if atoms_style.startswith("atomic"):
            # atom-ID atom-type x y z
            atype = int(parts[1])
            x, y, z = map(float, parts[2:5])
        elif atoms_style.startswith("charge"):
            # atom-ID atom-type q x y z
            atype = int(parts[1])
            x, y, z = map(float, parts[3:6])
        elif atoms_style.startswith("full"):
            # atom-ID molecule-ID atom-type q x y z
            atype = int(parts[2])
            x, y, z = map(float, parts[4:7])
        else:
            # Fallback: assume type is second column, last 3 are x y z
            atype = int(parts[1])
            x, y, z = map(float, parts[-3:])

        types[idx] = atype
        pos[idx, :] = (x, y, z)

    return box, types, pos


def read_lammpstrj(path: str, frame: str | int = "last") -> Tuple[Box, np.ndarray, np.ndarray]:
    """
    Read a LAMMPS trajectory (.lammpstrj) and return a single frame.

    Parameters
    ----------
    path : str
        Trajectory file path.
    frame : 'last' or int
        If 'last', return the last frame. If int, return that timestep index
        in file order (0-based).

    Returns
    -------
    box : dict
    types : (N,) int ndarray
    positions : (N, 3) float ndarray
    """
    chosen = None
    chosen_box: Box | None = None

    with open(path, "r") as f:
        lines = iter(f)
        while True:
            try:
                line = next(lines)
            except StopIteration:
                break

            if not line.startswith("ITEM: TIMESTEP"):
                continue

            # TIMESTEP
            timestep = int(next(lines).strip())

            # NUMBER OF ATOMS
            line = next(lines)
            assert line.startswith("ITEM: NUMBER OF ATOMS")
            n_atoms = int(next(lines).strip())

            # BOX BOUNDS
            line = next(lines)
            assert line.startswith("ITEM: BOX BOUNDS")
            # we ignore boundary types for now
            xlo, xhi = map(float, next(lines).split()[:2])
            ylo, yhi = map(float, next(lines).split()[:2])
            zlo, zhi = map(float, next(lines).split()[:2])

            box = {
                "xlo": xlo,
                "xhi": xhi,
                "ylo": ylo,
                "yhi": yhi,
                "zlo": zlo,
                "zhi": zhi,
                "lx": xhi - xlo,
                "ly": yhi - ylo,
                "lz": zhi - zlo,
            }

            # ATOMS
            line = next(lines)
            assert line.startswith("ITEM: ATOMS")
            fields = line.split()[2:]  # after 'ITEM: ATOMS'
            # indices of the columns we care about
            idx_id = fields.index("id")
            idx_type = fields.index("type")
            idx_x = fields.index("x")
            idx_y = fields.index("y")
            idx_z = fields.index("z")

            types = np.empty(n_atoms, dtype=int)
            pos = np.empty((n_atoms, 3), dtype=float)

            for i in range(n_atoms):
                parts = next(lines).split()
                types[i] = int(parts[idx_type])
                pos[i, 0] = float(parts[idx_x])
                pos[i, 1] = float(parts[idx_y])
                pos[i, 2] = float(parts[idx_z])

            # Decide whether to keep this frame
            if frame == "last":
                chosen = (types, pos)
                chosen_box = box
            elif isinstance(frame, int):
                if frame == 0:
                    # We want the first encountered
                    return box, types, pos
                else:
                    frame -= 1

    if chosen is None or chosen_box is None:
        raise ValueError(f"No frames found in trajectory {path!r}.")

    types, pos = chosen
    return chosen_box, types, pos