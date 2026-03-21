"""
make_ic.py  --  Generate initial conditions for the MPM ice-front advance test.

Domain: 500 km x 75 km Cartesian channel, 25 km x 25 km cells.
  NIGLOBAL = 20  (x-direction)
  NJGLOBAL = 3   (y-direction)

Physics:
  H0 = 500 m uniform floating shelf
  u0 = 200 m/yr inflow at western boundary
  A  = 1e-26 Pa^-3 s^-1  (stiffer ice => slower strain rate)
  No basal friction
  Initial ice front at x = 300 km; open ocean beyond.

Mask convention:
  h_mask = 3  Dirichlet inflow BC  (x in [0, 25 km], first cell)
  h_mask = 1  Free SSA interior    (x in [25, 300 km])
  h_mask = 0  Open ocean           (x in [300, 500 km])

  ufacemask = 5   ice-covered u-face
  ufacemask = -2  open-ocean u-face
  vfacemask = 5   ice-covered / wall v-face
  vfacemask = -2  open-ocean interior v-face

Analytic front advance (Huth et al. 2021, Eq. 47):
  eps_xx   = A * (rho_i * g * H * (1 - rho_i/rho_w) / 4)^3
           = 1e-26 * (910*9.8*500*(1-910/1028)/4)^3
           approx 2.097e-11 s^-1  =  6.614e-4 yr^-1
  u0/eps   = 200 / 6.614e-4 = 302.5 km
  x_f(t)   = (x_f0 + u0/eps) * exp(eps * t) - u0/eps
  x_f(300) = (300 + 302.5) * exp(0.1984) - 302.5  approx 432 km  (+132 km)

Output: MPM_IC.nc
"""

from netCDF4 import Dataset
import numpy as np

# ---- domain --------------------------------------------------------
Lx = 500.0e3      # m
Ly =  75.0e3      # m
dx =  25.0e3      # m
dy =  25.0e3      # m

nx  = int(Lx / dx)     # 20
ny  = int(Ly / dy)     # 3
nxp = nx + 1           # 21
nyp = ny + 1           # 4

xh = np.linspace(dx / 2, Lx - dx / 2, nx)   # cell centres
yh = np.linspace(dy / 2, Ly - dy / 2, ny)
xc = np.linspace(0.0, Lx, nxp)              # corners
yc = np.linspace(0.0, Ly, nyp)

XH, YH = np.meshgrid(xh, yh)   # (ny, nx)
XC, YC = np.meshgrid(xc, yc)   # (nyp, nxp)

# ---- physical parameters ------------------------------------------
rhoi      = 910.0
rhow      = 1028.0
H0        = 500.0
s_per_yr  = 365.0 * 86400
u0        = 200.0 / s_per_yr   # m s^-1

x_inflow  =  25.0e3   # m  -- Dirichlet BC (first cell only)
x_front   = 300.0e3   # m  -- initial ice front

# ---- h-grid variables ----------------------------------------------

# ice thickness: H0 west of front, 0 east of front
h_shelf = np.where(XH < x_front, H0, 0.0)

# depth: flat 1500 m
depth = np.ones((ny, nx)) * 1500.0

# h_mask: 3 = inflow BC, 1 = free SSA, 0 = open ocean
h_mask = np.zeros((ny, nx))
for i in range(nx):
    if xh[i] < x_front:
        h_mask[:, i] = 1.0
    if xh[i] <= x_inflow:
        h_mask[:, i] = 3.0

# shelf area: cell area where ice present, 0 in open ocean
shelf_area = np.where(XH < x_front, dx * dy, 0.0)

smb = np.zeros((ny, nx))
float_frac = np.zeros((ny, nx))  # 0 = floating (MOM6 ground_frac convention)

# ---- B-grid variables ----------------------------------------------

# u_face_mask_bdry convention (read by MOM6 as ICE_UBDRYMSK_VARNAME):
#   5  = Dirichlet inflow BC (western boundary only)
#   2  = calving-front CFBC (face exactly at x_front)
#  -2  = interior ice face OR ocean face → case default in update_velocity_masks
#         → umask = max(1, umask) = 1 → SSA node (NOT Dirichlet!)
# NOTE: ufacemask=5 means Dirichlet BC (umask=3 with u_bdry_val).
#       Do NOT set interior ice faces to 5 or they get u=0 Dirichlet.
ufacemask = np.full((nyp, nxp), -2.0)   # default: interior/ocean (umask stays 1)
front_col = int(round(x_front / (Lx / nx)))   # column index = 12
ufacemask[:, 0]         = 5.0               # western inflow: Dirichlet with u0
ufacemask[:, front_col] = 2.0               # calving-front face: CFBC

# vfacemask: free-slip N/S walls (vfacemask=5 → vmask=3, v=vbdry_val=0, u free)
# Interior and ocean faces: -2 (default, SSA node)
vfacemask = np.full((nyp, nxp), -2.0)
vfacemask[0,  :] = 5.0   # south wall: free-slip (v=0, u free)
vfacemask[-1, :] = 5.0   # north wall: free-slip (v=0, u free)

# Boundary velocity: u0 at western face (xc=0)
ubdry_val = np.zeros((nyp, nxp))
ubdry_val[:, 0] = u0

vbdry_val = np.zeros((nyp, nxp))

# Initial ice velocity: u0 in inflow region, 0 elsewhere
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

# ---- print analytic front advance for reference --------------------
g        = 9.8
A        = 1.0e-26
drive    = rhoi * g * H0 * (1.0 - rhoi / rhow) / 4.0
eps_xx   = A * drive**3
eps_yr   = eps_xx * s_per_yr
u0_yr    = u0 * s_per_yr
T        = 300.0   # yr
x_f0_m   = x_front                              # initial front position [m]
char_len = u0_yr / eps_yr                       # u0/eps  [m]
xf_T_m   = (x_f0_m + char_len) * np.exp(eps_yr * T) - char_len  # [m]
print(f"A                = {A:.0e} Pa^-3 s^-1")
print(f"Driving stress   = {drive:.1f} Pa")
print(f"eps_xx           = {eps_xx:.3e} s^-1  = {eps_yr:.3e} yr^-1")
print(f"u0               = {u0_yr:.1f} m/yr")
print(f"Front advance at t={T:.0f} yr:  {x_f0_m/1e3:.0f} km -> {xf_T_m/1e3:.1f} km  "
      f"(+{(xf_T_m - x_f0_m)/1e3:.1f} km)")
