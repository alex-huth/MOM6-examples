#/bin/bash
mkdir -p build/IS_only/
(cd build/IS_only/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/{config_src/infra/FMS1,config_src/memory/dynamic_symmetric,config_src/drivers/ice_solo_driver,config_src/external,src/{*,*/*}}/ ; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms' -p MOM6 -l '-L../fms -lfms' path_names)
(cd build/IS_only/; source ../env; make REPRO=1 MOM6 -j; cd ../..)
