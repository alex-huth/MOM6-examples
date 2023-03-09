#!/bin/bash
mkdir -p build/fms/
(cd build/fms; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ../../src/FMS; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF" path_names)

(cd build/fms/; source ../env; make NETCDF=3 REPRO=1 libfms.a -j; cd ../..)

