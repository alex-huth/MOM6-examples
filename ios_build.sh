#!/bin/bash
cd build/ice_ocean_SIS2/
source ../env
make REPRO=1 MOM6 -j
cd ../..
