#/bin/bash
mkdir -p build/IS_only_fms2_nonsym/
(cd build/IS_only_fms2_nonsym/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_nonsymmetric,config_src/drivers/ice_solo_driver,config_src/external,src/{*,*/*}}/ ; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms2' -p MOM6 -l '-L../fms2 -lfms' -c '-Duse_libMPI -Duse_netCDF' path_names)
(cd build/IS_only_fms2_nonsym/; source ../env_c5; make NETCDF=3 REPRO=1 MOM6 -j; cd ../..)
