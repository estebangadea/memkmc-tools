from __future__ import annotations
from pathlib import Path
from typing import TextIO


def write_degradation_mechanism(
    outfile: str | Path,
    ke: float = 0.5,
    kwe: float = 2.5e12,
    km: float = 1.0e11,
    kd: float = 1.0e8,
    fh: TextIO | None = None,
) -> None:
    """
    Write the degradation mechanism_input.dat file with four steps:

    - sn2_degradation (pre_expon = ke)
    - wat_removal1   (pre_expon = kwe)
    - wat_removal2   (pre_expon = km)
    - hew_elimination(pre_expon = kd)
    """
    outfile = Path(outfile)
    need_close = False
    if fh is None:
        fh = open(outfile, "w")
        need_close = True

    try:
        f = fh
        f.write("mechanism\n\n")
        f.write("############################################################################\n\n")

        # sn2_degradation
        f.write("step sn2_degradation\n")
        f.write("  sites 2\n")
        f.write("  neighboring 1-2\n")
        f.write("  initial # (entitynumber, species, dentate)\n")
        f.write("    1 tma*    1\n")
        f.write("    2 mw*     1\n")
        f.write("  final\n")
        f.write("    1 mem* 1\n")
        f.write("    2 hew* 1\n")
        f.write("  site_types G G\n")
        f.write(f"  pre_expon  {ke:g}\n")
        f.write("  activ_eng  0.00\n")
        f.write("end_step\n\n")
        f.write("############################################################################\n\n")

        # wat_removal1
        f.write("step wat_removal1\n")
        f.write("  sites 3\n")
        f.write("  neighboring 1-2 2-3\n")
        f.write("  initial # (entitynumber, species, dentate)\n")
        f.write("    1 mw*    1\n")
        f.write("    2 hew*   1\n")
        f.write("    3 mem*   1\n")
        f.write("  final\n")
        f.write("    1 hew* 1\n")
        f.write("    2 mem* 1\n")
        f.write("    3 mem* 1\n")
        f.write("  site_types G G G\n")
        f.write(f"  pre_expon  {kwe:g}\n")
        f.write("  activ_eng  0.05\n")
        f.write("end_step\n")
        f.write("############################################################################\n")
        f.write("############################################################################\n\n")

        # wat_removal2
        f.write("step wat_removal2\n")
        f.write("  sites 2\n")
        f.write("  neighboring 1-2\n")
        f.write("  initial # (entitynumber, species, dentate)\n")
        f.write("    1 hew*    1\n")
        f.write("    2 mw*     1\n")
        f.write("  final\n")
        f.write("    1 mw*     1\n")
        f.write("    2 hew*    1\n")
        f.write("  site_types G G\n")
        f.write(f"  pre_expon  {km:g}\n")
        f.write("  activ_eng  0.05\n")
        f.write("end_step\n\n")
        f.write("############################################################################\n\n")

        # hew_elimination
        f.write("step hew_elimination\n")
        f.write("  sites 2\n")
        f.write("  neighboring 1-2\n")
        f.write("  initial # (entitynumber, species, dentate)\n")
        f.write("    1 hew*    1\n")
        f.write("    2 mem*    1\n")
        f.write("  final\n")
        f.write("    1 mem* 1\n")
        f.write("    2 mem* 1\n")
        f.write("  site_types G G\n")
        f.write(f"  pre_expon  {kd:g}\n")
        f.write("  activ_eng  0.05\n")
        f.write("end_step\n")
        f.write("############################################################################\n")
        f.write("end_mechanism\n")
    finally:
        if need_close:
            fh.close()