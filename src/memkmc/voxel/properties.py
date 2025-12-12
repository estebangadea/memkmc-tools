from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Mapping, Tuple
import numpy as np


@dataclass
class ParticleCounts:
    """Counts of particles by class (from atomistic data)."""
    total: int
    by_class: Dict[str, int]


@dataclass
class GridCounts:
    """Counts of voxels by class (from the label grid)."""
    total: int
    by_class: Dict[str, int]


@dataclass
class MembraneProperties:
    """Membrane properties, mirroring the original report.dat layout."""
    n_water: int
    n_tma: int
    lam: float        # lambda (water / TMA)
    iec: float | None # Ion-exchange capacity (user-defined formula)
    wu: float | None  # Water uptake (user-defined formula)
    fv: float         # water voxel fraction (excluding TMA voxels)
    vwu: float        # water voxels / non-water voxels

    n_part: int
    n_water_grid: int
    n_tma_grid: int
    n_pol_grid: int   # "non-TMA" in original script


def count_particles(
    types: np.ndarray,
    type_to_class: Mapping[int, str],
) -> ParticleCounts:
    """
    Count particles by abstract class (water, polymer, tma, ...).

    Parameters
    ----------
    types : (N,) int
        LAMMPS atom types.
    type_to_class : mapping
        type_id -> class_name (e.g. 5 -> "water").

    Returns
    -------
    ParticleCounts
    """
    total = int(types.size)
    by_class: Dict[str, int] = {}
    for t in types:
        cls = type_to_class.get(int(t), "unknown")
        by_class[cls] = by_class.get(cls, 0) + 1
    return ParticleCounts(total=total, by_class=by_class)


def count_grid_voxels(
    labels: np.ndarray,
    class_to_int: Mapping[str, int],
) -> GridCounts:
    """
    Count voxels by class from a label grid.

    Parameters
    ----------
    labels : (nx, ny, nz) int
        Grid of labels.
    class_to_int : mapping
        class_name -> integer label used in `labels`.

    Returns
    -------
    GridCounts
    """
    total = int(labels.size)
    by_class: Dict[str, int] = {}

    # Build inverse mapping int -> class_name
    int_to_class = {v: k for k, v in class_to_int.items()}

    unique, counts = np.unique(labels, return_counts=True)
    for lab, cnt in zip(unique, counts):
        cls = int_to_class.get(int(lab), "unknown")
        by_class[cls] = by_class.get(cls, 0) + int(cnt)

    return GridCounts(total=total, by_class=by_class)


def compute_lambda(particle_counts: ParticleCounts) -> float:
    """Compute lambda = N_water / N_tma."""
    n_water = particle_counts.by_class.get("water", 0)
    n_tma = particle_counts.by_class.get("tma", 0)
    if n_tma == 0:
        raise ValueError("Cannot compute lambda: no TMA particles.")
    return n_water / n_tma


def compute_grid_fractions(
    grid_counts: GridCounts,
) -> Tuple[float, float]:
    """
    Compute FV and VWU from grid voxel counts, reproducing the original script:

        FV  = N_water_grid / (N_total - N_tma_grid)
        VWU = N_water_grid / (N_total - N_water_grid)
    """
    total = grid_counts.total
    n_water_g = grid_counts.by_class.get("water", 0)
    n_tma_g = grid_counts.by_class.get("tma", 0)

    if total <= 0:
        raise ValueError("Grid has zero voxels.")

    fv_den = total - n_tma_g
    vwu_den = total - n_water_g

    fv = n_water_g / fv_den if fv_den > 0 else 0.0
    vwu = n_water_g / vwu_den if vwu_den > 0 else 0.0

    return fv, vwu


def compute_water_uptake(
    particle_counts: ParticleCounts,
    mass_by_class: Mapping[str, float],
) -> float:
    """
    Compute water uptake WU given per-particle masses for each class.

    This is a general mass-based definition:

        WU = m_water / (m_water + m_dry)

    where `m_dry` can include polymer, TMA, counterions, etc., depending on
    how you populate `mass_by_class`.

    Example (your case):
        mass_by_class = {
            "water": 18.0,
            "polymer": M_polymer_unit,
            "tma": M_TMA,
            "cl": 35.5,
        }

    You can customize this per system.
    """
    # total mass per class
    m_water = 0.0
    m_dry = 0.0
    for cls, n in particle_counts.by_class.items():
        m_cls = mass_by_class.get(cls)
        if m_cls is None:
            continue
        m_total = m_cls * n
        if cls == "water":
            m_water += m_total
        else:
            m_dry += m_total

    if m_water + m_dry == 0.0:
        raise ValueError("Total mass is zero; cannot compute WU.")
    return m_water / (m_water + m_dry)


def compute_iec(
    particle_counts: ParticleCounts,
    mass_dry: float,
    charge_per_tma: int = 1,
    use_moles: bool = True,
) -> float:
    """
    Compute IEC (ion-exchange capacity).

    Generic, physically reasonable version:

        IEC [eq / g] = (z * N_TMA / N_A) / mass_dry

    If `use_moles=False`, you can instead work in arbitrary units where IEC
    is simply proportional to N_TMA / mass_dry.

    Parameters
    ----------
    particle_counts : ParticleCounts
    mass_dry : float
        Dry membrane mass (polymer + fixed charged groups + counterions), in g.
    charge_per_tma : int
        Valence of the fixed cation (usually +1 for TMA).
    use_moles : bool
        If False, returns N_TMA / mass_dry (your old script may have effectively
        done this without Avogadro factors).

    Returns
    -------
    IEC value.
    """
    n_tma = particle_counts.by_class.get("tma", 0)
    if mass_dry <= 0.0:
        raise ValueError("mass_dry must be positive.")

    if not use_moles:
        # Simple proportional measure
        return n_tma * charge_per_tma / mass_dry

    N_A = 6.02214076e23
    moles = n_tma / N_A
    # equivalents == z * moles
    eq = charge_per_tma * moles
    # eq per gram
    return eq / mass_dry


def build_properties(
    particle_counts: ParticleCounts,
    grid_counts: GridCounts,
    iec: float | None = None,
    wu: float | None = None,
) -> MembraneProperties:
    """
    Assemble a MembraneProperties object using the established formulas.

    IEC and WU can be precomputed using `compute_iec` / `compute_water_uptake`
    and passed in, or left as None if you only care about the grid-based
    properties (lambda, FV, VWU).
    """
    n_water = particle_counts.by_class.get("water", 0)
    n_tma = particle_counts.by_class.get("tma", 0)
    lam = compute_lambda(particle_counts)

    fv, vwu = compute_grid_fractions(grid_counts)

    n_water_grid = grid_counts.by_class.get("water", 0)
    n_tma_grid = grid_counts.by_class.get("tma", 0)
    # In your original script this was "N_polG" but actually used
    # grid_x*grid_y*grid_z - tma_g (i.e. all non-TMA voxels).
    n_pol_grid = grid_counts.total - n_tma_grid

    return MembraneProperties(
        n_water=n_water,
        n_tma=n_tma,
        lam=lam,
        iec=iec,
        wu=wu,
        fv=fv,
        vwu=vwu,
        n_part=particle_counts.total,
        n_water_grid=n_water_grid,
        n_tma_grid=n_tma_grid,
        n_pol_grid=n_pol_grid,
    )