#!/bin/bash
mkdir -p build/ice_oceanFMS2_SIS2_c4/
(cd build/ice_oceanFMS2_SIS2_c4/; rm -f path_names; \
 ../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/config_src/{infra/FMS2,memory/dynamic_symmetric,drivers/FMS_cap,external} ../../src/MOM6/src/{*,*/*}/ ../../src/{atmos_null,coupler/full,coupler/shared,land_null,ice_param,icebergs/src,SIS2,FMS2/coupler,FMS2/include,FMS2}/)
(cd build/ice_oceanFMS2_SIS2_c4/; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms2_c4' -p MOM6_SIS2_Alex_bergs -l '-L../fms2_c4 -lfms' -c '-Duse_AM3_physics -D_USE_LEGACY_LAND_ -DUSE_FMS2_IO -Duse_libMPI -Duse_netCDF' path_names )

cd build/ice_oceanFMS2_SIS2_c4/
source ../env_c4
make NETCDF=3 REPRO=1 MOM6_SIS2_Alex_bergs -j
cd ../..
