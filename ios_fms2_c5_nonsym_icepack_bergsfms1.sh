#!/bin/bash
mkdir -p build/ice_oceanFMS2_SIS2_c5_nonsym_icepack_bergsfms1/
(cd build/ice_oceanFMS2_SIS2_c5_nonsym_icepack_bergsfms1/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/Icepack/columnphysics ../../src/MOM6/config_src/{infra/FMS2,memory/dynamic_nonsymmetric,drivers/FMS_cap,external} ../../src/MOM6/src/{*,*/*}/ ../../src/SIS2/config_src/dynamic_symmetric ../../src/{atmos_null,SIS2/src,SIS2,coupler/full,coupler/shared,coupler,land_null,ice_param,FMS2/coupler,FMS2/include,FMS2})
(cd build/ice_oceanFMS2_SIS2_c5_nonsym_icepack_bergsfms1/; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc5-intel.mk -o '-I../bergs_fms1 -I../fms2' -p MOM6_SIS2_Alex_bergs -l '-L../bergs_fms1 -lbergs -L../fms2 -lfms' -c '-Duse_AM3_physics -D_USE_LEGACY_LAND_ -Duse_libMPI -Duse_netCDF' path_names )
source ./build/env_c5
make -C ./build/ice_oceanFMS2_SIS2_c5_nonsym_icepack_bergsfms1 NETCDF=3 REPRO=1 MOM6_SIS2_Alex_bergs -j
