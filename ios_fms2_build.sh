#!/bin/bash
cd build/ice_oceanFMS2_SIS2/
source ../env_c5
make REPRO=1 MOM6 -j
cd ../..
