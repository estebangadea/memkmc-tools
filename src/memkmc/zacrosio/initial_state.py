from __future__ import annotations
from pathlib import Path
from typing import Dict, TextIO


def load_label_to_species(path: str | Path) -> Dict[int, str]:
    """
    Load a mapping from integer grid labels to Zacros species names.

    File format:
        # label  species
        1        mw*
        3        mem*
        4        tma*

    Lines starting with '#' or blank lines are ignored.
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
            lab = int(parts[0])
            species = parts[1]
            mapping[lab] = species
    if not mapping:
        raise ValueError(f"No label→species mappings found in {path!r}.")
    return mapping


def write_initial_state_from_grid(
    grid_xyz: str | Path,
    outfile: str | Path = "state_input.dat",
    label_to_species: Dict[int, str] | None = None,
    mapping_file: str | Path | None = None,
    fh: TextIO | None = None,
) -> None:
    """
    Generate a Zacros initial_state file from a membrane grid in XYZ-like format.

    The grid file is expected to have the format produced by `write_grid_xyz`:

        N
        <header/comment line>
        label ix iy iz
        label ix iy iz
        ...

    Each grid line corresponds to a lattice site, in the same ordering as the
    lattice_input file.

    This function writes lines of the form:

        seed_on_sites <species> <site_id>

    where `<species>` is taken from `label_to_species[label]`.

    Parameters
    ----------
    grid_xyz : str or Path
        Path to the grid XYZ file.
    outfile : str or Path
        Where to write the Zacros initial_state file (ignored if `fh` is given).
    label_to_species : dict, optional
        Mapping from integer grid labels to Zacros species names. If not given,
        `mapping_file` must be provided.
    mapping_file : str or Path, optional
        Path to a text file with "label species" mapping lines.
    fh : file-like, optional
        If provided, write to this file handle instead of opening `outfile`.
    """
    grid_xyz = Path(grid_xyz)

    if label_to_species is None:
        if mapping_file is None:
            raise ValueError(
                "Either `label_to_species` or `mapping_file` must be provided."
            )
        label_to_species = load_label_to_species(mapping_file)

    need_close = False
    if fh is None:
        fh = open(outfile, "w")
        need_close = True

    try:
        f = fh
        f.write("initial_state\n")

        with grid_xyz.open("r") as g:
            # Skip the first two header lines (N, comment/blank)
            # and then iterate over the grid lines.
            for line_number, line in enumerate(g):
                if line_number < 2:
                    continue
                parts = line.split()
                if not parts:
                    continue

                label = int(parts[0])

                species = label_to_species.get(label)
                if species is None:
                    # Skip voxels that don't correspond to a species
                    continue

                # Site IDs start at 1 and increase by 1 per grid line,
                # exactly like the original script's (line_number-1).
                site_id = line_number - 1
                f.write(f"seed_on_sites {species} {site_id}\n")

        f.write("end_initial_state\n")
    finally:
        if need_close:
            fh.close()