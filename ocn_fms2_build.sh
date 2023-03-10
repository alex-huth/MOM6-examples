#/bin/bash
mkdir -p build/ocean_only_fms2/
(cd build/ocean_only_fms2/; rm -f path_names; \
../../src/mkmf/bin/list_paths -l ./ ../../src/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external,src/{*,*/*}}/ ; \
../../src/mkmf/bin/mkmf -t ../../src/mkmf/templates/ncrc-intel.mk -o '-I../fms2' -p MOM6 -l '-L../fms2 -lfms' path_names)
(cd build/ocean_only/; source ../env; make REPRO=1 MOM6 -j; cd ../..)
