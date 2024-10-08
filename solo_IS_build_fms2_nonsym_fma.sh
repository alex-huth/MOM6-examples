#/bin/bash
mkdir -p build/IS_only_fms2_nonsym_fma/
(cd build/IS_only_fms2_nonsym_fma/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_nonsymmetric,config_src/drivers/ice_solo_driver,config_src/external,src/{*,*/*}}/ ; \
 ../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms2' -p MOM6 -l '-L../fms2 -lfms' -c '-Duse_libMPI -Duse_netCDF' path_names)
source ./build/env_c5
make -C ./build/IS_only_fms2_nonsym_fma NETCDF=3 REPRO=1 ISA='-fma -qno-opt-dynamic-align' -j 8 MOM6
