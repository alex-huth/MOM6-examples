"""
compare_analytic.py  --  Compare MPM Weertman test output to the analytic solution.

Huth et al. 2021, Section 5.1 flow-band experiment.
  Extension domain: x = [0, 200] km (hmask=3, enforced H=H0, u=v0)
  Active domain:    x >= 200 km (comparison region)

Analytical steady-state (active domain, x_rel = x - 200 km):
  Q0 = H0 * v0
  alpha = A * (rho_i * g * (1 - rho_i/rho_w) / 4)^3
  H(x_rel) = (4*alpha*x_rel/Q0 + 1/H0^4)^(-0.25)
  u(x_rel) = Q0 / H(x_rel)

Usage:
  python compare_analytic.py [ice_shelf.nc]
"""

import sys
import glob
import numpy as np
from netCDF4 import Dataset, MFDataset

# --- Physical parameters (Huth et al. 2021) ---
rhoi     = 910.0        # kg m^-3
rhow     = 1028.0       # kg m^-3
g        = 9.81         # m s^-2
H0       = 600.0        # m
B0       = 1.9e8        # Pa s^(1/3)
A_glen   = B0**(-3)     # Pa^-3 s^-1
n_glen   = 3
s_per_yr = 31556926.0   # Julian year
v0_yr    = 300.0        # m yr^-1
v0       = v0_yr / s_per_yr

Q0     = H0 * v0   # m^2 s^-1
drive  = rhoi * g * (1.0 - rhoi / rhow) / 4.0
alpha  = A_glen * drive**n_glen
m1     = 4.0 * alpha / Q0
m2     = 1.0 / H0**4

def H_analytic(x_rel):
    return (m1 * x_rel + m2)**(-0.25)

def u_analytic_ms(x_rel):
    return Q0 / H_analytic(x_rel)

# --- Domain ---
Lx = 450.0e3  # m
dx = 5.0e3    # m
nx = 90
nxp = nx + 1
ny = 15
x_inflow = 200.0e3  # m

xh = np.linspace(dx/2, Lx - dx/2, nx)   # cell centres [m]
xc = np.linspace(0.0, Lx, nxp)          # B-grid corners [m]

# Active domain masks
active_h = xh > x_inflow          # cells in the free SSA domain (hmask=1)
active_c = xc > x_inflow          # B-grid corners in active domain

# Analytical profiles on active domain
xh_rel = xh[active_h] - x_inflow
xc_rel = xc[active_c] - x_inflow

H_ana_h = np.array([H_analytic(x) for x in xh_rel])
u_ana_c = np.array([u_analytic_ms(x) * s_per_yr for x in xc_rel])  # m/yr

# --- Read output ---
# Accept either a single file or a glob pattern; default: per-year files
if len(sys.argv) > 1:
    pattern = sys.argv[1]
else:
    pattern = "ice_shelf__*.nc"

files = sorted(glob.glob(pattern))
if not files:
    files = ["ice_shelf.nc"]   # fallback to legacy single file

ds = MFDataset(files, 'r', aggdim='Time') if len(files) > 1 else Dataset(files[0], 'r')

times    = ds.variables['Time'][:]
u_shelf  = ds.variables['u_shelf'][:, :, :]    # (nt, nyp, nxp)
h_shelf  = ds.variables['h_shelf'][:, :, :]    # (nt, ny, nx)
u_units  = getattr(ds.variables['u_shelf'], 'units', 'm s-1')
ds.close()

nt = len(times)
u_conv = 1.0 if 'yr' in u_units else s_per_yr

# --- Print parameters ---
print(f"Huth et al. 2021 parameters:")
print(f"  H0       = {H0:.0f} m")
print(f"  v0       = {v0_yr:.0f} m/yr")
print(f"  A_glen   = {A_glen:.4e} Pa^-3 s^-1")
print(f"  Q0       = {Q0*s_per_yr:.0f} m^2/yr")
print(f"  alpha    = {alpha:.4e} m^-3 s^-1")
print(f"  Comparison on x >= {x_inflow/1e3:.0f} km (active domain)")
print(f"  Output units: {u_units}")

# --- Compare at each output time ---
print(f"\n{'Time [yr]':>10s} {'u_rel_L2':>12s} {'H_rel_L2':>12s} {'H_mean [m]':>11s} {'Status':>8s}")
print("-" * 60)

best_it = 0
best_u_rel = 1e30

for it in range(nt):
    t_yr = times[it] / 365.0

    u_model_yr = np.mean(u_shelf[it, :, :], axis=0) * u_conv  # average over j
    h_model_1d = np.mean(h_shelf[it, :, :], axis=0)

    # Velocity error on active B-grid points
    u_active = u_model_yr[active_c]
    u_err = u_active - u_ana_c
    u_rel = np.sqrt(np.mean(u_err**2)) / np.sqrt(np.mean(u_ana_c**2))

    # Thickness error on active cells
    h_active = h_model_1d[active_h]
    h_err = h_active - H_ana_h
    h_rel = np.sqrt(np.mean(h_err**2)) / np.sqrt(np.mean(H_ana_h**2))

    h_mean = np.mean(h_active)
    status = "PASS" if u_rel < 0.05 else ("~OK" if u_rel < 0.10 else "FAIL")

    if u_rel < best_u_rel:
        best_u_rel = u_rel
        best_it = it

    print(f"{t_yr:10.1f} {u_rel:12.4e} {h_rel:12.4e} {h_mean:11.1f} {status:>8s}")

# --- Detailed comparison at best time ---
it = best_it
t_yr = times[it] / 365.0
u_model_yr = np.mean(u_shelf[it, :, :], axis=0) * u_conv
h_model_1d = np.mean(h_shelf[it, :, :], axis=0)

u_active = u_model_yr[active_c]
u_err = u_active - u_ana_c
u_rms = np.sqrt(np.mean(u_err**2))
u_rel = u_rms / np.sqrt(np.mean(u_ana_c**2))

h_active = h_model_1d[active_h]
h_err = h_active - H_ana_h
h_rms = np.sqrt(np.mean(h_err**2))
h_rel = h_rms / np.sqrt(np.mean(H_ana_h**2))

print(f"\n--- Best match at t = {t_yr:.1f} yr ---")
print(f"  Velocity relative L2 = {u_rel:.4e}")
print(f"  Velocity RMS error   = {u_rms:.2f} m/yr")
print(f"  Thickness relative L2= {h_rel:.4e}")
print(f"  Thickness RMS error  = {h_rms:.2f} m")

# Linearity check on active B-grid points
x_free = xc[active_c]
u_free = u_model_yr[active_c]
if len(x_free) > 2:
    coeffs = np.polyfit(x_free, u_free, 1)
    u_fit = np.polyval(coeffs, x_free)
    residuals = u_free - u_fit
    linearity_r2 = 1.0 - np.sum(residuals**2) / np.sum((u_free - np.mean(u_free))**2)
    eps_model_yr = coeffs[0]  # du/dx in yr^-1 (since u is m/yr and x is m)

    h_mean_free = np.mean(h_active)
    drive_eff = rhoi * g * h_mean_free * (1.0 - rhoi/rhow) / 4.0
    eps_expected_yr = A_glen * drive_eff**n_glen * s_per_yr

    print(f"\n  Linearity R^2     = {linearity_r2:.8f}")
    print(f"  Model strain rate = {eps_model_yr:.4e} yr^-1")
    print(f"  Expected (H={h_mean_free:.0f}m) = {eps_expected_yr:.4e} yr^-1")

    linear_pass = linearity_r2 > 0.999
    eps_pass = abs(eps_model_yr - eps_expected_yr) / eps_expected_yr < 0.10
else:
    linear_pass = False
    eps_pass = False
    linearity_r2 = 0.0

vel_pass = u_rel < 0.10
h_pass   = h_rel < 0.10

print(f"\n{'PASS' if linear_pass else 'FAIL'}: velocity linearity R^2 = {linearity_r2:.8f} (threshold > 0.999)")
print(f"{'PASS' if eps_pass else 'FAIL'}: strain rate matches current H (threshold < 10%)")
print(f"{'PASS' if vel_pass else 'FAIL'}: velocity relative L2 = {u_rel:.4e} (threshold < 10%)")
print(f"{'PASS' if h_pass else 'FAIL'}: thickness relative L2 = {h_rel:.4e} (threshold < 10%)")

# --- 1-D profiles at best time ---
print(f"\n{'x [km]':>10s} {'x_rel':>8s} {'u_model':>12s} {'u_ana':>12s} {'H_model':>10s} {'H_ana':>10s}")
for i in range(nxp):
    x_km = xc[i] / 1e3
    x_rel = xc[i] - x_inflow
    u_mod = u_model_yr[i]
    u_ana = u_analytic_ms(max(x_rel, 0.0)) * s_per_yr if x_rel >= 0 else v0_yr
    h_str = ""
    h_ana_str = ""
    if i < nx:
        h_str = f"{h_model_1d[i]:10.1f}"
        xh_rel = xh[i] - x_inflow
        h_ana_str = f"{H_analytic(max(xh_rel, 0.0)):10.1f}" if xh_rel >= 0 else f"{H0:10.1f}"
    print(f"{x_km:10.1f} {x_rel/1e3:8.1f} {u_mod:12.2f} {u_ana:12.2f} {h_str} {h_ana_str}")
