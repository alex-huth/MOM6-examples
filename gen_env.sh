#!/bin/bash
mkdir -p build
cat << EOFA > build/env
module unload PrgEnv-pgi
module unload PrgEnv-pathscale
module unload PrgEnv-intel
module unload PrgEnv-gnu
module unload PrgEnv-cray

module load PrgEnv-intel
module swap intel intel/18.0.6.288
module unload netcdf
module load cray-netcdf
module load cray-hdf5
EOFA
