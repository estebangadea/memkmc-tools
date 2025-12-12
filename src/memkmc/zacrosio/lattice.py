from __future__ import annotations
from pathlib import Path
from typing import TextIO


def _coord_to_id(ix: int, iy: int, iz: int, nx: int, ny: int, nz: int) -> int:
    """
    Map lattice indices (ix, iy, iz) to a 1-based site ID with full PBC.

    Sites are ordered in row-major fashion:
        id = ix + iy*nx + iz*nx*ny + 1
    """
    ix %= nx
    iy %= ny
    iz %= nz
    return ix + iy * nx + iz * nx * ny + 1


def write_cubic_pbc_lattice(
    nx: int,
    ny: int,
    nz: int,
    outfile: str | Path = "lattice_input.dat",
    site_type_name: str = "G",
    fh: TextIO | None = None,
) -> None:
    """
    Write a Zacros 'lattice explicit' file for a simple cubic lattice
    with full 3D periodic boundary conditions.

    Parameters
    ----------
    nx, ny, nz : int
        Number of lattice sites along x, y, z.
    outfile : str or Path
        Output filename (ignored if `fh` is given).
    site_type_name : str
        Name of the single site type (default: 'G').
    fh : file-like, optional
        If provided, write to this file handle instead of opening `outfile`.
    """
    if nx <= 0 or ny <= 0 or nz <= 0:
        raise ValueError("All lattice dimensions must be positive.")

    n_sites = nx * ny * nz

    need_close = False
    if fh is None:
        fh = open(outfile, "w")
        need_close = True

    f = fh
    try:
        # Header
        f.write("lattice explicit\n")
        f.write(f"n_sites            {n_sites}\n")
        f.write("max_coord          6\n")
        f.write("n_site_types   1\n")
        f.write(f"site_type_names    {site_type_name}\n")
        f.write("lattice_structure\n")

        # Loop over sites and write neighbors
        for iz in range(nz):
            z_frac = iz / nz
            for iy in range(ny):
                y_frac = iy / ny
                for ix in range(nx):
                    x_frac = ix / nx
                    site_id = _coord_to_id(ix, iy, iz, nx, ny, nz)

                    # 6 nearest neighbors in a cubic lattice with full PBC
                    neighbor_ids = [
                        _coord_to_id(ix + 1, iy, iz, nx, ny, nz),
                        _coord_to_id(ix - 1, iy, iz, nx, ny, nz),
                        _coord_to_id(ix, iy + 1, iz, nx, ny, nz),
                        _coord_to_id(ix, iy - 1, iz, nx, ny, nz),
                        _coord_to_id(ix, iy, iz + 1, nx, ny, nz),
                        _coord_to_id(ix, iy, iz - 1, nx, ny, nz),
                    ]

                    # For a cubic lattice with PBC, we should always have 6 unique neighbors
                    # but we sort them to keep the file nicely ordered.
                    neighbor_ids = sorted(set(neighbor_ids))
                    if len(neighbor_ids) != 6:
                        raise RuntimeError(
                            f"Site {site_id} has {len(neighbor_ids)} neighbors; expected 6."
                        )

                    f.write(
                        f"{site_id} {x_frac:.6f} {y_frac:.6f} {z_frac:.6f} "
                        f"{len(neighbor_ids)} "
                        + " ".join(str(n) for n in neighbor_ids)
                        + "\n"
                    )

        f.write("end_lattice_structure\n")
        f.write("end_lattice\n")
    finally:
        if need_close:
            f.close()