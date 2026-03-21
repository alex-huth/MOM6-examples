"""
make_ic.py  --  Generate initial conditions for the MPM Weertman steady-state test.

Domain: 500 km x 75 km Cartesian channel, 25 km x 25 km cells.
  NIGLOBAL = 20  (x-direction)
  NJGLOBAL = 3   (y-direction)

Physics:
  H0 = 500 m uniform floating shelf
  u0 = 200 m/yr inflow at western boundary
  A  = 1e-25 Pa^-3 s^-1 (Glen flow law, warm temperate ice)
  No basal friction

Mask convention:
  h_mask = 3  Dirichlet inflow BC  (x in [0, 100 km], first 4 cells)
  h_mask = 1  Free SSA interior    (x in [100, 500 km])

  ufacemask = 5   ice-covered u-face
  vfacemask = 5   ice-covered v-face (including N/S walls)
  ufacemask = -2  open-ocean face (not used here -- full ice domain)
  vfacemask = -2  open-ocean face

Analytic Weertman velocity (for verification):
  eps_xx = A * (rho_i * g * H * (1 - rho_i/rho_w) / 4)^3
         = 1e-25 * (910*9.8*500*(1-910/1028)/4)^3
         approx 2.095e-10 s^-1  =  6.607e-3 yr^-1
  u(x)   = u0 + eps_xx * x
  u(500 km) approx 3503.5 m/yr

Output: MPM_IC.nc
"""

from netCDF4 import Dataset
import numpy as np

# ---- domain --------------------------------------------------------
Lx = 500.0e3      # m
Ly =  75.0e3      # m
dx =  25.0e3      # m  cell width
dy =  25.0e3      # m  cell height

nx  = int(Lx / dx)     # 20  (h-grid / cell-center count)
ny  = int(Ly / dy)     # 3
nxp = nx + 1           # 21  (B-grid / corner count)
nyp = ny + 1           # 4

# cell-centre positions
xh = np.linspace(dx / 2, Lx - dx / 2, nx)   # [12.5, 37.5, ..., 487.5] km
yh = np.linspace(dy / 2, Ly - dy / 2, ny)   # [12.5, 37.5, 62.5] km

# corner positions
xc = np.linspace(0.0, Lx, nxp)              # [0, 25, ..., 500] km
yc = np.linspace(0.0, Ly, nyp)              # [0, 25, 50, 75] km

XH, YH = np.meshgrid(xh, yh)   # shape (ny, nx)
XC, YC = np.meshgrid(xc, yc)   # shape (nyp, nxp)

# ---- physical parameters ------------------------------------------
rhoi      = 910.0           # kg m^-3
rhow      = 1028.0          # kg m^-3
H0        = 500.0           # m
s_per_yr  = 365.0 * 86400   # s yr^-1
u0        = 200.0 / s_per_yr  # m s^-1  (200 m yr^-1)

x_inflow  = 100.0e3   # m  -- Dirichlet BC region: x in [0, 100 km]

# ---- h-grid (cell-centre) variables --------------------------------

# ice thickness: uniform 500 m
h_shelf = np.ones((ny, nx)) * H0

# depth: flat 1500 m ocean floor
depth = np.ones((ny, nx)) * 1500.0

# h_mask:  3 = Dirichlet BC,  1 = free SSA
h_mask = np.ones((ny, nx))
for i in range(nx):
    if xh[i] <= x_inflow:
        h_mask[:, i] = 3.0

# shelf area (full cell for uniform shelf)
shelf_area = np.ones((ny, nx)) * dx * dy

# surface mass balance: zero (purely dynamic test)
smb = np.zeros((ny, nx))

# grounding fraction: 0 = floating, 1 = grounded (MOM6 ground_frac convention)
# Fully floating shelf: set to 0 everywhere
float_frac = np.zeros((ny, nx))

# ---- B-grid (corner) variables -------------------------------------

# u_face_mask_bdry convention (read by MOM6 as ICE_UBDRYMSK_VARNAME):
#   5  = Dirichlet inflow BC (western boundary)
#   2  = stress-free calving front (eastern boundary)
#   3  = no-slip wall (N/S boundaries via vfacemask)
#  -2  = interior ice-covered face (falls into default case in
#         update_velocity_masks, keeping umask=1 so SSA solves there)
ufacemask = np.full((nyp, nxp), -2.0)   # interior: default (umask=1)
ufacemask[:, 0]       = 5.0             # western inflow: Dirichlet
ufacemask[:, nxp - 1] = 2.0             # eastern calving front: stress-free

# v_face_mask_bdry: free-slip at N/S walls (v=0, u free), default elsewhere
# vfacemask=5 → case(5): vmask=3 (v Dirichlet = vbdry_val=0), umask unchanged (stays 1)
# vfacemask=3 → case(3): vmask=3 AND umask=3 (no-slip, kills lateral u — wrong for Weertman)
vfacemask = np.full((nyp, nxp), -2.0)   # interior: default
vfacemask[0, :]       = 5.0             # southern wall: free-slip (v=0, u free)
vfacemask[nyp - 1, :] = 5.0             # northern wall: free-slip (v=0, u free)

# boundary velocity: u0 at the western face (xc = 0), zero elsewhere
ubdry_val = np.zeros((nyp, nxp))
ubdry_val[:, 0] = u0            # western inflow

vbdry_val = np.zeros((nyp, nxp))

# initial ice velocity: u0 in the Dirichlet inflow region, zero in
# the free domain (SSA will compute the steady-state profile)
u_shelf = np.zeros((nyp, nxp))
v_shelf = np.zeros((nyp, nxp))
for i in range(nxp):
    if xc[i] <= x_inflow:
        u_shelf[:, i] = u0

# ---- write NetCDF --------------------------------------------------
ds = Dataset('./MPM_IC.nc', mode='w', format='NETCDF4_CLASSIC')

ds.createDimension('nx',  nx)
ds.createDimension('ny',  ny)
ds.createDimension('nxp', nxp)
ds.createDimension('nyp', nyp)

def cvar(name, dtype, dims):
    return ds.createVariable(name, dtype, dims)

cvar('depth',      'f4', ('ny',  'nx' ))[:] = depth
cvar('h_mask',     'f4', ('ny',  'nx' ))[:] = h_mask
cvar('h_shelf',    'f4', ('ny',  'nx' ))[:] = h_shelf
cvar('shelf_area', 'f4', ('ny',  'nx' ))[:] = shelf_area
cvar('smb',        'f4', ('ny',  'nx' ))[:] = smb
cvar('float_frac', 'f4', ('ny',  'nx' ))[:] = float_frac

cvar('ufacemask',  'f4', ('nyp', 'nxp'))[:] = ufacemask
cvar('vfacemask',  'f4', ('nyp', 'nxp'))[:] = vfacemask
cvar('ubdry_val',  'f4', ('nyp', 'nxp'))[:] = ubdry_val
cvar('vbdry_val',  'f4', ('nyp', 'nxp'))[:] = vbdry_val
cvar('u_shelf',    'f4', ('nyp', 'nxp'))[:] = u_shelf
cvar('v_shelf',    'f4', ('nyp', 'nxp'))[:] = v_shelf

ds.close()
print("Wrote MPM_IC.nc")

# ---- print analytic Weertman profile for reference ----------------
g        = 9.8
A        = 1.0e-25
drive    = rhoi * g * H0 * (1.0 - rhoi / rhow) / 4.0
eps_xx   = A * drive**3
eps_yr   = eps_xx * s_per_yr
print(f"Driving stress   = {drive:.1f} Pa")
print(f"eps_xx           = {eps_xx:.3e} s^-1  = {eps_yr:.3e} yr^-1")
print(f"u(  0 km) = {u0*s_per_yr:.1f} m/yr")
print(f"u(500 km) = {(u0 + eps_xx*Lx)*s_per_yr:.1f} m/yr  (analytic Weertman)")
