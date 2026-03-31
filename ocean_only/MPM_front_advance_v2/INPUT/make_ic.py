"""
make_ic.py  --  Generate initial conditions for the MPM front advance test.

Domain: 450 km x 75 km Cartesian channel, 5 km x 5 km cells.
  NIGLOBAL = 90  (x-direction)
  NJGLOBAL = 15  (y-direction)

Layout (Huth et al. 2021, Section 5.1):
  Extension domain:  x = [0, 200] km  (cells 0-7)  hmask=1, H=H0, u=v0
  First active cell:  x = [200, 225] km (cell 8)     hmask=1, H=H0, u=v0
  Active domain:     x = [225, 450] km (cells 9-17) hmask=0 (NO ICE INITIALLY)

Particles are initialized ONLY in extension + first active cells.
Dirichlet BCs for those cells are specified at B-grid nodes (h_node_mask,
u_node_mask, v_node_mask, h_node_bdry_val) rather than via hmask=3.
The active domain starts empty; particles flow in from the extension over time.

Physics (Huth et al. 2021):
  H0 = 600 m, v0 = 300 m/yr
  B0 = 1.9e8 Pa s^(1/3)  =>  A_glen = B0^(-3) = 1.458e-25 Pa^-3 s^-1
  rho_i = 910, rho_w = 1028, g = 9.81, n = 3

Front advance (Eq. 47):
  eps = A * (rho_i*g*H0*(1-rho_i/rho_w)/4)^n
  x_f(t) = (x_f0 + v0/eps) * exp(eps*t) - v0/eps
  where x_f0 = 0 (front starts at inflow boundary, x=200km in MOM6 coords)

Output: MPM_IC.nc
"""

from netCDF4 import Dataset
import numpy as np

# ---- domain --------------------------------------------------------
Lx = 450.0e3      # m
Ly =  10.0e3      # m
dx =   5.e3      # m
dy =   5.e3      # m
dx_dir = 5.e3  #enforce dirichlet on extension domain + dx_dir (m)


nx  = int(Lx / dx)
ny  = int(Ly / dy)
nxp = nx + 1            # 19
nyp = ny + 1            # 4

xh = np.linspace(dx / 2, Lx - dx / 2, nx)
yh = np.linspace(dy / 2, Ly - dy / 2, ny)
xc = np.linspace(0.0, Lx, nxp)
yc = np.linspace(0.0, Ly, nyp)

# ---- physical parameters (Huth et al. 2021) -------------------------
rhoi      = 910.0
rhow      = 1028.0
g         = 9.81
H0        = 600.0
B0        = 1.9e8
A_glen    = B0**(-3)
n_glen    = 3
s_per_yr  = 31536000.0 #31556926.0
v0_yr     = 300.0
v0        = v0_yr / s_per_yr

x_inflow  = 200.0e3   # m -- inflow boundary
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

# for i in range(nx):
#     if xh[i] <= x_inflow + dx:
#         # Extension domain + first active cell: hmask=1, Dirichlet BCs at nodes
#         h_mask[:, i] = 3.0
#         h_shelf[:, i] = H0
#     else:
#         # Active domain: hmask=0 (no ice initially)
#         h_mask[:, i] = 0.0
#         h_shelf[:, i] = 0.0

for i in range(nx):
    # if xh[i] <=x_inflow+dx:
    if xh[i] <=x_inflow:
        h_mask[:, i] = 1.0
    else:
        # All ice cells use hmask=1; Dirichlet BCs are specified at B-grid nodes
        h_mask[:, i] = 0.0
    x_rel = xh[i] - x_inflow
    if x_rel <= 0.0:
        h_shelf[:, i] = H0
    else:
        h_shelf[:, i] = H_analytic(x_rel)

# depth: flat 1500 m
depth = np.ones((ny, nx)) * 1500.0

# shelf area: full cell where ice, 0 in open ocean
shelf_area = np.where(h_mask > 0, dx * dy, 0.0)

smb = np.zeros((ny, nx))
float_frac = np.zeros((ny, nx))

# ---- B-grid (corner) variables -------------------------------------

ufacemask = np.full((nyp, nxp), -2.0)
# Dirichlet for all u-faces within the extension domain (x=0 to x=225 km)
n_ext_faces = int((x_inflow + dx_dir) / dx)  # 9: faces at x=0,25,...,200,225 km
for i in range(n_ext_faces + 1):         # indices 0..9
    ufacemask[:, i] = 5.0
ufacemask[:, nxp - 1] = 2.0   # eastern calving front: stress-free

vfacemask = np.full((nyp, nxp), -2.0)
vfacemask[0, :]       = 5.0   # southern wall: free-slip
vfacemask[nyp - 1, :] = 5.0   # northern wall: free-slip

# ubdry_val = np.zeros((nyp, nxp))
# for i in range(nxp):
#     if xc[i] <= x_inflow + dx:
#         ubdry_val[:, i] = v0

ubdry_val = np.zeros((nyp, nxp))
for i in range(nxp):
    x_rel = xc[i] - x_inflow
    if xc[i] <= x_inflow:
        ubdry_val[:, i] = v0
    elif xc[i] <= x_inflow + dx_dir:
        # First active cell boundary (x=225km): use analytical velocity
        ubdry_val[:, i] = u_analytic(x_rel)

vbdry_val = np.zeros((nyp, nxp))

# Initial ice velocity: v0 in extension domain + first active cell face, 0 elsewhere
u_shelf = np.zeros((nyp, nxp))
v_shelf = np.zeros((nyp, nxp))
for i in range(nxp):
    if xc[i] <= x_inflow + dx_dir:
        u_shelf[:, i] = v0

# ---- MPM node masks (B-grid corners) --------------------------------
# h_node_mask: Dirichlet thickness nodes in extension domain (xc <= x_inflow + dx)
h_node_mask = np.zeros((nyp, nxp))
for i in range(nxp):
    if xc[i] <= x_inflow + dx_dir:
        h_node_mask[:, i] = 1.0

# u_node_mask: Dirichlet u-velocity nodes (same region)
u_node_mask = h_node_mask.copy()

# v_node_mask: extension region + N/S walls (v=0 everywhere on walls)
v_node_mask = h_node_mask.copy()
v_node_mask[0, :]       = 1.0   # southern wall: v=0
v_node_mask[nyp - 1, :] = 1.0   # northern wall: v=0
v_node_mask[:,:] = 1.0 #make it all 

# h_node_bdry_val: prescribed H at Dirichlet thickness nodes [m]
# Constant H0 throughout extension domain
# h_node_bdry_val = np.zeros((nyp, nxp))
# for i in range(nxp):
#     if xc[i] <= x_inflow + dx:
#         h_node_bdry_val[:, i] = H0

# h_node_bdry_val: prescribed H at Dirichlet thickness nodes [m]
# Nodes at x <= x_inflow: constant H0; nodes at x_inflow < x <= x_inflow+dx: analytical
h_node_bdry_val = np.zeros((nyp, nxp))
for i in range(nxp):
    if xc[i] <= x_inflow:
        h_node_bdry_val[:, i] = H0
    elif xc[i] <= x_inflow + dx_dir:
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

# ---- print analytic front advance for reference --------------------
drive   = rhoi * g * H0 * (1.0 - rhoi / rhow) / 4.0
eps_xx  = A_glen * drive**n_glen
eps_yr  = eps_xx * s_per_yr
char_len = v0 / eps_xx   # m

print(f"\nHuth et al. 2021 parameters:")
print(f"  H0       = {H0:.0f} m")
print(f"  v0       = {v0_yr:.0f} m/yr")
print(f"  A_glen   = {A_glen:.4e} Pa^-3 s^-1")
print(f"  eps      = {eps_xx:.4e} s^-1 = {eps_yr:.4e} yr^-1")
print(f"  v0/eps   = {char_len/1e3:.1f} km")

print(f"\nFront advance (Eq. 47, x_f0 = 0 at inflow boundary):")
for t_yr in [10, 50, 100, 200, 300]:
    t_s = t_yr * s_per_yr
    xf = char_len * (np.exp(eps_xx * t_s) - 1.0)
    print(f"  t = {t_yr:>4d} yr:  x_f = {xf/1e3:.1f} km  (absolute: {xf/1e3 + 200:.1f} km)")
