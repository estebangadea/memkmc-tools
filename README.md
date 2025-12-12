# memkmc-tools

Utilities for membrane kinetic Monte Carlo (kMC) workflows.

This package (`memkmc`) provides:

- **Voxelization** of LAMMPS membranes into labeled grids.
- **Membrane properties** from atomistic + grid data (λ, FV, VWU, etc.).
- **Zacros input generation** (lattice, initial state, simulation, mechanism, energetics).
- **Post-processing of Zacros runs** (IEC, WU, VH time evolution) and plotting.

---

## Installation

```bash
git clone https://github.com/<your-username>/memkmc-tools.git
cd memkmc-tools

python3 -m venv .venv
source .venv/bin/activate

pip install -e .[dev]
pytest
```
⸻

## Main command-line tools

### 1. Voxelization: memkmc-voxelize

From a LAMMPS data file + type mapping to a 3D grid:

```bash
memkmc-voxelize \
  path/to/membrane.data \
  --format data \
  --types path/to/type_classes.txt \
  --spacing 4.0 \
  --output membrane_grid.xyz
```

type_classes.txt contains atom-type → phase mapping, e.g.:

```text
# type  class
1   polymer
2   polymer
3   tma
4   polymer
5   water
6   water
7   polymer
8   polymer
9   polymer
```

The output membrane_grid.xyz has:

```text
N
<header>
label ix iy iz
...
```

⸻

2. Full Zacros setup from a grid: memkmc-zacros-prepare-run

Given a grid and a label→species mapping, prepare all Zacros inputs for several seeds:

```bash
memkmc-zacros-prepare-run \
  membrane_grid.xyz \
  --mapping label_to_species.txt \
  --seeds 101 102 103 \
  --outdir runs_degradation
```

Where label_to_species.txt maps grid labels to Zacros species, e.g.:

```text
# grid_label  species
1   mw*
3   mem*
4   tma*
```

For each seed, this creates:

```text
runs_degradation/
  seed_<seed>/
    lattice_input.dat      # 3D PBC cubic lattice
    state_input.dat        # initial_state from grid
    simulation_input.dat   # random_seed = <seed>
    mechanism_input.dat    # degradation mechanism (sn2, wat_removal1/2, hew_elimination)
    energetics_input.dat   # uniform site + pair energies
```

You can then cp your Zacros executable/template files into each seed_* directory and run.

Other Zacros-related CLIs (used internally by memkmc-zacros-prepare-run but also callable directly):
	•	memkmc-zacros-lattice – only write lattice_input.dat
	•	memkmc-zacros-initial-state – only write state_input.dat
	•	memkmc-zacros-inputs – only simulation_input.dat + mechanism_input.dat


⸻

3. Analysis: memkmc-analyze (specnum → IEC/WU/VH)

Post-process Zacros species_numbers outputs (e.g. specnum_101.txt) into IEC/WU/VH time series:

```bash
memkmc-analyze specnum_101.txt specnum_102.txt specnum_103.txt
```

This reads each specnum_*.txt and writes:

```text
IEC_WU_specnum_101.dat
IEC_WU_specnum_102.dat
IEC_WU_specnum_103.dat
```

with columns:

```text
time   IEC   WU   VH
```

The formulas match the original workflow:
	•	WU from VWU (linear fit),
	•	IEC from degradation fraction and (Mc, Mn, Md),
	•	VH as (MW + TMA) / (MW + TMA + POL₀).

The implementation lives in memkmc.analysis.specnum.

⸻

4. Plotting: memkmc-plot-iec-wu (IEC/WU → figure)

Plot WU vs IEC curves for multiple runs and their average:

```bash
memkmc-plot-iec-wu \
  IEC_WU_specnum_101.dat \
  IEC_WU_specnum_102.dat \
  IEC_WU_specnum_103.dat \
  -o WUvsIEC.png
```

memkmc-plot-iec-wu \
  IEC_WU_specnum_101.dat \
  IEC_WU_specnum_102.dat \
  IEC_WU_specnum_103.dat \
  -o WUvsIEC.png

```bash
memkmc-voxelize membrane.data --format data --types type_classes.txt --spacing 4.0 --output membrane_grid.xyz
```

2.	Prepare Zacros inputs for a set of seeds:

```bash
memkmc-zacros-prepare-run membrane_grid.xyz \
  --mapping label_to_species.txt \
  --seeds 101 102 103 \
  --outdir runs_degradation
```

3.	Run Zacros in each seed_* directory (e.g. via SLURM).
4.	Analyze specnum_*.txt into IEC/WU/VH:

```bash
memkmc-analyze runs_degradation/seed_*/specnum_*.txt
```

5.	Plot WU vs IEC with the average curve:

```bash
memkmc-plot-iec-wu IEC_WU_specnum_*.dat -o WUvsIEC.png
```

