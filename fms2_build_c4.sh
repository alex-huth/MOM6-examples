#!/bin/bash
mkdir -p build/fms2_c4/
(cd build/fms2_c4; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ../../src/FMS2; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF" path_names)

cd build/fms2_c4/
source ../env_c4
make NETCDF=3 REPRO=1 libfms.a -j
cd ../..
