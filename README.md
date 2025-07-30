
# 3D Band Structure Workflow for FHI-aims

This repository provides a Python-based toolkit for generating and visualizing **3D band structure surfaces** from **FHI-aims** simulations. It is ideal for exploring fine band features like Dirac cones and small band gaps in 2D or layered systems.

---

## 📁 Contents

| File | Description |
|------|-------------|
| `kpoints_gui_weighted.py` | GUI tool to generate two-tier FHI-aims `output band` lines around a symmetry point (e.g., Γ, K, M). |
| `aims_kpoints_grid.py`    | Parses FHI-aims `band*.out` files, extracts k-points and eigenvalues, and creates `.grd` files for visualization. |
| `visualization.py`        | Visualizes HOMO/LUMO surfaces over reciprocal space from `.grd` data. |

---

## 🧪 Workflow Overview

1. Generate `output band` lines using the GUI.
2. Run the FHI-aims calculation to obtain `band*.out` files.
3. Extract k-points and band energies using `aims_kpoints_grid.py`.
4. Visualize the 3D band surfaces using `visualization.py`.

---

## 🔹 Step 1: Generate Band Lines with GUI

Run:

```bash
python3 kpoints_gui_weighted.py
```

### 🎛️ GUI Features:

- Define the symmetry center point (G, K, or M).
- Set `sparse` and `dense` x-ranges for a two-tier k-point scan.
- Automatically ensures that the high-symmetry point is included.
- Removes duplicate lines and highlights the center line.
- Visual preview available.
- Saves formatted `output band ...` lines for inclusion in FHI-aims control files.

📄 **Output:** A `.txt` file with all `output band` lines, ready to be copied into your FHI-aims input file.

---

## 🔹 Step 2: Run FHI-aims with Band Line Output

- Place the generated band lines into your `control.in` file.
- Run the FHI-aims calculation as usual.
- Ensure that `band*.out` files are generated in the directory.

---

## 🔹 Step 3: Extract HOMO/LUMO from Band Files

Run:

```bash
python3 aims_kpoints_grid.py
```

This will:

- Auto-detect SOC vs non-SOC calculations.
- Read `band*.out` files and the main `aims.out`.
- Identify HOMO and LUMO band indices.
- Save:

| File | Content |
|------|---------|
| `KX.grd`, `KY.grd` | k-point coordinates |
| `BAND_HOMO.grd` | HOMO energies |
| `BAND_LUMO.grd` | LUMO energies |

> Energies are already referenced to the Fermi level by FHI-aims.

---

## 🔹 Step 4: Visualize 3D Band Surfaces

Run:

```bash
python3 visualization.py
```

Features:

- 3D surface plots of HOMO and LUMO over k-space.
- Detect band gaps, crossings, and curvature.
- Ideal for visualizing Dirac cones or flat bands.

---

## 📥 Requirements

Install dependencies with:

```bash
pip install numpy matplotlib pyvista
```

Also requires `tkinter` (for the GUI).

---

## 📄 License

MIT License — Free to use, modify, and share.

---
