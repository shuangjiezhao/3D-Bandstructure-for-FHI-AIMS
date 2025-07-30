#!/usr/bin/env python3
"""
FHI-aims version: Extracts k-points and HOMO/LUMO eigenvalues from band files.
Creates KX.grd, KY.grd, BAND_HOMO.grd, BAND_LUMO.grd for visualization.
"""

import numpy as np
import glob
import re
import sys
from pathlib import Path

def detect_soc(directory="."):
    """Check if SOC calculation based on presence of .no_soc files."""
    no_soc_files = glob.glob(f"{directory}/band*.out.no_soc")
    return len(no_soc_files) > 0

def parse_band_files(directory=".", soc=False):
    """Parse all band files and extract k-points and eigenvalues."""
    # Get all band files
    if soc:
        # For SOC, use the main band files (not .no_soc)
        band_files = sorted(glob.glob(f"{directory}/band*.out"))
        # Remove .no_soc files from the list
        band_files = [f for f in band_files if not f.endswith('.no_soc')]
    else:
        band_files = sorted(glob.glob(f"{directory}/band*.out"))
    
    if not band_files:
        raise ValueError("No band files found in directory")
    
    print(f"Found {len(band_files)} band files")
    print(f"SOC calculation: {soc}")
    
    all_kpoints = []
    all_eigenvalues = []
    all_occupations = []
    
    for band_file in band_files:
        kpoints, eigenvalues, occupations = parse_single_band_file(band_file)
        all_kpoints.extend(kpoints)
        all_eigenvalues.extend(eigenvalues)
        all_occupations.extend(occupations)
    
    return np.array(all_kpoints), np.array(all_eigenvalues), np.array(all_occupations)

def parse_single_band_file(filename):
    """Parse a single band file and return k-points, eigenvalues, and occupations."""
    kpoints = []
    eigenvalues = []
    occupations = []
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 4:
            continue
            
        # First 4 columns: index, kx, ky, kz
        kx, ky, kz = float(parts[1]), float(parts[2]), float(parts[3])
        kpoints.append([kx, ky, kz])
        
        # Remaining columns: pairs of (occupation, eigenvalue)
        band_data = parts[4:]
        occs = []
        eigs = []
        
        for i in range(0, len(band_data), 2):
            if i+1 < len(band_data):
                occs.append(float(band_data[i]))
                eigs.append(float(band_data[i+1]))
        
        occupations.append(occs)
        eigenvalues.append(eigs)
    
    return kpoints, eigenvalues, occupations

def find_homo_lumo_indices(occupations):
    """Find HOMO and LUMO band indices based on occupations."""
    occupations = np.array(occupations)
    n_kpoints, n_bands = occupations.shape
    
    # Find HOMO: highest occupied band (last band with occupation > 0.5)
    homo_idx = -1
    for i in range(n_bands-1, -1, -1):
        if np.any(occupations[:, i] > 0.5):
            homo_idx = i
            break
    
    # Find LUMO: lowest unoccupied band (first band with occupation < 0.5)
    lumo_idx = -1
    for i in range(n_bands):
        if np.all(occupations[:, i] < 0.5):
            lumo_idx = i
            break
    
    return homo_idx, lumo_idx

def read_vbm_cbm_from_output(output_file="aims.out", soc=False):
    """Read VBM and CBM values from FHI-aims output file."""
    vbm, cbm = None, None
    
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        # If SOC, we need to find the SOC-specific values
        in_soc_section = False
        
        for line in lines:
            if "STARTING SECOND VARIATIONAL SOC CALCULATION" in line:
                in_soc_section = True
            
            if soc and in_soc_section:
                if "Highest occupied state (VBM)" in line:
                    vbm = float(line.split()[-2])
                if "Lowest unoccupied state (CBM)" in line:
                    cbm = float(line.split()[-2])
            elif not soc and not in_soc_section:
                if "Highest occupied state (VBM)" in line:
                    vbm = float(line.split()[-2])
                if "Lowest unoccupied state (CBM)" in line:
                    cbm = float(line.split()[-2])
        
        return vbm, cbm
    except:
        print("Warning: Could not read VBM/CBM from output file")
        return None, None

def read_fermi_energy(output_file="aims.out", soc=False):
    """Read Fermi energy from FHI-aims output file."""
    import re
    import glob
    
    # Try to find output file if aims.out doesn't exist
    if not Path(output_file).exists():
        output_files = glob.glob("*.out")
        for f in output_files:
            if "band" not in f and "no_soc" not in f:
                output_file = f
                print(f"Using output file: {output_file}")
                break
        else:
            print("Warning: No output file found")
            return None
    
    fermi_energy = None
    value_pattern = re.compile(r"[-]?(\d+)?\.\d+([E,e][-,+]?\d+)?")
    
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        in_soc_section = False
        
        for line in lines:
            if "STARTING SECOND VARIATIONAL SOC CALCULATION" in line:
                in_soc_section = True
            
            # Handle different output formats
            if soc and in_soc_section:
                if "Chemical potential (Fermi level)" in line:
                    match = value_pattern.search(line)
                    if match:
                        fermi_energy = float(match.group())
            elif not soc and not in_soc_section:
                if "Chemical potential (Fermi level)" in line:
                    match = value_pattern.search(line)
                    if match:
                        fermi_energy = float(match.group())
                        break
                # Handle MD_light format
                elif "| Chemical Potential                          :" in line:
                    match = value_pattern.search(line)
                    if match:
                        fermi_energy = float(match.group())
                        break
        
        if fermi_energy is not None:
            print(f"Found Fermi energy: {fermi_energy} eV")
        else:
            print("Warning: Fermi energy not found in output (using absolute eigenvalues)")
            
        return fermi_energy
    except Exception as e:
        print(f"Warning: Could not read Fermi energy from output file: {e}")
        return None

def save_grid_file(data, filename):
    """Save data to grid file format."""
    with open(filename, 'w') as f:
        for value in data:
            f.write(f"{value:16.8f}\n")

def main(output_file="aims.out"):
    # Detect if SOC calculation
    soc = detect_soc()
    
    print("Parsing FHI-aims band files...")
    kpoints, eigenvalues, occupations = parse_band_files(".", soc)
    print(f"Total k-points: {len(kpoints)}")
    
    # Extract kx, ky
    kx = kpoints[:, 0]
    ky = kpoints[:, 1]
    
    # Save k-point grids
    save_grid_file(kx, "KX.grd")
    save_grid_file(ky, "KY.grd")
    print("Saved KX.grd and KY.grd")
    
    # Find HOMO and LUMO
    homo_idx, lumo_idx = find_homo_lumo_indices(occupations)
    print(f"HOMO band index: {homo_idx}")
    print(f"LUMO band index: {lumo_idx}")
    
    if homo_idx >= 0 and lumo_idx >= 0:
        # Extract HOMO and LUMO eigenvalues
        homo_energies = eigenvalues[:, homo_idx]
        lumo_energies = eigenvalues[:, lumo_idx]
        
        # Note: FHI-aims band files already have eigenvalues referenced to Fermi level
        # So we do NOT need to subtract Fermi energy again!
        fermi_energy = read_fermi_energy(output_file, soc)
        if fermi_energy is not None:
            print(f"Fermi energy from output: {fermi_energy} eV")
            print("Note: Band files already reference eigenvalues to Fermi level")
        
        # Save band grids (already Fermi-referenced)
        save_grid_file(homo_energies, "BAND_HOMO.grd")
        save_grid_file(lumo_energies, "BAND_LUMO.grd")
        print("Saved BAND_HOMO.grd and BAND_LUMO.grd")
        
        # Print some statistics
        print(f"\nHOMO energy range: [{np.min(homo_energies):.4f}, {np.max(homo_energies):.4f}] eV")
        print(f"LUMO energy range: [{np.min(lumo_energies):.4f}, {np.max(lumo_energies):.4f}] eV")
        print(f"Band gap range: [{np.min(lumo_energies - homo_energies):.4f}, {np.max(lumo_energies - homo_energies):.4f}] eV")
    else:
        print("Error: Could not determine HOMO/LUMO bands")

if __name__ == "__main__":
    import sys
    
    # Check if output file is provided as argument
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        # Try to auto-detect
        output_files = glob.glob("*.out")
        output_file = "aims.out"  # default
        for f in output_files:
            if "band" not in f and "no_soc" not in f:
                output_file = f
                print(f"Auto-detected output file: {output_file}")
                break
    
    main(output_file)