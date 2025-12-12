from __future__ import annotations
from pathlib import Path
from typing import Iterable, TextIO, Sequence


def write_simulation_input(
    outfile: str | Path,
    random_seed: int,
    temperature: float = 300.0,
    pressure: float = 1.0,
    gas_names: Sequence[str] = ("tma", "mem", "mw"),
    gas_energies: Sequence[float] = (0.0, 0.0, 0.0),
    gas_weights: Sequence[float] = (18.0, 18.0, 18.0),  # g/mol
    gas_fracs: Sequence[float] = (0.0, 0.0, 0.0),
    surf_species: Sequence[str] = ("tma*", "mem*", "mw*", "hew*"),
    surf_dent: Sequence[int] = (1, 1, 1, 1),
    snapshots_event: int = 100,
    process_statistics_event: int = 100,
    species_numbers_event: int = 5,
    max_steps: int = 80000,
    max_time: str = "infinity",
    wall_time: int = 100800,
    fh: TextIO | None = None,
) -> None:
    """
    Write a Zacros simulation_input.dat file for the degradation model.

    Parameters match your original script, but are configurable.
    """
    outfile = Path(outfile)
    n_gas = len(gas_names)
    n_surf = len(surf_species)

    if not (len(gas_energies) == len(gas_weights) == len(gas_fracs) == n_gas):
        raise ValueError("Gas arrays must all have the same length as gas_names.")
    if len(surf_dent) != n_surf:
        raise ValueError("surf_dent must have the same length as surf_species.")

    need_close = False
    if fh is None:
        fh = open(outfile, "w")
        need_close = True

    try:
        f = fh
        f.write(f"random_seed               {random_seed}\n\n")
        f.write(f"temperature               {temperature:.2f}\n")
        f.write(f"pressure                  {pressure:.2f}\n\n")

        f.write(f"n_gas_species             {n_gas}\n")
        f.write("gas_specs_names           ")
        for name in gas_names:
            f.write(f"{name:>6s} ")
        f.write("\n")

        f.write("gas_energies              ")
        for e in gas_energies:
            f.write(f"{e:>7.3f} ")
        f.write("# eV\n")

        f.write("gas_molec_weights         ")
        for w in gas_weights:
            f.write(f"{w:>7.2f} ")
        f.write("# g/mol\n")

        f.write("gas_molar_fracs           ")
        for x in gas_fracs:
            f.write(f"{x:>7.3f} ")
        f.write("\n\n")

        f.write(f"n_surf_species            {n_surf}\n")
        f.write("surf_specs_names          ")
        for name in surf_species:
            f.write(f"{name:>4s} ")
        f.write("\n")

        f.write("surf_specs_dent           ")
        for d in surf_dent:
            f.write(f"{d:>4d} ")
        f.write("\n\n")

        f.write(f"snapshots                 on event {snapshots_event}\n")
        f.write(f"process_statistics        on event {process_statistics_event}\n")
        f.write(f"species_numbers           on event {species_numbers_event}\n\n")

        # f.write("# event_report              on\n\n")

        f.write(f"max_steps                 {max_steps}\n")
        f.write(f"max_time                  {max_time}\n\n")

        f.write(f"wall_time                 {wall_time} # in seconds\n\n")
        f.write("finish\n")
    finally:
        if need_close:
            fh.close()