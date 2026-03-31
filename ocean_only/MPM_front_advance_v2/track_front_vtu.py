"""
track_front_vtu.py  --  Track the calving front position from MPM particle
                        VTU output and compare to the analytical solution
                        (Huth et al. 2021, Eq. 47).

Eq. 47 (mass conservation Q0*t = integral_0^xc H(x) dx, with steady-state
SSA n=3 thickness profile H(x) = H0*(1 + 4*C*H0^3*x/v0)^(-1/4)):

    xc(t) = v0/(4*epsilon) * [(1 + 3*epsilon*t)^(4/3) - 1]

    where:
        Q0      = v0 * H0               [m^2/s]  inflow volume flux
        C       = A * (rho_i*g*(1-rho_i/rho_w)/4)^n   [Pa^-n s^-1]
        epsilon = C * H0^n              [s^-1]   strain rate at inflow

Front detection from VTU:
    x_front = max(x_particle + 0.5 * Lx_m) - x_inflow

Usage:
    python track_front_vtu.py [--vtu-dir VTU] [--no-plot]
"""

import os
import re
import sys
import glob
import argparse
import xml.etree.ElementTree as ET
import numpy as np

# ---------------------------------------------------------------------------
# Physical parameters (Huth et al. 2021, Section 5.1)
# ---------------------------------------------------------------------------
rho_i    = 910.0          # [kg m^-3]
rho_w    = 1028.0         # [kg m^-3]
g        = 9.81           # [m s^-2]
H0       = 600.0          # [m]  inflow thickness
B0       = 1.9e8          # [Pa s^(1/3)]  Glen's law rate factor
n_glen   = 3
A_glen   = B0**(-n_glen)  # [Pa^-3 s^-1]
s_per_yr = 31536000.0     # [s yr^-1]
v0       = 300.0 / s_per_yr  # [m s^-1]  inflow velocity

# Eq. 47 parameters
Q0      = v0 * H0                                         # [m^2 s^-1]
C       = A_glen * (rho_i * g * (1.0 - rho_i / rho_w) / 4.0)**n_glen  # [Pa^-3 s^-1]
epsilon = C * H0**n_glen                                  # [s^-1]
x_inflow = 200.0e3                                        # [m]

def xc_analytic(t_s):
    """Eq. 47: front position [m] relative to inflow at time t [s]."""
    return (v0 / (4.0 * epsilon)) * ((1.0 + 3.0 * epsilon * t_s)**(4.0 / 3.0) - 1.0)


# ---------------------------------------------------------------------------
# VTU parsing (ASCII XML format)
# ---------------------------------------------------------------------------
def read_vtu_points_and_field(path, field_name):
    """Return (x_coords [m], field_values) from an ASCII VTU file."""
    tree = ET.parse(path)
    root = tree.getroot()

    # Points coordinates
    pts_elem = root.find("./UnstructuredGrid/Piece/Points/DataArray")
    pts = np.fromstring(pts_elem.text, sep="\n" if "\n" in pts_elem.text else None,
                        dtype=float)
    n_comp = int(pts_elem.get("NumberOfComponents", "3"))
    pts = pts.reshape(-1, n_comp)
    x = pts[:, 0]

    # Named point-data field
    for da in root.findall("./UnstructuredGrid/Piece/PointData/DataArray"):
        if da.get("Name") == field_name:
            vals = np.fromstring(da.text, sep="\n" if "\n" in da.text else None,
                                 dtype=float)
            return x, vals

    raise KeyError(f"Field '{field_name}' not found in {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vtu-dir", default="VTU",
                        help="Directory containing mpm_*_pe0000.vtu files")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip saving the comparison plot")
    args = parser.parse_args()

    pattern = os.path.join(args.vtu_dir, "mpm_*_pe0000.vtu")
    files = sorted(glob.glob(pattern))
    if not files:
        sys.exit(f"No VTU files found matching: {pattern}")

    print(f"Found {len(files)} VTU files in '{args.vtu_dir}'")
    print(f"epsilon = {epsilon:.4e} s^-1 = {epsilon * s_per_yr:.4e} yr^-1")
    print(f"v0/(4*epsilon) = {v0 / (4*epsilon) / 1e3:.2f} km")
    print()
    print(f"{'Time [yr]':>10s}  {'x_front_abs [km]':>17s}  "
          f"{'x_front_rel [km]':>17s}  {'xc_ana [km]':>12s}  {'Error [km]':>11s}")
    print("-" * 76)

    times_yr   = []
    xf_rel_arr = []
    xc_ana_arr = []

    for path in files:
        # Extract file index from name, e.g. mpm_000042_pe0000.vtu -> 42
        m = re.search(r"mpm_(\d+)_pe0000\.vtu", os.path.basename(path))
        if not m:
            continue
        file_idx = int(m.group(1))
        t_yr = float(file_idx)            # file N = end of year N (step_num = nint(t/vtu_dt))
        t_s  = t_yr * s_per_yr

        x, Lx_m = read_vtu_points_and_field(path, "Lx_m")
        x_front_abs = float(np.max(x + 0.5 * Lx_m))
        x_front_rel = x_front_abs - x_inflow
        xc_ana      = xc_analytic(t_s)
        err_km      = (x_front_rel - xc_ana) / 1e3

        times_yr.append(t_yr)
        xf_rel_arr.append(x_front_rel)
        xc_ana_arr.append(xc_ana)

        print(f"{t_yr:10.1f}  {x_front_abs/1e3:17.2f}  "
              f"{x_front_rel/1e3:17.2f}  {xc_ana/1e3:12.2f}  {err_km:11.2f}")

    times_yr   = np.array(times_yr)
    xf_rel_arr = np.array(xf_rel_arr)
    xc_ana_arr = np.array(xc_ana_arr)
    errors_km  = (xf_rel_arr - xc_ana_arr) / 1e3

    # Summary (exclude t=0)
    mask = times_yr > 0
    if mask.any():
        e = errors_km[mask]
        print()
        print("Front tracking summary (t > 0):")
        print(f"  Mean error  = {np.mean(e):+.3f} km")
        print(f"  Max |error| = {np.max(np.abs(e)):.3f} km")
        print(f"  RMS error   = {np.sqrt(np.mean(e**2)):.3f} km")
        print(f"  Analytic xc at t={times_yr[-1]:.0f} yr: {xc_ana_arr[-1]/1e3:.2f} km (rel), "
              f"{(xc_ana_arr[-1]+x_inflow)/1e3:.2f} km (abs)")

    # Plot
    if not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(times_yr, xf_rel_arr / 1e3, "b.", ms=3, label="Model (VTU)")
        ax.plot(times_yr, xc_ana_arr / 1e3, "r--", lw=1.5, label="Analytic Eq. 47")
        ax.set_xlabel("Time [yr]")
        ax.set_ylabel("Ice-front position relative to inflow [km]")
        ax.set_title("Ice-front advance: model vs. Huth et al. 2021 Eq. 47")
        ax.legend()
        ax.grid(True, lw=0.4)
        fig.tight_layout()
        outfile = "front_comparison.png"
        fig.savefig(outfile, dpi=150)
        print(f"\nPlot saved to {outfile}")


if __name__ == "__main__":
    main()
