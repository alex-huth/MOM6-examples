#/bin/bash
mkdir -p build/ocean_only_debug/
(cd build/ocean_only_debug/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/{config_src/infra/FMS1,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external,src/{*,*/*}}/ ; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms_debug' -p MOM6 -l '-L../fms_debug -lfms' path_names)
(cd build/ocean_only_debug/; source ../env; make DEBUG=1 MOM6 -j)
