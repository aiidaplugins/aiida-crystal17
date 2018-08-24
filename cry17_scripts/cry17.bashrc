########################################################################
# These commands set up for use of CRYSTAL17.  
# They should be source'd into each CRYSTAL17 user's .bashrc file, 
# after definition of the following environment variable:
#
# User defined variables:
#
# CRY17_ROOT -- CRYSTAL17 main directory. For instance: 
 export CRY17_ROOT="/home/CRYSTAL17"
#
# CRY17_BIN -- directory with executables 
 export CRY17_BIN="bin"
#
# CRY17_ARCH -- string defining the platform/compiler
 export CRY17_ARCH="Linux-ifort"
#
# VERSION -- string associated with the binary version
 export VERSION="std"
#
# CRY17_SCRDIR -- directory scratch (integrals and temporary files)
 export CRY17_SCRDIR="$HOME/tmp"
#
# The following variables are according to CRYSTAL17 filesystem structure
 export CRY17_EXEDIR="$CRY17_ROOT/$CRY17_BIN/$CRY17_ARCH"
 export CRY17_UTILS="$CRY17_ROOT/utils17"
 export CRY2K6_GRA="$CRY17_ROOT/crgra2006"
 export CRY17_TEST="$CRY17_ROOT/test_cases/inputs"
 export GRA6_EXEDIR="$CRY2K6_GRA/bin/Linux-pgf"
#
 export PATH="${PATH}:./:${CRY17_EXEDIR}:${CRY17_UTILS}:${CRY2K6_GRA}"
#
 echo CRY17_SCRDIR - scratch directory "("integrals and temp files")": $CRY17_SCRDIR
 echo CRY17_EXEDIR - directory with crystal executables: $CRY17_EXEDIR
 echo CRY17_UTILS - running scripts and misc: $CRY17_UTILS/runcry17, runprop17
 echo CRY2K6_GRA - graphical scripts: $CRY2K6_GRA/maps06, doss06, band06
 echo CRY17_TEST - directory with test cases: $CRY2K6_TEST
#
########################################################################
#  Tip:
#  add the following line in .bashrc file
#
#   source ~/.cry17.bashrc
########################################################################
