from netCDF4 import Dataset
import numpy as np


Lx=800.e3
Ly=80.e3
#set to Ly for full domain, or Ly/2 for half-domain to take advantage of symmetry over y-axis
#y_extent=Ly/2
y_extent=Ly

x_extent_shelf=640.e3
Lx=800.e3
Ly=80.e3
B0=-150.0
B2=-728.8
B4=343.91
B6=-50.57
xtil=300.e3
fc=4.e3
dc=500.0
wc=24.e3
zbd=-720.0
rhoi=918.0
rhow=1028.0

res=2.e3
nnx=int(Lx/res+1)
nny=int(y_extent/res+1)
x=np.linspace(0,Lx,nnx)
y=np.linspace(0,y_extent,nny)

x2 = np.linspace(res/2,Lx-res/2,nnx-1)
y2 = np.linspace(res/2,y_extent-res/2,nny-1)

xc, yc = np.meshgrid(x,y)
xh, yh = np.meshgrid(x2,y2)

xt=xh/xtil
Bx = B0 + B2*(xt**2) + B4*(xt**4) + B6*(xt**6)

Byd1 = 1+np.exp(-2*(yh-Ly/2-wc)/fc)
Byd2 = 1+np.exp(2*(yh-Ly/2+wc)/fc)

By=dc/Byd1 + dc/Byd2

#-----cell-centered-----

#depth
depth1 = Bx + By
depth1[depth1<zbd]=zbd
depth1=-depth1

#h_mask
h_mask1=xh*0.; h_mask1[xh<x_extent_shelf]=1.0

#ice thickness
h_shelf1=h_mask1*100.0

#shelf_area
shelf_area1=xh*0.+1 * res * res

#surface mass balance
smb1=0.3/(365.*86400.)*rhoi

#float fraction
zb = h_shelf1*rhoi/rhow
ff1 = np.zeros_like(xh)
ff1[zb>depth1]=1.0

#-----corner vars-----

#boundary stuff
ufacemask1=np.zeros_like(xc)-2.; vfacemask1=np.zeros_like(xc)-2.
ufacemask1[:,0]=3; vfacemask1[0,:]=5; vfacemask1[nny-1,:]=5
ubdry_val1=np.zeros_like(xc); vbdry_val1=np.zeros_like(xc)

#----write the file------

ds = Dataset('./MISOMIP_IS.nc',mode='w',format='NETCDF4_CLASSIC')

xh_dim = ds.createDimension('nx',nnx-1); yh_dim = ds.createDimension('ny',nny-1)
xc_dim = ds.createDimension('nxp',nnx);  yc_dim = ds.createDimension('nyp',nny)

depth      = ds.createVariable('depth','f4',('ny','nx'))
depth[:,:]=depth1[:,:]
h_mask     = ds.createVariable('h_mask','f4',('ny','nx'));     h_mask[:,:]=h_mask1
h_shelf    = ds.createVariable('h_shelf','f4',('ny','nx'));    h_shelf[:,:]=h_shelf1
shelf_area = ds.createVariable('shelf_area','f4',('ny','nx')); shelf_area[:,:]=shelf_area1
smb        = ds.createVariable('smb','f4',('ny','nx'));        smb[:,:]=smb1
shelf_mass = ds.createVariable('shelf_mass','f4',('ny','nx')); shelf_mass[:,:]=h_shelf1*rhoi
float_frac = ds.createVariable('float_frac','f4',('ny','nx')); float_frac[:,:]=ff1


ufacemask = ds.createVariable('ufacemask','f4',('nyp','nxp')); ufacemask[:,:]=ufacemask1
vfacemask = ds.createVariable('vfacemask','f4',('nyp','nxp')); vfacemask[:,:]=vfacemask1
ubdry_val = ds.createVariable('ubdry_val','f4',('nyp','nxp')); ubdry_val[:,:]=ubdry_val1
vbdry_val = ds.createVariable('vbdry_val','f4',('nyp','nxp')); vbdry_val[:,:]=vbdry_val1
u_shelf = ds.createVariable('u_shelf','f4',('nyp','nxp')); u_shelf[:,:]=np.zeros_like(xc)
v_shelf = ds.createVariable('v_shelf','f4',('nyp','nxp')); v_shelf[:,:]=np.zeros_like(xc)


ds.close()

