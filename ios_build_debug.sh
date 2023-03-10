#!/bin/bash
mkdir -p build/ice_ocean_SIS2_debug/
(cd build/ice_ocean_SIS2_debug/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/config_src/{infra/FMS1,memory/dynamic_symmetric,drivers/FMS_cap,external} ../../src/MOM6/src/{*,*/*}/ ../../src/{atmos_null,coupler/{*,*/*},land_null,ice_param,icebergs/src,SIS2,FMS/coupler,FMS/include}/)
(cd build/ice_ocean_SIS2_debug/; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms_debug' -p MOM6 -l '-L../fms_debug -lfms' -c '-Duse_AM3_physics -D_USE_LEGACY_LAND_' path_names )

cd build/ice_ocean_SIS2_debug/
source ../env
make DEBUG=1 MOM6 -j
cd ../..
