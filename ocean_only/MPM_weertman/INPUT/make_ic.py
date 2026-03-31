"""
make_ic.py  --  Generate initial conditions for the MPM Weertman steady-state test.

Domain: 450 km x 75 km Cartesian channel, 5 km x 5 km cells.
  NIGLOBAL = 90  (x-direction)
  NJGLOBAL = 15  (y-direction)

Layout (Huth et al. 2021, Section 5.1):
  Extension domain:  x = [0, 200] km  (cells 0-7)  hmask=1, H=H0, u=v0
  First active cell:  x = [200, 225] km (cell 8)     hmask=1, H/u = analytical
  Free SSA domain:   x = [225, 450] km (cells 9-17) hmask=1, H/u = analytical

Physics (Huth et al. 2021):
  H0 = 600 m, v0 = 300 m/yr
  B0 = 1.9e8 Pa s^(1/3)  =>  A_glen = B0^(-3) = 1.458e-25 Pa^-3 s^-1
  rho_i = 910, rho_w = 1028, g = 9.81, n = 3

Analytical steady-state:
  Q0 = H0 * v0
  alpha = A * (rho_i * g * (1 - rho_i/rho_w) / 4)^3
  H(x_rel) = (4*alpha*x_rel/Q0 + 1/H0^4)^(-0.25)
  u(x_rel) = Q0 / H(x_rel)
  where x_rel = x - 200 km

Mask convention (MPM node-based BCs):
  h_mask = 1  All ice cells (extension + free SSA domain)
  h_mask = 0  No ice

  ufacemask = 5   Dirichlet for all extension domain u-faces (x=0 to x=225 km)
  ufacemask = 2   Calving front at eastern boundary (x=450 km)
  ufacemask = -2  Interior ice face (active domain)
  vfacemask = 5   Free-slip N/S walls (v=0, u free)
  vfacemask = -2  Interior

  h_node_mask = 1  Dirichlet thickness nodes (corners where xc <= x_inflow + dx)
  u_node_mask = 1  Dirichlet u-velocity nodes (same region)
  v_node_mask = 1  Dirichlet v-velocity nodes (same region + N/S walls)
  h_node_bdry_val  Prescribed H at Dirichlet thickness nodes [m]

Output: MPM_IC.nc
"""

from netCDF4 import Dataset
import numpy as np

# ---- domain --------------------------------------------------------
Lx = 450.0e3      # m
Ly =  40.0e3      # m
dx =   5.0e3      # m  cell width
dy =   5.0e3      # m  cell height

nx  = int(Lx / dx)     # 18
ny  = int(Ly / dy)     # 3
nxp = nx + 1            # 19
nyp = ny + 1            # 4

# cell-centre positions
xh = np.linspace(dx / 2, Lx - dx / 2, nx)   # [12.5, 37.5, ..., 437.5] km
yh = np.linspace(dy / 2, Ly - dy / 2, ny)

# corner positions
xc = np.linspace(0.0, Lx, nxp)
yc = np.linspace(0.0, Ly, nyp)

XH, YH = np.meshgrid(xh, yh)   # shape (ny, nx)
XC, YC = np.meshgrid(xc, yc)   # shape (nyp, nxp)

# ---- physical parameters (Huth et al. 2021) -------------------------
rhoi      = 910.0           # kg m^-3
rhow      = 1028.0          # kg m^-3
g         = 9.81            # m s^-2
H0        = 600.0           # m
B0        = 1.9e8           # Pa s^(1/3)
A_glen    = B0**(-3)        # Pa^-3 s^-1 = 1.458e-25
n_glen    = 3
s_per_yr  = 31556926.0      # s yr^-1 (Julian year)
v0_yr     = 300.0           # m yr^-1
v0        = v0_yr / s_per_yr  # m s^-1

x_inflow  = 200.0e3   # m -- inflow boundary (end of extension domain)
Q0        = H0 * v0   # m^2 s^-1

# Analytical steady-state coefficients
drive = rhoi * g * (1.0 - rhoi / rhow) / 4.0   # Pa m^-1
alpha = A_glen * drive**n_glen                   # m^-3 s^-1
m1 = 4.0 * alpha / Q0   # m^-4
m2 = 1.0 / H0**4        # m^-4

def H_analytic(x_rel):
    """Analytical thickness at distance x_rel from inflow [m]."""
    return (m1 * x_rel + m2)**(-0.25)

def u_analytic(x_rel):
    """Analytical velocity at distance x_rel from inflow [m/s]."""
    return Q0 / H_analytic(x_rel)

# ---- h-grid (cell-centre) variables --------------------------------

h_shelf = np.zeros((ny, nx))
h_mask  = np.zeros((ny, nx))

for i in range(nx):
    if xh[i] <=x_inflow+dx:
        h_mask[:, i] = 3.0
    else:
        # All ice cells use hmask=1; Dirichlet BCs are specified at B-grid nodes
        h_mask[:, i] = 1.0
    x_rel = xh[i] - x_inflow
    if x_rel <= 0.0:
        h_shelf[:, i] = H0
    else:
        h_shelf[:, i] = H_analytic(x_rel)

# depth: flat 1500 m ocean floor
depth = np.ones((ny, nx)) * 1500.0

# shelf area (full cell)
shelf_area = np.ones((ny, nx)) * dx * dy

# surface mass balance: zero
smb = np.zeros((ny, nx))

# grounding fraction: 0 = fully floating
float_frac = np.zeros((ny, nx))

# ---- B-grid (corner) variables -------------------------------------

ufacemask = np.full((nyp, nxp), -2.0)   # interior default
# Dirichlet for all u-faces within the extension domain (x=0 to x=225 km)
# This ensures the SSA solver prescribes velocity in hmask=3 cells
n_ext_faces = int((x_inflow + dx) / dx)  # 9: faces at x=0,25,...,200,225 km
for i in range(n_ext_faces + 1):         # indices 0..9
    ufacemask[:, i] = 5.0
ufacemask[:, nxp - 1] = 2.0             # eastern calving front: stress-free

vfacemask = np.full((nyp, nxp), -2.0)   # interior default
vfacemask[0, :]       = 5.0             # southern wall: free-slip
vfacemask[nyp - 1, :] = 5.0             # northern wall: free-slip

# Boundary velocity: analytical profile at all Dirichlet u-faces
ubdry_val = np.zeros((nyp, nxp))
for i in range(nxp):
    x_rel = xc[i] - x_inflow
    if xc[i] <= x_inflow:
        ubdry_val[:, i] = v0
    elif xc[i] <= x_inflow + dx:
        # First active cell boundary (x=225km): use analytical velocity
        ubdry_val[:, i] = u_analytic(x_rel)

vbdry_val = np.zeros((nyp, nxp))

# Initial ice velocity: analytical profile everywhere
u_shelf = np.zeros((nyp, nxp))
v_shelf = np.zeros((nyp, nxp))
for i in range(nxp):
    x_rel = xc[i] - x_inflow
    if x_rel <= 0.0:
        u_shelf[:, i] = v0
    else:
        u_shelf[:, i] = u_analytic(x_rel)

# ---- MPM node masks (B-grid corners) --------------------------------
# h_node_mask: Dirichlet thickness nodes in extension domain (xc <= x_inflow + dx)
h_node_mask = np.zeros((nyp, nxp))
for i in range(nxp):
    if xc[i] <= x_inflow + dx:
        h_node_mask[:, i] = 1.0

# u_node_mask: Dirichlet u-velocity nodes (same region)
u_node_mask = h_node_mask.copy()

# v_node_mask: extension region + N/S walls (v=0 everywhere on walls)
v_node_mask = h_node_mask.copy()
v_node_mask[0, :]       = 1.0   # southern wall: v=0
v_node_mask[nyp - 1, :] = 1.0   # northern wall: v=0

# h_node_bdry_val: prescribed H at Dirichlet thickness nodes [m]
# Nodes at x <= x_inflow: constant H0; nodes at x_inflow < x <= x_inflow+dx: analytical
h_node_bdry_val = np.zeros((nyp, nxp))
for i in range(nxp):
    if xc[i] <= x_inflow:
        h_node_bdry_val[:, i] = H0
    elif xc[i] <= x_inflow + dx:
        h_node_bdry_val[:, i] = H_analytic(xc[i] - x_inflow)

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

cvar('h_node_mask',    'f4', ('nyp', 'nxp'))[:] = h_node_mask
cvar('u_node_mask',    'f4', ('nyp', 'nxp'))[:] = u_node_mask
cvar('v_node_mask',    'f4', ('nyp', 'nxp'))[:] = v_node_mask
cvar('h_node_bdry_val','f4', ('nyp', 'nxp'))[:] = h_node_bdry_val

ds.close()
print("Wrote MPM_IC.nc")

# ---- print analytic profile for reference ---------------------------
print(f"\nHuth et al. 2021 parameters:")
print(f"  H0       = {H0:.0f} m")
print(f"  v0       = {v0_yr:.0f} m/yr")
print(f"  B0       = {B0:.1e} Pa s^(1/3)")
print(f"  A_glen   = {A_glen:.4e} Pa^-3 s^-1")
print(f"  Q0       = {Q0 * s_per_yr:.0f} m^2/yr")
print(f"  alpha    = {alpha:.4e} m^-3 s^-1")
print(f"\nAnalytical profile (active domain, x_rel from inflow):")
for x_km in [0, 25, 50, 100, 150, 200, 250]:
    x_m = x_km * 1e3
    H = H_analytic(x_m)
    u = u_analytic(x_m) * s_per_yr
    print(f"  x_rel = {x_km:>4d} km:  H = {H:.1f} m,  u = {u:.1f} m/yr")
