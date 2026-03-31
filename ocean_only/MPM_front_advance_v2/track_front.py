"""
track_front.py  --  Track the calving front position and compare to the analytic
                    solution (Huth et al. 2021, Eq. 47).

Huth et al. 2021, Section 5.1 flow-band experiment.
  Extension domain: x = [0, 200] km
  Active domain:    x >= 200 km
  Front starts at inflow boundary (x = 200 km, i.e. x_f0 = 0 in relative coords).

Analytic front advance (Eq. 47):
  eps = A * (rho_i * g * H0 * (1 - rho_i/rho_w) / 4)^n
  x_f(t) = (x_f0 + v0/eps) * exp(eps*t) - v0/eps
  where H0 is the inflow boundary thickness (600 m), not a constant-H assumption.

Front detection: rightmost cell with area_shelf_h > threshold (from grid output),
  corresponding to rightmost particle + half particle length conceptually.

Usage:
  python track_front.py [ice_shelf.nc]
"""

import sys
import glob
import numpy as np
from netCDF4 import Dataset, MFDataset

# --- Physical parameters (Huth et al. 2021) ---
rhoi     = 910.0
rhow     = 1028.0
g        = 9.81
H0       = 600.0
B0       = 1.9e8
A_glen   = B0**(-3)
n_glen   = 3
s_per_yr = 31536000 #31556926.0
v0_yr    = 300.0
v0       = v0_yr / s_per_yr

# Strain rate at inflow boundary
drive    = rhoi * g * H0 * (1.0 - rhoi / rhow) / 4.0
eps_xx   = A_glen * drive**n_glen
eps_yr   = eps_xx * s_per_yr
char_len = v0 / eps_xx   # m

# --- Domain ---
Lx = 450.0e3
dx = 5.0e3
nx = 90
xh = np.linspace(dx/2, Lx - dx/2, nx)

x_inflow = 200.0e3   # m -- inflow boundary in MOM6 coords
x_f0_rel = 0.0       # front starts at inflow boundary (relative)

# Analytic front position (Eq. 47), relative to inflow boundary
def x_front_analytic_rel(t_s):
    """Front position relative to inflow [m] at time t [s]."""
    return (x_f0_rel + char_len) * np.exp(eps_xx * t_s) - char_len

# --- Read output ---
if len(sys.argv) > 1:
    pattern = sys.argv[1]
else:
    pattern = "ice_shelf__*.nc"

files = sorted(glob.glob(pattern))
if not files:
    files = ["ice_shelf.nc"]

ds = MFDataset(files, 'r', aggdim='Time') if len(files) > 1 else Dataset(files[0], 'r')

times = ds.variables['Time'][:]

if 'npart_per_cell' in ds.variables:
    front_field = ds.variables['npart_per_cell'][:, :, :]
    front_threshold = 0.0
    front_label = "npart_per_cell"
elif 'h_mask' in ds.variables:
    front_field = ds.variables['h_mask'][:, :, :]
    front_threshold = 0.5
    front_label = "h_mask"
else:
    front_field = ds.variables['h_shelf'][:, :, :]
    front_threshold = 1.0
    front_label = "h_shelf"

ds.close()

nt = len(times)
print(f"Using '{front_label}' for front detection (threshold = {front_threshold})")
print(f"Inflow boundary at x = {x_inflow/1e3:.0f} km")

# --- Track front position ---
print(f"\n{'Time [yr]':>10s} {'x_front':>10s} {'x_front_rel':>12s} {'x_ana_rel':>12s} "
      f"{'Error [km]':>11s}")
print("-" * 60)

errors_km = []
for it in range(nt):
    t_days = times[it]
    t_yr   = t_days / 365.0
    t_s    = t_days * 86400.0

    f_2d = front_field[it, :, :]
    f_max_per_col = np.max(f_2d, axis=0)
    ice_cols = np.where(f_max_per_col > front_threshold)[0]

    if len(ice_cols) == 0:
        x_front_model = x_inflow   # no ice detected — front at inflow
    else:
        i_front = ice_cols[-1]
        x_front_model = xh[i_front] + dx / 2.0   # right edge of last ice cell

    x_front_rel = x_front_model - x_inflow   # relative to inflow [m]
    x_ana_rel   = x_front_analytic_rel(t_s)

    err_km = (x_front_rel - x_ana_rel) / 1e3

    if t_yr > 0:
        errors_km.append(err_km)

    print(f"{t_yr:10.1f} {x_front_model/1e3:10.1f} {x_front_rel/1e3:12.1f} "
          f"{x_ana_rel/1e3:12.1f} {err_km:11.2f}")

# --- Summary ---
if len(errors_km) > 0:
    errors_km = np.array(errors_km)
    print(f"\nFront tracking summary (excluding t=0):")
    print(f"  Mean error    = {np.mean(errors_km):+.2f} km")
    print(f"  Max |error|   = {np.max(np.abs(errors_km)):.2f} km")
    print(f"  RMS error     = {np.sqrt(np.mean(errors_km**2)):.2f} km")

    t_final = times[-1] / 365.0
    x_final_ana_rel = x_front_analytic_rel(times[-1] * 86400.0)
    print(f"\n  Final time             = {t_final:.0f} yr")
    print(f"  Analytic front (rel)   = {x_final_ana_rel/1e3:.1f} km")
    print(f"  Analytic front (abs)   = {(x_final_ana_rel + x_inflow)/1e3:.1f} km")

    # Check that front actually advanced
    final_x_rel = (errors_km[-1] * 1e3 + x_final_ana_rel) if len(errors_km) > 0 else 0
    advance_pass = final_x_rel > dx   # front moved at least one cell
    print(f"\n{'PASS' if advance_pass else 'FAIL'}: front advanced "
          f"({final_x_rel/1e3:.1f} km, threshold > {dx/1e3:.0f} km)")

# --- Analytic parameters ---
print(f"\nAnalytic parameters:")
print(f"  H0       = {H0:.0f} m")
print(f"  v0       = {v0_yr:.0f} m/yr")
print(f"  A_glen   = {A_glen:.4e} Pa^-3 s^-1")
print(f"  eps      = {eps_xx:.4e} s^-1 = {eps_yr:.4e} yr^-1")
print(f"  v0/eps   = {char_len/1e3:.1f} km")
print(f"  x_f0     = {x_f0_rel/1e3:.0f} km (relative)")
for t_yr_ref in [50, 100, 200, 300]:
    xf = x_front_analytic_rel(t_yr_ref * s_per_yr)
    print(f"  x_f({t_yr_ref}yr) = {xf/1e3:.1f} km (abs: {(xf+x_inflow)/1e3:.1f} km)")
