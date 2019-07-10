#!/bin/bash
#PBS -r n
#PBS -m n
#PBS -N aiida-13006
#PBS -V
#PBS -o _scheduler-stdout.txt
#PBS -e _scheduler-stderr.txt
#PBS -l walltime=00:28:00
#PBS -l select=1:ncpus=8:mem=1gb
cd "$PBS_O_WORKDIR"


module load intel-suite/2016.3 mpi/intel-5.1

'mpiexec' '/rds/general/user/gmallia/home/CRYSTAL17_cx1/v2/bin/Linux-mpiifort_MPP/C17-v2_mod_Xeon___mpi__intel-2018___intel-suite__2016.3/Pcrystal'  > 'main.out' 2>&1

