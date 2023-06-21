#!/bin/bash
mkdir -p build/ice_oceanFMS2_SIS2_c5_nonsym/
(cd build/ice_oceanFMS2_SIS2_c5_nonsym/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/config_src/{infra/FMS2,memory/dynamic_nonsymmetric,drivers/FMS_cap,external} ../../src/MOM6/src/{*,*/*}/ ../../src/SIS2/config_src/dynamic_symmetric ../../src/{atmos_null,coupler/full,coupler/shared,land_null,ice_param,icebergs/src,SIS2,FMS2/coupler,FMS2/include}/)
(cd build/ice_oceanFMS2_SIS2_c5_nonsym/; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms2' -p MOM6_SIS2_Alex_bergs -l '-L../fms2 -lfms' -c '-Duse_AM3_physics -D_USE_LEGACY_LAND_' path_names )
cd build/ice_oceanFMS2_SIS2_c5_nonsym/
source ../env
make REPRO=1 MOM6_SIS2_Alex_bergs -j
