#!/bin/bash
mkdir -p build/ice_oceanFMS2_SIS2/
(cd build/ice_oceanFMS2_SIS2/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/config_src/{infra/FMS2,memory/dynamic_symmetric,drivers/FMS_cap,external} ../../src/MOM6/src/{*,*/*}/ ../../src/{atmos_null,coupler/full,coupler/shared,land_null,ice_param,icebergs/src,SIS2,FMS2/coupler,FMS2/include}/)
(cd build/ice_oceanFMS2_SIS2/; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms2' -p MOM6 -l '-L../fms2 -lfms' -c '-Duse_AM3_physics -D_USE_LEGACY_LAND_' path_names )
