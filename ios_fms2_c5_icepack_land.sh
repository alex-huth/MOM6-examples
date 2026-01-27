#!/bin/bash
mkdir -p build/ice_oceanFMS2_SIS2_c5_icepack_land/
(cd build/ice_oceanFMS2_SIS2_c5_icepack_land/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/Icepack/columnphysics ../../src/MOM6/config_src/{infra/FMS2,memory/dynamic_nonsymmetric,drivers/FMS_cap,external} ../../src/MOM6/src/{*,*/*}/ ../../src/SIS2/config_src/dynamic_symmetric ../../src/SIS2/config_src/external/Icepack_interfaces ../../src/{atmos_null,SIS2/src,coupler/full,coupler/shared,coupler,land_lad2,ice_param,icebergs/src,FMS2/coupler,FMS2/include,FMS2})
(cd build/ice_oceanFMS2_SIS2_c5_icepack_land/; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc5-intel.mk -o '-I../fms2' -p MOM6_SIS2_LM4 -l '-L../fms2 -lfms' -c '-Duse_libMPI -Duse_netCDF -DSPMD -DINTERNAL_FILE_NML -Duse_AM3_physics -DUSE_FMS2_IO ' path_names )
source ./build/env_c5
make -C ./build/ice_oceanFMS2_SIS2_c5_icepack_land NETCDF=3 REPRO=1 MOM6_SIS2_LM4 -j
