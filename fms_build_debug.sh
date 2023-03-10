#!/bin/bash
mkdir -p build/fms_debug/
(cd build/fms_debug; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ../../src/FMS; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF" path_names)

cd build/fms_debug/
source ../env
make NETCDF=3 DEBUG=1 libfms.a -j
cd ../..
