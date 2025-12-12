from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np


@dataclass
class SpecnumAnalysisResult:
    """Result of analyzing a Zacros species_numbers file."""
    time: np.ndarray
    tma: np.ndarray
    pol: np.ndarray
    mw: np.ndarray
    iec: np.ndarray
    wu: np.ndarray
    vh: np.ndarray  # hydrophilic volume fraction


def _read_specnum(path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read a specnum_*.txt file and return time, TMA, POL, MW arrays.

    Assumes:
        - First line is a header.
        - Columns such that:
            time = col 3
            TMA  = col 6
            POL  = col 7
            MW   = col 8
        (0-based indices 2, 5, 6, 7)
    """
    path = Path(path)
    time: list[float] = []
    tma: list[float] = []
    pol: list[float] = []
    mw: list[float] = []

    with path.open("r") as f:
        lines = f.readlines()

    for line in lines[1:]:  # skip header
        parts = line.split()
        if len(parts) < 8:
            continue
        time.append(float(parts[2]))
        tma.append(float(parts[5]))
        pol.append(float(parts[6]))
        mw.append(float(parts[7]))

    if not time:
        raise ValueError(f"No data lines found in {path}")

    return (
        np.array(time, dtype=float),
        np.array(tma, dtype=float),
        np.array(pol, dtype=float),
        np.array(mw, dtype=float),
    )


def analyze_specnum_file(path: str | Path) -> SpecnumAnalysisResult:
    """Compute IEC, WU, and VH from a specnum_*.txt file.

    This reproduces the original script's formulas:

        VWU = MW[j] / (POL[0] + TMA[0])
        WU  = 0.74637 * VWU - 0.07734

        deg = (TMA[0] - TMA[j]) / TMA[0]
        IEC = 1000 * 0.33 * (1 - deg) / (
              0.33 * (1 - deg) * Mc + 0.67 * Mn + deg * 0.33 * Md
        )

        VH  = (MW[j] + TMA[j]) / (MW[j] + TMA[j] + POL[0])

    with:
        Mc = 192.28
        Mn = 118.133
        Md = 118.133 + 14 + 13
    """
    time, tma, pol, mw = _read_specnum(path)

    Mc = 192.28
    Mn = 118.133
    Md = 118.133 + 14.0 + 13.0

    tma0 = tma[0]
    pol0 = pol[0]

    if tma0 == 0.0:
        raise ValueError("Initial TMA count is zero; cannot compute degradation fraction.")

    # VWU, WU
    denom_vwu = pol0 + tma0
    if denom_vwu == 0.0:
        raise ValueError("POL[0] + TMA[0] == 0; cannot compute VWU.")

    vwu = mw / denom_vwu
    wu = 0.74637 * vwu - 0.07734

    # Degradation fraction and IEC
    deg = (tma0 - tma) / tma0
    # Ensure deg stays within [0, 1] numerically
    deg = np.clip(deg, 0.0, 1.0)

    num = 1000.0 * 0.33 * (1.0 - deg)
    den = 0.33 * (1.0 - deg) * Mc + 0.67 * Mn + deg * 0.33 * Md
    iec = num / den

    # Hydrophilic volume fraction VH
    vh = (mw + tma) / (mw + tma + pol0)

    return SpecnumAnalysisResult(
        time=time,
        tma=tma,
        pol=pol,
        mw=mw,
        iec=iec,
        wu=wu,
        vh=vh,
    )


def write_iec_wu_file(
    result: SpecnumAnalysisResult,
    outfile: str | Path,
    header: str = "time\tIEC\tWU\tVH\n",
) -> None:
    """Write time, IEC, WU, VH to a .dat file."""
    outfile = Path(outfile)
    with outfile.open("w") as f:
        f.write(header)
        for t, iec, wu, vh in zip(
            result.time, result.iec, result.wu, result.vh
        ):
            f.write(f"{t:8.4f}\t{iec:8.4f}\t{wu:8.4f}\t{vh:8.4f}\n")