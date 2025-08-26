MISOMIP IceOcean1r experiment, restarting from the MISMIP+ steady state

Asay-Davis, et al., 2016. Experimental design for three interrelated marine ice sheet and ocean model intercomparison projects: MISMIP v. 3 (MISMIP +), ISOMIP v. 2 (ISOMIP +) and MISOMIP v. 1 (MISOMIP1), Geosci. Model Dev., 9, 2471–2497, https://doi.org/10.5194/gmd-9-2471-2016.


To run

1. move executable MOM6 to the current directory
   (cp ./../../../build/ocean_only_fms2/MOM6 ./MOM6)
2. Run setup
   (cd INPUT; python3 MISMIP_setup.py; cd ..)
3. Run simulation
   (srun -n 40 ./MOM6)
