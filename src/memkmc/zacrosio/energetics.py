from __future__ import annotations
from pathlib import Path
from typing import TextIO


def write_uniform_energetics(
    outfile: str | Path = "energetics_input.dat",
    site_energy_mem: float = -1.0,
    site_energy_mw: float = -1.0,
    site_energy_tma: float = -1.0,
    site_energy_hew: float = -1.0,
    tma_mw_interaction: float = -0.18,
    tma_hew_interaction: float = -0.18,
    fh: TextIO | None = None,
) -> None:
    """
    Write a Zacros energetics_input.dat file for the degradation model,
    matching your current setup:

      - mem_site, mw_site, tma_site, hew_site: site energies
      - tma*-mw* and tma*-hew* pair interactions

    Parameters
    ----------
    outfile : str or Path
        Output file name.
    site_energy_mem, site_energy_mw, site_energy_tma, site_energy_hew : float
        Single-site energies in eV.
    tma_mw_interaction, tma_hew_interaction : float
        Pair interaction energies in eV.
    fh : file-like, optional
        If provided, write to this handle instead of opening `outfile`.
    """
    outfile = Path(outfile)

    need_close = False
    if fh is None:
        fh = open(outfile, "w")
        need_close = True

    try:
        f = fh
        f.write("energetics\n\n")
        f.write("############################################################################\n\n")

        # mem_site
        f.write("cluster mem_site\n")
        f.write("  sites 1\n")
        f.write("  lattice_state\n")
        f.write("    1 mem*   1\n")
        f.write("  site_types G\n")
        f.write("  graph_multiplicity 1\n")
        f.write(f"    cluster_eng {site_energy_mem:.2f} # eV\n")
        f.write("end_cluster\n\n")
        f.write("############################################################################\n")

        # mw_site
        f.write("cluster mw_site\n")
        f.write("  sites 1\n")
        f.write("  lattice_state\n")
        f.write("    1 mw*   1\n")
        f.write("  site_types G\n")
        f.write("  graph_multiplicity 1\n")
        f.write(f"    cluster_eng {site_energy_mw:.2f} # eV\n")
        f.write("end_cluster\n\n")
        f.write("#############################################\n")

        # tma_site
        f.write("cluster tma_site\n")
        f.write("  sites 1\n")
        f.write("  lattice_state\n")
        f.write("    1 tma*   1\n")
        f.write("  site_types G\n")
        f.write("  graph_multiplicity 1\n")
        f.write(f"    cluster_eng {site_energy_tma:.2f} # eV\n")
        f.write("end_cluster\n")
        f.write("############################################################################\n\n")

        # tma*-mw* interaction
        f.write("cluster tma*-mw*_Interaction\n")
        f.write("  sites 2\n")
        f.write("  neighboring 1-2\n")
        f.write("  lattice_state\n")
        f.write("    1 tma*  1\n")
        f.write("    2 mw*   1\n")
        f.write("  site_types G G\n")
        f.write(f"  cluster_eng {tma_mw_interaction:.2f}\n")
        f.write("end_cluster\n")
        f.write("############################################################################\n\n")

        # tma*-hew* interaction
        f.write("cluster tma*-hew*_Interaction\n")
        f.write("  sites 2\n")
        f.write("  neighboring 1-2\n")
        f.write("  lattice_state\n")
        f.write("    1 tma*  1\n")
        f.write("    2 hew*   1\n")
        f.write("  site_types G G\n")
        f.write(f"  cluster_eng {tma_hew_interaction:.2f}\n")
        f.write("end_cluster\n")
        f.write("############################################################################\n\n")

        # hew_site
        f.write("cluster hew_site\n")
        f.write("  sites 1\n")
        f.write("  lattice_state\n")
        f.write("    1 hew*   1\n")
        f.write("  site_types G\n")
        f.write("  graph_multiplicity 1\n")
        f.write(f"    cluster_eng {site_energy_hew:.2f} # eV\n")
        f.write("end_cluster\n\n")
        f.write("############################################################################\n")
        f.write("end_energetics\n")
    finally:
        if need_close:
            fh.close()