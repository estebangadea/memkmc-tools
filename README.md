# memkmc-tools

Tools for voxelization, Zacros input generation, and post-processing of
kinetic Monte Carlo simulations in heterogeneous membranes.

## Features (planned)

- **Voxelization** of atomistic or coarse-grained structures into 3D grids
  suitable for kMC and percolation analysis.
- **Zacros input generation** from voxelized membranes and reaction models.
- **Post-processing and analysis** of Zacros simulations:
  coverages, TOFs, percolation, and custom observables.

The initial goal is to consolidate a working research workflow into a
reusable Python toolkit with simple command-line interfaces.

## Installation (development)

Clone the repository and install in editable mode:

```bash
git clone https://github.com/<your-username>/memkmc-tools.git
cd memkmc-tools
pip install -e .
