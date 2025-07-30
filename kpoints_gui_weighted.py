import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox

def remove_duplicate_lines(x_positions, tolerance=1e-8):
    """Remove duplicate x positions within tolerance."""
    unique_positions = []
    for x in x_positions:
        is_duplicate = False
        for ux in unique_positions:
            if abs(x - ux) < tolerance:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_positions.append(x)
    return np.sort(unique_positions)

def generate_band_lines(center_point, sparse_x_range, sparse_density, 
                       cone_x_range, cone_density, y_range, 
                       points_per_line, output_file):
    """Generate FHI-aims output band lines with sparse and dense regions."""
    
    # Define high-symmetry points
    centers = {
        "G": (0.0, 0.0, 0.0),
        "K": (1/3, 1/3, 0.0),
        "M": (0.5, 0.0, 0.0),
    }
    
    center_point = center_point.upper()
    if center_point not in centers:
        raise ValueError(f"Unknown center point: {center_point}. Choose from G, K, or M.")
    
    cx, cy, cz = centers[center_point]
    
    # Parse ranges
    sparse_x_min, sparse_x_max = map(float, sparse_x_range.split(","))
    cone_x_min, cone_x_max = map(float, cone_x_range.split(","))
    y_start, y_end = map(float, y_range.split(","))
    
    # Generate sparse grid positions
    sparse_x_positions = np.linspace(sparse_x_min, sparse_x_max, sparse_density)
    
    # Generate dense grid positions around Dirac cone
    cone_x_positions = np.linspace(cone_x_min, cone_x_max, cone_density)
    
    # Ensure the cone grid includes the center point
    distances = np.abs(cone_x_positions - cx)
    closest_idx = np.argmin(distances)
    if distances[closest_idx] > 1e-6:
        # Replace the closest position with the exact center
        cone_x_positions[closest_idx] = cx
    
    # Combine all positions
    all_x_positions = np.concatenate([sparse_x_positions, cone_x_positions])
    
    # Remove duplicates and sort
    unique_x_positions = remove_duplicate_lines(all_x_positions)
    
    # Generate output band lines
    lines = []
    center_line_idx = None
    
    for i, x in enumerate(unique_x_positions):
        # Start and end points of the line
        start_point = f"{x:16.12f} {y_start:16.12f} {cz:16.12f}"
        end_point = f"{x:16.12f} {y_end:16.12f} {cz:16.12f}"
        
        # Generate labels
        label_start = f"{center_point}{i+1}"
        label_end = f"A{i+1}"
        
        # Special label for the line through the center
        if abs(x - cx) < 1e-6:
            label_start = f"{center_point}*"
            label_end = "A*"
            center_line_idx = i
        
        # Format the output band line
        line = f"output band {start_point} {end_point} {points_per_line:4d} {label_start} {label_end}"
        lines.append(line)
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(f"# FHI-aims band structure lines around {center_point} point\n")
        f.write(f"# Sparse grid: {sparse_density} lines from x={sparse_x_min} to x={sparse_x_max}\n")
        f.write(f"# Dense grid: {cone_density} lines from x={cone_x_min} to x={cone_x_max}\n")
        f.write(f"# Total unique lines: {len(unique_x_positions)}\n")
        if center_line_idx is not None:
            f.write(f"# Center line at index {center_line_idx+1} (marked with *)\n")
        f.write(f"# Each line goes from y={y_start} to y={y_end} with {points_per_line} points\n\n")
        
        for line in lines:
            f.write(line + "\n")
    
    return lines, unique_x_positions

def visualize_lines(center_point, sparse_x_range, sparse_density, 
                   cone_x_range, cone_density, y_range):
    """Visualize the generated k-path lines with sparse and dense regions."""
    try:
        import matplotlib.pyplot as plt
        
        centers = {
            "G": (0.0, 0.0),
            "K": (1/3, 1/3),
            "M": (0.5, 0.0),
        }
        
        cx, cy = centers[center_point.upper()][:2]
        
        # Parse ranges
        sparse_x_min, sparse_x_max = map(float, sparse_x_range.split(","))
        cone_x_min, cone_x_max = map(float, cone_x_range.split(","))
        y_start, y_end = map(float, y_range.split(","))
        
        # Generate positions
        sparse_x = np.linspace(sparse_x_min, sparse_x_max, sparse_density)
        cone_x = np.linspace(cone_x_min, cone_x_max, cone_density)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot sparse lines
        for x in sparse_x:
            ax.plot([x, x], [y_start, y_end], 'b-', alpha=0.3, linewidth=1, label='Sparse' if x == sparse_x[0] else '')
        
        # Plot dense lines
        for x in cone_x:
            ax.plot([x, x], [y_start, y_end], 'r-', alpha=0.6, linewidth=1.5, label='Dense' if x == cone_x[0] else '')
        
        # Highlight the center point
        ax.plot(cx, cy, 'k*', markersize=20, label=f'{center_point} point')
        ax.axvline(cx, color='k', linestyle='--', alpha=0.5, linewidth=0.8)
        
        # Add shaded regions
        ax.axvspan(cone_x_min, cone_x_max, alpha=0.1, color='red', label='Dense region')
        ax.axvspan(sparse_x_min, sparse_x_max, alpha=0.05, color='blue', label='Sparse region')
        
        # Add labels
        ax.set_xlabel('$k_x$')
        ax.set_ylabel('$k_y$')
        ax.set_title(f'Band Structure Lines around {center_point} point')
        ax.grid(True, alpha=0.3)
        
        # Custom legend to avoid duplicates
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='best')
        
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("Matplotlib not available for visualization")

def launch_gui():
    """Launch the GUI for FHI-aims band structure lines generation."""
    root = tk.Tk()
    root.title("FHI-aims Band Structure Lines Generator (Two-tier)")
    root.geometry("500x450")

    labels = [
        "Center point (G, K, or M):",
        "Sparse X range (min,max):",
        "Sparse density (number of lines):",
        "Cone X range (min,max):",
        "Cone density (number of lines):",
        "Y range for all lines (start,end):",
        "Points per line:",
    ]
    entries = []

    for i, label in enumerate(labels):
        tk.Label(root, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=5)
        e = tk.Entry(root, width=25)
        e.grid(row=i, column=1, padx=5, pady=5)
        entries.append(e)

    # Set default values
    entries[0].insert(0, "G")  # Center point
    entries[1].insert(0, "-0.2,0.2")  # Sparse X range
    entries[2].insert(0, "10")  # Sparse density
    entries[3].insert(0, "-0.05,0.05")  # Cone X range
    entries[4].insert(0, "10")  # Cone density
    entries[5].insert(0, "0.0,0.5")  # Y range
    entries[6].insert(0, "41")  # Points per line

    # Add example text
    example_text = """Example for Gamma point:
    Sparse grid: 10 lines from -0.2 to 0.2
    Dense grid: 10 lines from -0.05 to 0.05 (includes Γ)
    
Example for K point:
    Sparse grid: 10 lines from 0.133 to 0.533 (K_x ± 0.2)
    Dense grid: 10 lines from 0.283 to 0.383 (K_x ± 0.05, includes K)"""
    
    tk.Label(root, text=example_text, font=("Arial", 9), fg="gray", justify="left").grid(
        row=len(labels), column=0, columnspan=2, padx=5, pady=10)

    def submit():
        try:
            center_point = entries[0].get().strip()
            sparse_x_range = entries[1].get().strip()
            sparse_density = int(entries[2].get().strip())
            cone_x_range = entries[3].get().strip()
            cone_density = int(entries[4].get().strip())
            y_range = entries[5].get().strip()
            points_per_line = int(entries[6].get().strip())

            # Validate inputs
            if not all([center_point, sparse_x_range, cone_x_range, y_range]):
                raise ValueError("Please fill in all fields")

            output_file = filedialog.asksaveasfilename(
                defaultextension=".txt", 
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"band_lines_{center_point.lower()}_twotier.txt"
            )
            if not output_file:
                return

            lines, x_positions = generate_band_lines(
                center_point, sparse_x_range, sparse_density,
                cone_x_range, cone_density, y_range, 
                points_per_line, output_file
            )
            
            # Show statistics
            stats = f"Generated band structure lines:\n"
            stats += f"- Sparse grid: {sparse_density} lines requested\n"
            stats += f"- Dense grid: {cone_density} lines requested\n"
            stats += f"- Total unique lines: {len(lines)}\n"
            stats += f"- Duplicates removed: {sparse_density + cone_density - len(lines)}\n"
            stats += f"\nSaved to: {output_file}"
            
            messagebox.showinfo("Success", stats)
            
            # Optional visualization
            try:
                visualize_lines(center_point, sparse_x_range, sparse_density,
                              cone_x_range, cone_density, y_range)
            except:
                pass
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def show_help():
        help_text = """This tool generates two-tier band structure lines for FHI-aims:

1. SPARSE GRID: Background coverage over a wider range
   - Does NOT need to include the center point
   
2. DENSE GRID: Detailed coverage around the Dirac cone
   - ALWAYS includes the exact center point
   
The tool automatically:
- Removes duplicate lines
- Sorts lines by x-coordinate
- Marks the center line with * in labels

Output format:
output band start_kx start_ky start_kz end_kx end_ky end_kz n_points label_start label_end"""
        
        messagebox.showinfo("Help", help_text)

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.grid(row=len(labels)+1, column=0, columnspan=2, pady=10)
    
    tk.Button(button_frame, text="Generate Lines", command=submit, 
              bg="lightblue", width=15).pack(side="left", padx=5)
    tk.Button(button_frame, text="Help", command=show_help, 
              width=10).pack(side="left", padx=5)

    root.mainloop()

if __name__ == "__main__":
    launch_gui()